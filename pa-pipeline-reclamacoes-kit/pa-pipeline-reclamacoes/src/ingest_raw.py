"""R02 – Ingestão dos CSVs mensais do Consumidor.gov.br para a camada bruta (raw).

O que faz, para cada CSV em data/raw/:
  1. detecta encoding e separador automaticamente;
  2. normaliza os nomes das colunas (minúsculas, sem acento, com _);
  3. lê o arquivo em blocos (chunks), sem alterar nenhum valor (tudo como texto);
  4. grava em raw.reclamacoes via COPY, com colunas de controle
     (_arquivo, _linha, _carga_em);
  5. registra a carga em raw.log_carga e em logs/log_carga.csv.

É idempotente: rodar de novo apaga e recarrega apenas o arquivo reprocessado.
Se um mês vier com colunas novas, elas são adicionadas à tabela e anotadas no log.

Uso:
    python src/ingest_raw.py               # todos os CSVs da pasta
    python src/ingest_raw.py arquivo.csv   # apenas um arquivo
"""
import csv
import io
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone

import pandas as pd
from charset_normalizer import from_bytes

from config import LOGS_DIR, RAW_DIR, TABELA_RAW, conectar

CHUNK = 200_000
SEPARADORES = [";", ",", "\t", "|"]
COLS_CONTROLE = ["_arquivo", "_linha", "_carga_em"]


def detectar_formato(caminho):
    """Retorna (encoding, separador) a partir de uma amostra do início do arquivo."""
    with open(caminho, "rb") as f:
        amostra = f.read(512_000)
    melhor = from_bytes(amostra).best()
    enc = (melhor.encoding if melhor else "utf-8").lower()
    if enc in ("ascii", "utf_8"):
        enc = "utf-8"
    if enc.startswith("cp125") or enc in ("latin_1", "iso8859_1", "cp850"):
        enc = "latin-1"
    if amostra.startswith(b"\xef\xbb\xbf"):
        enc = "utf-8-sig"
    texto = amostra.decode(enc, errors="replace")
    primeiras = "\n".join(texto.splitlines()[:20])
    try:
        sep = csv.Sniffer().sniff(primeiras, delimiters="".join(SEPARADORES)).delimiter
    except csv.Error:
        cabecalho = texto.splitlines()[0]
        sep = max(SEPARADORES, key=cabecalho.count)
    return enc, sep


def normalizar_coluna(nome):
    nome = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    nome = re.sub(r"[^0-9a-zA-Z]+", "_", nome.strip().lower()).strip("_")
    return nome or "coluna_sem_nome"


def colunas_unicas(nomes):
    vistos, saida = {}, []
    for n in nomes:
        vistos[n] = vistos.get(n, 0) + 1
        saida.append(n if vistos[n] == 1 else f"{n}_{vistos[n]}")
    return saida


def colunas_existentes(cur):
    schema, tabela = TABELA_RAW.split(".")
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
        (schema, tabela),
    )
    return [r[0] for r in cur.fetchall()]


def garantir_tabela(cur, colunas):
    """Cria raw.reclamacoes (tudo TEXT) ou adiciona colunas novas. Retorna as adicionadas."""
    existentes = colunas_existentes(cur)
    if not existentes:
        defs = ", ".join(f'"{c}" TEXT' for c in colunas)
        cur.execute(
            f"CREATE TABLE {TABELA_RAW} ({defs}, "
            '"_arquivo" TEXT NOT NULL, "_linha" BIGINT NOT NULL, "_carga_em" TIMESTAMPTZ NOT NULL)'
        )
        cur.execute(f'CREATE INDEX IF NOT EXISTS ix_raw_reclamacoes_arquivo ON {TABELA_RAW} ("_arquivo")')
        return []
    novas = [c for c in colunas if c not in existentes]
    for c in novas:
        cur.execute(f'ALTER TABLE {TABELA_RAW} ADD COLUMN "{c}" TEXT')
    return novas


def registrar_log(cur, linha):
    cur.execute(
        "INSERT INTO raw.log_carga (arquivo, encoding, separador, colunas, linhas_carregadas, tamanho_mb, "
        "inicio, fim, duracao_seg, status, observacao) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (linha["arquivo"], linha["encoding"], linha["separador"], linha["colunas"], linha["linhas_carregadas"],
         linha["tamanho_mb"], linha["inicio"], linha["fim"], linha["duracao_seg"], linha["status"],
         linha["observacao"]),
    )
    LOGS_DIR.mkdir(exist_ok=True)
    arq = LOGS_DIR / "log_carga.csv"
    novo = not arq.exists()
    with open(arq, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linha.keys()), delimiter=";")
        if novo:
            w.writeheader()
        w.writerow(linha)


