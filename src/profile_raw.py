"""R03 – Perfilamento de qualidade da camada bruta (raw.reclamacoes).

Gera:
  reports/perfil_colunas.csv        uma linha por coluna (nulos, distintos, tamanhos, tipo sugerido, top valores)
  reports/relatorio_qualidade.md    relatório legível para print e para o relatório do Projeto Aplicado

Tudo é calculado dentro do PostgreSQL (rápido mesmo com milhões de linhas).

Uso:
    python src/profile_raw.py
"""
import csv
import re
from datetime import datetime

from config import REPORTS_DIR, TABELA_RAW, conectar

CONTROLE = {"_arquivo", "_linha", "_carga_em"}

RE_DATA_BR = r"^\d{2}/\d{2}/\d{4}$"
RE_DATA_ISO = r"^\d{4}-\d{2}-\d{2}"
RE_INTEIRO = r"^-?\d+$"
RE_DECIMAL = r"^-?\d+([.,]\d+)?$"

UFS = ("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO").split()

# Regras de domínio: aplicadas apenas se a coluna existir na base.
REGRAS_DOMINIO = [
    ("uf", "UF válida (27 siglas)",
     "upper(trim({c})) NOT IN (" + ",".join(f"'{u}'" for u in UFS) + ")"),
    ("nota_do_consumidor", "Nota entre 1 e 5",
     "NOT (trim({c}) ~ '^[1-5]$')"),
    ("tempo_resposta", "Tempo de resposta inteiro entre 0 e 30 dias",
     "CASE WHEN trim({c}) ~ '^\\d+$' THEN trim({c})::int > 30 ELSE true END"),
    ("respondida", "Respondida = S ou N",
     "upper(trim({c})) NOT IN ('S','N','SIM','NAO','NÃO')"),
    ("sexo", "Sexo = F, M ou O",
     "upper(trim({c})) NOT IN ('F','M','O')"),
    ("ano_abertura", "Ano de abertura = 2025",
     "trim({c}) <> '2025'"),
]


def consultar(cur, sql, params=None):
    cur.execute(sql, params)
    return cur.fetchall()


