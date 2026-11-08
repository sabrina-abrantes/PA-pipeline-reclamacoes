"""R07 + R08 – Cria o modelo dimensional e carrega a partir da staging (staging → analytics).

Executa sql/20_modelo_dimensional.sql (DDL) e sql/30_carga_analytics.sql (carga) DUAS vezes,
para comprovar a idempotência (mesmos totais na 2ª execução). Gera reports/carga_analytics.md.

Uso:
    python src/load_analytics.py
"""
import time
from datetime import datetime

from config import RAIZ, REPORTS_DIR, conectar

TABELAS = ["dim_tempo", "dim_empresa", "dim_localidade", "dim_problema", "dim_consumidor", "fato_reclamacao"]


def fmt(n):
    return f"{n:,}".replace(",", ".")


def contagens(cur):
    out = {}
    for t in TABELAS:
        cur.execute(f"SELECT count(*) FROM analytics.{t}")
        out[t] = cur.fetchone()[0]
    return out


def main():
    conn = conectar()
    cur = conn.cursor()
    sql = lambda nome: (RAIZ / "sql" / nome).read_text(encoding="utf-8")

    print("Criando modelo dimensional (sql/20_modelo_dimensional.sql)...")
    cur.execute(sql("20_modelo_dimensional.sql"))
    conn.commit()

    execucoes = []
    for i in (1, 2):
        t0 = time.time()
        print(f"Carga {i}/2 (sql/30_carga_analytics.sql)...")
        cur.execute(sql("30_carga_analytics.sql"))
        conn.commit()
        execucoes.append((round(time.time() - t0, 1), contagens(cur)))

    cur.execute("SELECT count(*) FROM raw.reclamacoes"); raw = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM staging.reclamacoes"); stg = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM staging.quarentena"); qua = cur.fetchone()[0]
    cur.execute("""SELECT count(*) FROM analytics.fato_reclamacao f
                   LEFT JOIN staging.reclamacoes s ON s._arquivo = f.origem_arquivo AND s._linha = f.origem_linha
                   WHERE s._arquivo IS NULL"""); orfas = cur.fetchone()[0]
    cur.execute("""SELECT t.mes, t.nome_mes, count(*) FROM analytics.fato_reclamacao f
                   JOIN analytics.dim_tempo t USING (sk_tempo) GROUP BY 1, 2 ORDER BY 1""")
    por_mes = cur.fetchall()
    conn.close()

    (d1, c1), (d2, c2) = execucoes
    fato = c2["fato_reclamacao"]
    idem = c1 == c2
    md = [
        "# Carga do modelo dimensional (Sprint 2 – R07/R08)", "",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M}.", "",
        "## Modelo (esquema estrela)", "",
        "- **fato_reclamacao** – 1 linha por reclamação; medidas: respondida, tempo_resposta, avaliada, resolvida, nota",
        "- **dim_tempo** – data de finalização (ano, trimestre, mês, dia da semana)",
        "- **dim_empresa** – empresa (nome canônico) e segmento de mercado",
        "- **dim_localidade** – região, UF e cidade do consumidor",
        "- **dim_problema** – área, assunto, grupo de problema e problema",
        "- **dim_consumidor** – sexo, faixa etária, canal de compra e se procurou a empresa", "",
        "## Idempotência (carga executada duas vezes)", "",
        "| Tabela | 1ª execução | 2ª execução |", "| --- | ---: | ---: |",
        *[f"| {t} | {fmt(c1[t])} | {fmt(c2[t])} |" for t in TABELAS],
        f"| Tempo de carga | {d1} s | {d2} s |".replace(".", ","), "",
        f"Resultado: **{'idempotente – mesmos totais nas duas execuções' if idem else 'ATENÇÃO: totais diferentes'}**.", "",
        "## Reconciliação", "",
        "| Verificação | Valor |", "| --- | ---: |",
        f"| Linhas na raw | {fmt(raw)} |",
        f"| Linhas na fato | {fmt(fato)} |",
        f"| Linhas em quarentena | {fmt(qua)} |",
        f"| raw − (fato + quarentena) | {fmt(raw - fato - qua)} |",
        f"| staging − fato (perdas na carga) | {fmt(stg - fato)} |",
        f"| Linhas da fato sem origem na staging | {fmt(orfas)} |", "",
        "## Reclamações por mês na fato", "",
        "| Mês | Reclamações |", "| --- | ---: |",
        *[f"| {nome} | {fmt(q)} |" for _, nome, q in por_mes], "",
    ]
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "carga_analytics.md").write_text("\n".join(md), encoding="utf-8")

    print("\n================ RESUMO ANALYTICS ================")
    for t in TABELAS:
        print(f"{t:<16} {fmt(c2[t]):>12}")
    print(f"idempotente:     {'SIM' if idem else 'NÃO'}")
    print(f"raw = fato + quarentena: {'SIM' if raw == fato + qua else 'NÃO'} ({fmt(raw)} = {fmt(fato)} + {fmt(qua)})")
    print(f"tempo de carga:  {d2} s")
    print("Relatório:       reports/carga_analytics.md")


if __name__ == "__main__":
    main()