def ingerir_arquivo(conn, caminho):
    inicio = datetime.now(timezone.utc)
    t0 = time.time()
    enc, sep = detectar_formato(caminho)
    tamanho_mb = round(caminho.stat().st_size / 1_048_576, 2)
    print(f"\n>> {caminho.name}  ({tamanho_mb} MB)  encoding={enc}  separador={sep!r}")

    total, observacao, ncols = 0, "", 0
    with conn.cursor() as cur:
        cur.execute(f"SELECT to_regclass('{TABELA_RAW}')")
        if cur.fetchone()[0]:
            cur.execute(f'DELETE FROM {TABELA_RAW} WHERE "_arquivo" = %s', (caminho.name,))
            if cur.rowcount:
                print(f"   reprocessamento: {cur.rowcount:,} linhas antigas removidas")

        leitor = pd.read_csv(caminho, sep=sep, encoding=enc, dtype=str, keep_default_na=False,
                             chunksize=CHUNK, on_bad_lines="warn", encoding_errors="replace")
        for i, bloco in enumerate(leitor):
            if i == 0:
                bloco.columns = colunas_unicas([normalizar_coluna(c) for c in bloco.columns])
                cols = list(bloco.columns)
                ncols = len(cols)
                novas = garantir_tabela(cur, cols)
                if novas:
                    observacao = "colunas novas adicionadas: " + ", ".join(novas)
                    print("   ATENÇÃO:", observacao)
            else:
                bloco.columns = cols
            bloco["_arquivo"] = caminho.name
            bloco["_linha"] = range(total + 2, total + 2 + len(bloco))  # linha 1 = cabeçalho
            bloco["_carga_em"] = inicio.isoformat()
            buf = io.StringIO()
            bloco.to_csv(buf, index=False, header=False)
            buf.seek(0)
            lista = ", ".join(f'"{c}"' for c in cols + COLS_CONTROLE)
            cur.copy_expert(f"COPY {TABELA_RAW} ({lista}) FROM STDIN WITH (FORMAT csv)", buf)
            total += len(bloco)
            print(f"   {total:,} linhas...", end="\r")

        fim = datetime.now(timezone.utc)
        linha = {
            "arquivo": caminho.name, "encoding": enc, "separador": sep, "colunas": ncols,
            "linhas_carregadas": total, "tamanho_mb": tamanho_mb, "inicio": inicio.isoformat(),
            "fim": fim.isoformat(), "duracao_seg": round(time.time() - t0, 1), "status": "OK",
            "observacao": observacao,
        }
        registrar_log(cur, linha)
    conn.commit()
    print(f"   OK: {total:,} linhas em {linha['duracao_seg']} s")
    return linha


def main():
    if len(sys.argv) > 1:
        arquivos = [RAW_DIR / a for a in sys.argv[1:]]
    else:
        arquivos = sorted(RAW_DIR.glob("*.csv"))
    if not arquivos:
        sys.exit(f"Nenhum CSV encontrado em {RAW_DIR}. Baixe os arquivos de 2025 para essa pasta.")

    conn = conectar()
    resumo = []
    for caminho in arquivos:
        try:
            resumo.append(ingerir_arquivo(conn, caminho))
        except Exception as erro:  # registra a falha e segue para o próximo arquivo
            conn.rollback()
            print(f"   ERRO em {caminho.name}: {erro}")
            with conn.cursor() as cur:
                agora = datetime.now(timezone.utc).isoformat()
                registrar_log(cur, {"arquivo": caminho.name, "encoding": None, "separador": None, "colunas": None,
                                    "linhas_carregadas": 0, "tamanho_mb": None, "inicio": agora, "fim": agora,
                                    "duracao_seg": 0, "status": "ERRO", "observacao": str(erro)[:500]})
            conn.commit()
    conn.close()

    ok = [r for r in resumo if r["status"] == "OK"]
    print("\n================ RESUMO DA INGESTÃO ================")
    print(f"Arquivos carregados: {len(ok)}/{len(arquivos)}")
    print(f"Total de linhas:     {sum(r['linhas_carregadas'] for r in ok):,}")
    print(f"Tempo total:         {sum(r['duracao_seg'] for r in ok):.1f} s")
    print("Log detalhado:       logs/log_carga.csv e tabela raw.log_carga")


if __name__ == "__main__":
    main()