def tipo_sugerido(cur, col, nao_nulos):
    if nao_nulos == 0:
        return "vazio"
    q = f'''SELECT
        count(*) FILTER (WHERE trim("{col}") ~ %s),
        count(*) FILTER (WHERE trim("{col}") ~ %s),
        count(*) FILTER (WHERE trim("{col}") ~ %s),
        count(*) FILTER (WHERE trim("{col}") ~ %s)
      FROM {TABELA_RAW} WHERE nullif(trim("{col}"), '') IS NOT NULL'''
    br, iso, inteiro, dec = consultar(cur, q, (RE_DATA_BR, RE_DATA_ISO, RE_INTEIRO, RE_DECIMAL))[0]
    for nome, qtd in (("data (dd/mm/aaaa)", br), ("data (aaaa-mm-dd)", iso), ("inteiro", inteiro), ("decimal", dec)):
        if qtd / nao_nulos >= 0.98:
            return nome
    return "texto"


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    conn = conectar()
    cur = conn.cursor()

    total = consultar(cur, f"SELECT count(*) FROM {TABELA_RAW}")[0][0]
    por_arquivo = consultar(cur, f'SELECT "_arquivo", count(*) FROM {TABELA_RAW} GROUP BY 1 ORDER BY 1')
    schema, tabela = TABELA_RAW.split(".")
    colunas = [r[0] for r in consultar(
        cur, "SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s "
             "ORDER BY ordinal_position", (schema, tabela)) if r[0] not in CONTROLE]
    print(f"{total:,} linhas, {len(colunas)} colunas de negócio")

    perfil = []
    for col in colunas:
        print(f"  perfilando {col}...")
        nulos, distintos, tmin, tmax = consultar(cur, f'''SELECT
              count(*) FILTER (WHERE nullif(trim("{col}"), '') IS NULL),
              count(DISTINCT nullif(trim("{col}"), '')),
              min(length("{col}")), max(length("{col}"))
            FROM {TABELA_RAW}''')[0]
        top = consultar(cur, f'''SELECT "{col}", count(*) FROM {TABELA_RAW}
            WHERE nullif(trim("{col}"), '') IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 5''')
        variantes = consultar(cur, f'''SELECT count(DISTINCT "{col}") - count(DISTINCT upper(trim("{col}")))
            FROM {TABELA_RAW}''')[0][0]
        perfil.append({
            "coluna": col,
            "pct_nulos": round(100 * nulos / total, 2) if total else 0,
            "nulos": nulos,
            "distintos": distintos,
            "variacoes_grafia": variantes,
            "tam_min": tmin, "tam_max": tmax,
            "tipo_sugerido": tipo_sugerido(cur, col, total - nulos),
            "top_valores": " | ".join(f"{v} ({q:,})" for v, q in top),
        })

    # Duplicidades: linhas idênticas em todas as colunas de negócio
    expr = " || '§' || ".join(f'coalesce("{c}", \'\')' for c in colunas)
    duplicadas = consultar(cur, f"SELECT count(*) - count(DISTINCT md5({expr})) FROM {TABELA_RAW}")[0][0]

    # Regras de domínio
    dominio = []
    for col, descricao, cond in REGRAS_DOMINIO:
        if col in colunas:
            c = f'"{col}"'
            violacoes = consultar(cur, f"""SELECT count(*) FROM {TABELA_RAW}
                WHERE nullif(trim({c}), '') IS NOT NULL AND ({cond.format(c=c)})""")[0][0]
            dominio.append((col, descricao, violacoes))

    conn.close()

    # ---------- saídas ----------
    with open(REPORTS_DIR / "perfil_colunas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(perfil[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(perfil)

    linhas = [
        "# Relatório de qualidade – camada bruta (raw.reclamacoes)",
        "",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M}. Fonte: Consumidor.gov.br, reclamações finalizadas em 2025.",
        "",
        "## Visão geral",
        "",
        "| Indicador | Valor |",
        "| --- | --- |",
        f"| Linhas | {total:,} |",
        f"| Arquivos | {len(por_arquivo)} |",
        f"| Colunas de negócio | {len(colunas)} |",
        f"| Linhas duplicadas (idênticas em todas as colunas) | {duplicadas:,} ({100 * duplicadas / total:.2f}%) |",
        "",
        "## Linhas por arquivo",
        "",
        "| Arquivo | Linhas |",
        "| --- | ---: |",
        *[f"| {a} | {q:,} |" for a, q in por_arquivo],
        "",
        "## Perfil por coluna",
        "",
        "| Coluna | % nulos | Distintos | Variações de grafia | Tipo sugerido | Tam. mín–máx |",
        "| --- | ---: | ---: | ---: | --- | --- |",
        *[f"| {p['coluna']} | {p['pct_nulos']}% | {p['distintos']:,} | {p['variacoes_grafia']:,} | "
          f"{p['tipo_sugerido']} | {p['tam_min']}–{p['tam_max']} |" for p in perfil],
        "",
        "## Regras de domínio",
        "",
        "| Coluna | Regra | Violações |",
        "| --- | --- | ---: |",
        *[f"| {c} | {d} | {v:,} |" for c, d, v in dominio],
        "",
        "## Valores mais frequentes",
        "",
        *[f"- **{p['coluna']}**: {p['top_valores']}" for p in perfil],
        "",
        "## Achados e próximos passos",
        "",
        "_Preencha aqui as suas conclusões (ex.: colunas com muitos nulos e por quê, problemas de grafia, "
        "o que vira regra de limpeza na Sprint 2)._",
        "",
    ]
    texto = "\n".join(linhas)
    # números no padrão brasileiro: 1.234.567 e 12,5%
    texto = re.sub(r"(?<=\d),(?=\d{3}\b)", ".", texto)
    texto = re.sub(r"(\d)\.(\d+)%", r"\1,\2%", texto)
    (REPORTS_DIR / "relatorio_qualidade.md").write_text(texto, encoding="utf-8")
    print("\nOK: reports/relatorio_qualidade.md e reports/perfil_colunas.csv")


if __name__ == "__main__":
    main()
