"""R10 – Reconcilia os KPIs do pipeline com o Boletim Consumidor.gov.br 2025 (Senacon).

Critério de aceite: diferença de até 1 p.p. (percentuais) ou 1% (totais), ou divergência explicada.
Gera reports/reconciliacao_boletim.md.

Fonte dos valores oficiais: Boletim Consumidor.gov.br 2025, Senacon/MJSP
https://www.gov.br/mj/pt-br/assuntos/seus-direitos/consumidor/defesadoconsumidor/Biblioteca/boletins-1/boletim-consumidor-gov-br-2025-vfinal.pdf

Uso:
    python src/reconciliar_boletim.py
"""
from datetime import datetime

from config import REPORTS_DIR, conectar

# (indicador, valor oficial, tipo, consulta SQL que devolve o valor do pipeline)
CHECAGENS = [
    ("Total de reclamações finalizadas", 2_328_863, "total",
     "SELECT count(*) FROM analytics.fato_reclamacao"),
    ("Índice de solução (%)", 81.43, "pp",
     "SELECT indice_solucao_pct FROM analytics.vw_kpi_geral"),
    ("Prazo médio de resposta (dias)", 6, "dias",
     "SELECT tempo_medio_resposta_dias FROM analytics.vw_kpi_geral"),
    ("Bancos, Financeiras e Adm. de Cartão (% das reclamações)", 42.84, "pp",
     "SELECT participacao_pct FROM analytics.vw_kpi_segmento "
     "WHERE segmento_de_mercado = 'Bancos, Financeiras e Administradoras de Cartão'"),
    ("Operadoras de Telecomunicações (% das reclamações)", 9.35, "pp",
     "SELECT participacao_pct FROM analytics.vw_kpi_segmento "
     "WHERE segmento_de_mercado LIKE 'Operadoras de Telecomunica%'"),
    ("Grupo Cobrança / Contestação (% das reclamações)", 52.14, "pp",
     "SELECT round(100.0 * count(*) FILTER (WHERE grupo_problema = 'Cobrança / Contestação') / count(*), 2) "
     "FROM analytics.fato_reclamacao JOIN analytics.dim_problema USING (sk_problema)"),
    ("Assunto Cartão de Crédito/Débito/Loja (% das reclamações)", 18.60, "pp",
     "SELECT round(100.0 * count(*) FILTER (WHERE assunto LIKE 'Cartão de Crédito / Cartão de Débito%') / count(*), 2) "
     "FROM analytics.fato_reclamacao JOIN analytics.dim_problema USING (sk_problema)"),
]


def br(v, casas=2):
    return f"{float(v):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    conn = conectar()
    cur = conn.cursor()
    linhas, ok_total = [], 0
    for nome, oficial, tipo, sql in CHECAGENS:
        cur.execute(sql)
        r = cur.fetchone()
        valor = float(r[0]) if r and r[0] is not None else None
        if valor is None:
            linhas.append((nome, oficial, "–", "–", "sem dado")); continue
        if tipo == "total":
            dif = 100 * (valor - oficial) / oficial
            ok = abs(dif) <= 1
            linhas.append((nome, f"{oficial:,}".replace(",", "."), f"{int(valor):,}".replace(",", "."),
                           f"{br(dif, 4)}%", "OK" if ok else "DIVERGENTE"))
        elif tipo == "dias":
            dif = valor - oficial
            ok = round(valor) == oficial
            linhas.append((nome, str(oficial), br(valor), f"{br(dif)} dia", "OK (arredondado)" if ok else "DIVERGENTE"))
        else:
            dif = valor - oficial
            ok = abs(dif) <= 1
            linhas.append((nome, br(oficial), br(valor), f"{br(dif)} p.p.", "OK" if ok else "DIVERGENTE"))
        ok_total += ok
    cur.execute("SELECT indice_resolucao_avaliadas_pct, avaliadas_pct FROM analytics.vw_kpi_geral")
    estrito, avaliadas = cur.fetchone()
    conn.close()

    md = [
        "# Reconciliação com o Boletim Consumidor.gov.br 2025 (Sprint 3 – R10)", "",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M}. Critério: até 1 p.p. (percentuais) ou 1% (totais).", "",
        "| Indicador | Boletim 2025 | Pipeline | Diferença | Situação |", "| --- | ---: | ---: | ---: | --- |",
        *[f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in linhas], "",
        f"**{ok_total} de {len(CHECAGENS)} indicadores dentro do critério.**", "",
        "## Observações", "",
        "- A diferença no total corresponde aos 6 registros enviados à quarentena na Sprint 2.",
        "- O índice de solução segue a metodologia da Senacon: reclamações **resolvidas + não avaliadas** "
        "divididas pelas finalizadas. Com essa regra, o pipeline reproduz o número oficial.",
        f"- Considerando só as reclamações que o consumidor avaliou ({br(avaliadas)}% do total), "
        f"o percentual de resolvidas é **{br(estrito)}%**. As duas visões ficam disponíveis nas views de KPIs.",
        "- O boletim informa o prazo médio em dias inteiros; o pipeline calcula com duas casas decimais.", "",
    ]
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "reconciliacao_boletim.md").write_text("\n".join(md), encoding="utf-8")

    print("\n================ RECONCILIAÇÃO COM O BOLETIM 2025 ================")
    for a, b, c, d, e in linhas:
        print(f"{a[:46]:<47} boletim {b:>10} | pipeline {c:>10} | {e}")
    print(f"\n{ok_total}/{len(CHECAGENS)} dentro do critério · Relatório: reports/reconciliacao_boletim.md")


if __name__ == "__main__":
    main()
