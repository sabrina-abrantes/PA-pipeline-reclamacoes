"""R09 – Cria as views de KPIs e gera reports/kpis.md com os indicadores calculados.

Uso:
    python src/kpis.py
"""
from datetime import datetime

from config import RAIZ, REPORTS_DIR, conectar


def fmt(v, casas=2):
    if v is None:
        return "–"
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return f"{float(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela(cur, sql, cabecalho):
    cur.execute(sql)
    linhas = cur.fetchall()
    out = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join(["---"] + ["---:"] * (len(cabecalho) - 1)) + " |"]
    for l in linhas:
        out.append("| " + " | ".join(str(x) if isinstance(x, str) else fmt(x) for x in l) + " |")
    return out


KPI_COLS = "reclamacoes, indice_solucao_pct, tempo_medio_resposta_dias, respondidas_pct, nota_media, indice_resolucao_avaliadas_pct"
KPI_HEAD = ["Reclamações", "Índice de solução (%)", "Tempo médio de resposta (dias)", "Respondidas (%)",
            "Nota média", "Resolvidas ÷ avaliadas (%)"]


def main():
    conn = conectar()
    cur = conn.cursor()
    print("Criando views de KPIs (sql/40_views_kpis.sql)...")
    cur.execute((RAIZ / "sql" / "40_views_kpis.sql").read_text(encoding="utf-8"))
    conn.commit()

    md = [
        "# Indicadores (KPIs) – Consumidor.gov.br 2025 (Sprint 3 – R09)", "",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M} a partir das views do schema analytics.", "",
        "Definições: **índice de solução** = (resolvidas + não avaliadas) ÷ finalizadas, metodologia da Senacon; "
        "**resolvidas ÷ avaliadas** = visão estrita, só com as reclamações que o consumidor avaliou.", "",
        "## Brasil (vw_kpi_geral)", "",
        *tabela(cur, f"SELECT {KPI_COLS} FROM analytics.vw_kpi_geral", KPI_HEAD), "",
        "## Por mês (vw_kpi_mensal)", "",
        *tabela(cur, f"SELECT nome_mes, {KPI_COLS} FROM analytics.vw_kpi_mensal ORDER BY ano, mes", ["Mês"] + KPI_HEAD), "",
        "## 10 segmentos com mais reclamações (vw_kpi_segmento)", "",
        *tabela(cur, f"SELECT segmento_de_mercado, participacao_pct, {KPI_COLS} FROM analytics.vw_kpi_segmento "
                     "ORDER BY reclamacoes DESC LIMIT 10", ["Segmento", "Participação (%)"] + KPI_HEAD), "",
        "## 15 empresas com mais reclamações (vw_kpi_empresa)", "",
        *tabela(cur, f"SELECT empresa, participacao_pct, {KPI_COLS} FROM analytics.vw_kpi_empresa "
                     "ORDER BY reclamacoes DESC LIMIT 15", ["Empresa", "Participação (%)"] + KPI_HEAD), "",
        "## Por UF (vw_kpi_uf)", "",
        *tabela(cur, f"SELECT uf, participacao_pct, {KPI_COLS} FROM analytics.vw_kpi_uf ORDER BY reclamacoes DESC",
                ["UF", "Participação (%)"] + KPI_HEAD), "",
    ]
    cur.execute(f"SELECT {KPI_COLS} FROM analytics.vw_kpi_geral")
    g = cur.fetchone()
    conn.close()
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "kpis.md").write_text("\n".join(md), encoding="utf-8")

    print("\n================ KPIs 2025 (BRASIL) ================")
    for nome, v in zip(KPI_HEAD, g):
        print(f"{nome:<32} {fmt(v)}")
    print("Views: vw_kpi_geral, vw_kpi_mensal, vw_kpi_segmento, vw_kpi_empresa, vw_kpi_uf, vw_reclamacoes")
    print("Relatório: reports/kpis.md")


if __name__ == "__main__":
    main()
