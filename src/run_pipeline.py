"""R12 – Orquestra o pipeline ponta a ponta com um único comando e mede o tempo de cada etapa.

Etapas: ingestão (raw) → limpeza/validação (staging) → modelo dimensional (analytics)
        → views de KPIs → reconciliação com o boletim → análise descritiva

Gera reports/execucao_pipeline.md e acrescenta uma linha em logs/execucoes_pipeline.csv.

Uso:
    python src/run_pipeline.py
"""
import csv
import sys
import time
from datetime import datetime

import analise_descritiva
import ingest_raw
import kpis
import load_analytics
import reconciliar_boletim
import transform_staging
from config import LOGS_DIR, REPORTS_DIR

META_MIN = 30


def main():
    sys.argv = sys.argv[:1]  # os scripts internos não recebem argumentos
    etapas = [
        ("1. Ingestão dos CSVs (raw)", ingest_raw.main),
        ("2. Limpeza, validação e quarentena (staging)", transform_staging.main),
        ("3. Modelo dimensional (analytics)", lambda: load_analytics.main(execucoes_carga=1)),
        ("4. Views de KPIs", kpis.main),
        ("5. Reconciliação com o Boletim 2025", reconciliar_boletim.main),
        ("6. Análise descritiva", analise_descritiva.main),
    ]
    inicio = datetime.now()
    tempos = []
    for nome, func in etapas:
        print(f"\n######## {nome} ########")
        t0 = time.time()
        func()
        tempos.append((nome, round(time.time() - t0, 1)))
    total = sum(t for _, t in tempos)
    dentro = total / 60 < META_MIN

    md = [
        "# Execução do pipeline ponta a ponta (Sprint 3 – R12)", "",
        f"Executado em {inicio:%d/%m/%Y %H:%M} com `python src/run_pipeline.py`.", "",
        "| Etapa | Tempo (s) | Tempo (min) |", "| --- | ---: | ---: |",
        *[f"| {n} | {t:.1f} | {t / 60:.1f} |".replace(".", ",") for n, t in tempos],
        f"| **Total** | **{total:.1f}** | **{total / 60:.1f}** |".replace(".", ","), "",
        f"Meta do objetivo SMART: menos de {META_MIN} minutos → **{'atingida' if dentro else 'NÃO atingida'}**.", "",
    ]
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "execucao_pipeline.md").write_text("\n".join(md), encoding="utf-8")
    LOGS_DIR.mkdir(exist_ok=True)
    arq = LOGS_DIR / "execucoes_pipeline.csv"
    novo = not arq.exists()
    with open(arq, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if novo:
            w.writerow(["inicio"] + [n for n, _ in tempos] + ["total_seg"])
        w.writerow([inicio.isoformat(timespec="seconds")] + [t for _, t in tempos] + [round(total, 1)])

    print("\n================ PIPELINE PONTA A PONTA ================")
    for n, t in tempos:
        print(f"{n:<48} {t:>8.1f} s")
    print(f"{'TOTAL':<48} {total:>8.1f} s  ({total / 60:.1f} min)")
    print(f"Meta < {META_MIN} min: {'ATINGIDA' if dentro else 'NÃO ATINGIDA'}")
    print("Relatório: reports/execucao_pipeline.md")


if __name__ == "__main__":
    main()
