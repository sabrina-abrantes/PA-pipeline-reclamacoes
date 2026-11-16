"""R11 – Análise descritiva e validação das hipóteses (a partir das views de KPIs).

Gera gráficos em reports/analise/ e o resumo reports/analise_descritiva.md:
  1. pareto_empresas.png   concentração das reclamações por empresa (curva de Pareto)
  2. mensal.png            volume mensal e índices de solução ao longo de 2025
  3. segmentos.png         10 segmentos com mais reclamações e % resolvidas entre avaliadas
  4. grupos_problema.png   participação de cada grupo de problema

Uso:
    python src/analise_descritiva.py
"""
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import REPORTS_DIR, conectar  # noqa: E402

VERDE, AZUL, LARANJA, CINZA = "#00A79A", "#1E74BA", "#E07A1F", "#9AA5A8"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left"})


def n(v):
    return f"{int(v):,}".replace(",", ".")


def br(v, casas=1):
    return f"{float(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def consulta(cur, sql):
    cur.execute(sql)
    return cur.fetchall()


def main():
    pasta = REPORTS_DIR / "analise"
    pasta.mkdir(parents=True, exist_ok=True)
    conn = conectar()
    cur = conn.cursor()

    # ---------- 1. Pareto por empresa ----------
    emp = consulta(cur, "SELECT empresa, reclamacoes FROM analytics.vw_kpi_empresa ORDER BY reclamacoes DESC")
    total = sum(q for _, q in emp)
    acum, curva = 0, []
    for _, q in emp:
        acum += q
        curva.append(100 * acum / total)
    n50 = next(i + 1 for i, v in enumerate(curva) if v >= 50)
    n80 = next(i + 1 for i, v in enumerate(curva) if v >= 80)
    top10_pct = curva[9] if len(curva) >= 10 else curva[-1]

    fig, ax = plt.subplots(figsize=(9, 3.8), dpi=180)
    top = emp[:20]
    ax.bar(range(len(top)), [100 * q / total for _, q in top], color=VERDE)
    ax.set_xticks(range(len(top)), [e[:18] for e, _ in top], rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("% das reclamações")
    ax2 = ax.twinx()
    ax2.plot(range(len(top)), curva[:20], color=AZUL, marker="o", ms=3)
    ax2.set_ylim(0, 100); ax2.set_ylabel("% acumulado", color=AZUL)
    ax2.spines["top"].set_visible(False)
    ax.set_title(f"Pareto por empresa: {n50} de {n(len(emp))} empresas concentram 50% das reclamações")
    fig.tight_layout(); fig.savefig(pasta / "pareto_empresas.png"); plt.close(fig)

    # ---------- 2. Série mensal ----------
    men = consulta(cur, """SELECT nome_mes, reclamacoes, indice_solucao_pct, indice_resolucao_avaliadas_pct, tempo_medio_resposta_dias
                           FROM analytics.vw_kpi_mensal ORDER BY ano, mes""")
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=180)
    x = range(len(men))
    ax.bar(x, [m[1] / 1000 for m in men], color=CINZA, width=0.65, label="Reclamações (mil)")
    ax.set_xticks(x, [m[0][:3] for m in men]); ax.set_ylabel("mil reclamações")
    ax2 = ax.twinx()
    ax2.plot(x, [float(m[2]) for m in men], color=VERDE, marker="o", ms=3, label="Índice de solução (Senacon)")
    ax2.plot(x, [float(m[3]) for m in men], color=LARANJA, marker="o", ms=3, label="Resolvidas ÷ avaliadas")
    ax2.set_ylim(0, 100); ax2.set_ylabel("%"); ax2.spines["top"].set_visible(False)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=7, frameon=False, ncol=3)
    ax.set_ylim(0, max(m[1] for m in men) / 1000 * 1.35)
    ax.set_title("Volume mensal e índices de solução – 2025")
    fig.tight_layout(); fig.savefig(pasta / "mensal.png"); plt.close(fig)

    # ---------- 3. Segmentos ----------
    seg = consulta(cur, """SELECT segmento_de_mercado, reclamacoes, participacao_pct, indice_resolucao_avaliadas_pct,
                                  nota_media, indice_solucao_pct
                           FROM analytics.vw_kpi_segmento ORDER BY reclamacoes DESC LIMIT 10""")
    fig, ax = plt.subplots(figsize=(9, 4), dpi=180)
    nomes = [s[0][:48] for s in seg][::-1]
    ax.barh(nomes, [float(s[2]) for s in seg][::-1], color=VERDE)
    for i, s in enumerate(seg[::-1]):
        ax.text(float(s[2]) + 0.5, i, f"{br(s[2])}%  ·  resolvidas/avaliadas {br(s[3])}%", va="center", fontsize=7)
    ax.set_xlabel("% das reclamações"); ax.set_xlim(0, float(seg[0][2]) * 1.6)
    ax.set_title("10 segmentos com mais reclamações")
    fig.tight_layout(); fig.savefig(pasta / "segmentos.png"); plt.close(fig)

    # ---------- 4. Grupos de problema ----------
    grp = consulta(cur, """SELECT grupo_problema, count(*), round(100.0 * count(*) / sum(count(*)) OVER (), 2)
                           FROM analytics.fato_reclamacao JOIN analytics.dim_problema USING (sk_problema)
                           GROUP BY 1 ORDER BY 2 DESC""")
    fig, ax = plt.subplots(figsize=(9, 3.2), dpi=180)
    ax.barh([g[0] for g in grp][::-1], [float(g[2]) for g in grp][::-1],
            color=[CINZA] * (len(grp) - 1) + [AZUL])
    for i, g in enumerate(grp[::-1]):
        ax.text(float(g[2]) + 0.5, i, f"{br(g[2])}%", va="center", fontsize=8)
    ax.set_xlabel("% das reclamações"); ax.set_xlim(0, float(grp[0][2]) * 1.2)
    ax.set_title("Reclamações por grupo de problema")
    fig.tight_layout(); fig.savefig(pasta / "grupos_problema.png"); plt.close(fig)

    top_emp = consulta(cur, """SELECT empresa, reclamacoes, participacao_pct, indice_solucao_pct,
                                      indice_resolucao_avaliadas_pct, nota_media, tempo_medio_resposta_dias
                               FROM analytics.vw_kpi_empresa ORDER BY reclamacoes DESC LIMIT 10""")
    conn.close()

    maior_mes = max(men, key=lambda m: m[1]); menor_mes = min(men, key=lambda m: m[1])
    md = [
        "# Análise descritiva – Consumidor.gov.br 2025 (Sprint 3 – R11)", "",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M}. Gráficos em reports/analise/.", "",
        "## Principais achados", "",
        f"- **Concentração por empresa:** {n50} empresas, de {n(len(emp))}, concentram 50% das reclamações; "
        f"{n80} concentram 80%. As 10 maiores somam {br(top10_pct)}%.",
        f"- **Segmento:** {seg[0][0]} responde por {br(seg[0][2])}% das reclamações.",
        f"- **Problema:** o grupo {grp[0][0]} responde por {br(grp[0][2])}% das reclamações.",
        f"- **Sazonalidade:** o maior volume foi em {maior_mes[0]} ({n(maior_mes[1])} reclamações) e o menor em "
        f"{menor_mes[0]} ({n(menor_mes[1])}).",
        "- **Dois retratos da solução:** o índice oficial considera as não avaliadas como solucionadas; "
        "entre as reclamações avaliadas, o percentual de resolvidas é bem menor (ver gráfico mensal).", "",
        "## 10 empresas com mais reclamações", "",
        "| Empresa | Reclamações | Participação (%) | Índice de solução (%) | Resolvidas ÷ avaliadas (%) | Nota média | Tempo médio (dias) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[f"| {e} | {n(q)} | {br(p, 2)} | {br(s, 2)} | {br(r, 2)} | {br(nt, 2)} | {br(t, 2)} |"
          for e, q, p, s, r, nt, t in top_emp], "",
        "## Hipótese H5 (concentração tipo Pareto)", "",
        f"Confirmada: {br(100 * n80 / len(emp))}% das empresas concentram 80% das reclamações, "
        f"e um único grupo de problema concentra {br(grp[0][2])}%.", "",
    ]
    (REPORTS_DIR / "analise_descritiva.md").write_text("\n".join(md), encoding="utf-8")

    print("\n================ ANÁLISE DESCRITIVA ================")
    print(f"Empresas para 50% / 80% das reclamações: {n50} / {n80} (de {len(emp)})")
    print(f"Top 10 empresas: {br(top10_pct)}% · Maior segmento: {seg[0][0]} ({br(seg[0][2])}%)")
    print(f"Maior grupo de problema: {grp[0][0]} ({br(grp[0][2])}%)")
    print("Gráficos: reports/analise/*.png · Resumo: reports/analise_descritiva.md")
    return {"n50": n50, "n80": n80, "empresas": len(emp)}


if __name__ == "__main__":
    main()
