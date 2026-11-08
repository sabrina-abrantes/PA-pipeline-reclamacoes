"""R05 + R06 – Limpeza, padronização, validação e quarentena (raw → staging).

Executa sql/10_staging.sql e gera reports/validacao_staging.md com:
  - rastreabilidade: linhas raw = staging + quarentena (meta: 100%)
  - registros em quarentena por motivo
  - antes × depois das principais regras (espaços, grafias de empresa e cidade, tipos)

Uso:
    python src/transform_staging.py
"""
import time
from datetime import datetime

from config import RAIZ, REPORTS_DIR, conectar


def um(cur, sql):
    cur.execute(sql)
    return cur.fetchone()[0]


def fmt(n):
    return f"{n:,}".replace(",", ".")


def main():
    conn = conectar()
    cur = conn.cursor()

    t0 = time.time()
    print("Aplicando regras de limpeza e validação (sql/10_staging.sql)...")
    cur.execute((RAIZ / "sql" / "10_staging.sql").read_text(encoding="utf-8"))
    conn.commit()
    dur = round(time.time() - t0, 1)

    raw = um(cur, "SELECT count(*) FROM raw.reclamacoes")
    stg = um(cur, "SELECT count(*) FROM staging.reclamacoes")
    qua = um(cur, "SELECT count(*) FROM staging.quarentena")
    cur.execute("""SELECT m, count(*) FROM staging.quarentena,
                   unnest(string_to_array(motivo_quarentena, '; ')) AS m GROUP BY 1 ORDER BY 2 DESC""")
    motivos = cur.fetchall()

    antes_depois = [
        ("Valores com espaços nas pontas (todas as colunas de texto)",
         um(cur, """SELECT count(*) FROM raw.reclamacoes WHERE regiao <> btrim(regiao) OR nome_fantasia <> btrim(nome_fantasia)
                    OR area <> btrim(area) OR cidade <> btrim(cidade) OR assunto <> btrim(assunto)"""),
         um(cur, """SELECT count(*) FROM staging.reclamacoes WHERE regiao <> btrim(regiao) OR nome_fantasia <> btrim(nome_fantasia)
                    OR area <> btrim(area) OR cidade <> btrim(cidade) OR assunto <> btrim(assunto)""")),
        ("Nomes de empresa distintos",
         um(cur, "SELECT count(DISTINCT nome_fantasia) FROM raw.reclamacoes"),
         um(cur, "SELECT count(DISTINCT nome_fantasia) FROM staging.reclamacoes")),
        ("Cidades distintas (por UF)",
         um(cur, "SELECT count(DISTINCT (uf, cidade)) FROM raw.reclamacoes"),
         um(cur, "SELECT count(DISTINCT (uf, cidade)) FROM staging.reclamacoes")),
        ("Valores de região distintos",
         um(cur, "SELECT count(DISTINCT regiao) FROM raw.reclamacoes"),
         um(cur, "SELECT count(DISTINCT regiao) FROM staging.reclamacoes")),
        ("Sexo vazio",
         um(cur, "SELECT count(*) FROM raw.reclamacoes WHERE nullif(btrim(sexo), '') IS NULL"),
         um(cur, "SELECT count(*) FROM staging.reclamacoes WHERE sexo IS NULL")),
    ]
    tipos = [
        ("data_finalizacao (DATE)", um(cur, "SELECT count(*) FROM staging.reclamacoes WHERE data_finalizacao IS NOT NULL")),
        ("tempo_resposta (INTEGER, só nulo se não respondida)",
         um(cur, "SELECT count(*) FROM staging.reclamacoes WHERE tempo_resposta IS NOT NULL OR NOT respondida")),
        ("nota_do_consumidor (1–5, só nula se não avaliada)",
         um(cur, "SELECT count(*) FROM staging.reclamacoes WHERE nota_do_consumidor BETWEEN 1 AND 5 OR avaliacao_reclamacao = 'Não Avaliada'")),
        ("respondida / procurou_empresa (BOOLEAN)",
         um(cur, "SELECT count(*) FROM staging.reclamacoes WHERE respondida IS NOT NULL AND procurou_empresa IS NOT NULL")),
    ]
    dup = um(cur, "SELECT count(*) FROM staging.reclamacoes WHERE possivel_duplicata")
    set_disp = um(cur, "SELECT count(*) FROM staging.reclamacoes WHERE colunas_set_disponiveis")
    cur.execute("""SELECT nome_fantasia, count(DISTINCT nome_fantasia_original), string_agg(DISTINCT '"' || nome_fantasia_original || '"', ', ')
                   FROM staging.reclamacoes GROUP BY 1 HAVING count(DISTINCT nome_fantasia_original) > 1
                   ORDER BY count(*) DESC LIMIT 10""")
    unificadas = cur.fetchall()
    conn.close()

    rastreio = 100 * (stg + qua) / raw if raw else 0
    md = [
        "# Validação da camada staging (Sprint 2 – R05/R06)", "",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M}. Tempo de processamento: {dur} s.", "",
        "## Rastreabilidade (meta: 100% dos registros carregados ou em quarentena)", "",
        "| Camada | Linhas |", "| --- | ---: |",
        f"| raw.reclamacoes | {fmt(raw)} |",
        f"| staging.reclamacoes (aprovados) | {fmt(stg)} |",
        f"| staging.quarentena (rejeitados com motivo) | {fmt(qua)} |",
        f"| **Rastreados (staging + quarentena) ÷ raw** | **{rastreio:.2f}%** |".replace(".", ",", 1), "",
        "## Quarentena por motivo", "",
        "| Motivo | Linhas |", "| --- | ---: |",
        *([f"| {m} | {fmt(q)} |" for m, q in motivos] or ["| (nenhum registro em quarentena) | 0 |"]), "",
        "## Antes × depois da limpeza", "",
        "| Verificação | raw | staging |", "| --- | ---: | ---: |",
        *[f"| {d} | {fmt(a)} | {fmt(b)} |" for d, a, b in antes_depois], "",
        "## Tipagem (registros válidos na staging)", "",
        "| Coluna / regra | Registros válidos | % |", "| --- | ---: | ---: |",
        *[f"| {d} | {fmt(v)} | {(f'{100 * v / stg:.2f}' if stg else '0').replace('.', ',')}% |" for d, v in tipos], "",
        "## Sinalizações", "",
        f"- Possíveis duplicatas sinalizadas (mantidas, não removidas – R12): **{fmt(dup)}**",
        f"- Registros de arquivos com as colunas de setembro/2025 disponíveis (R11): **{fmt(set_disp)}**", "",
        "## Empresas com grafias unificadas (top 10)", "",
        "| Nome canônico | Grafias na origem | Variações encontradas |", "| --- | ---: | --- |",
        *([f"| {n} | {q} | {v} |" for n, q, v in unificadas] or ["| (nenhuma) | 0 | – |"]), "",
    ]
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "validacao_staging.md").write_text("\n".join(md), encoding="utf-8")

    print("\n================ RESUMO STAGING ================")
    print(f"raw:        {fmt(raw)}")
    print(f"staging:    {fmt(stg)}")
    print(f"quarentena: {fmt(qua)}")
    print(f"rastreados: {rastreio:.2f}%")
    print(f"tempo:      {dur} s")
    print("Relatório:  reports/validacao_staging.md")


if __name__ == "__main__":
    main()
