"""R04 – Gera o rascunho do dicionário de dados a partir do perfilamento (R03).

Lê reports/perfil_colunas.csv e escreve docs/dicionario_dados.md com:
  campo, descrição, tipo sugerido, % nulos, domínio/exemplos e regra de tratamento prevista.

As descrições das colunas conhecidas do Consumidor.gov.br já vêm preenchidas;
revise todas e complete as marcadas com "A DESCREVER".

Uso:
    python src/gerar_dicionario.py
"""
import csv
from datetime import datetime

from config import DOCS_DIR, REPORTS_DIR

# Colunas usuais da base do Consumidor.gov.br (nomes já normalizados pelo ingest_raw.py).
DESCRICOES = {
    "regiao": "Região do Brasil do consumidor (N, NE, CO, SE, S)",
    "uf": "Unidade da Federação do consumidor",
    "cidade": "Município do consumidor",
    "sexo": "Sexo informado pelo consumidor",
    "faixa_etaria": "Faixa etária do consumidor",
    "ano_abertura": "Ano de abertura da reclamação",
    "mes_abertura": "Mês de abertura da reclamação",
    "data_abertura": "Data em que o consumidor registrou a reclamação",
    "data_resposta": "Data em que a empresa respondeu",
    "data_analise": "Data de análise pelo gestor da plataforma",
    "data_recusa": "Data de recusa da reclamação, quando houver",
    "data_finalizacao": "Data de finalização da reclamação",
    "prazo_resposta": "Data-limite para a empresa responder",
    "prazo_analise_gestor": "Prazo para análise do gestor",
    "tempo_resposta": "Dias entre a abertura e a resposta da empresa",
    "nome_fantasia": "Nome fantasia da empresa reclamada",
    "segmento_de_mercado": "Segmento de mercado da empresa",
    "area": "Área temática da reclamação",
    "assunto": "Assunto da reclamação",
    "grupo_problema": "Grupo do problema relatado",
    "problema": "Problema específico relatado",
    "como_comprou_contratou": "Canal de compra ou contratação",
    "procurou_empresa": "Se o consumidor procurou a empresa antes de reclamar (S/N)",
    "respondida": "Se a empresa respondeu a reclamação (S/N)",
    "situacao": "Situação final da reclamação",
    "avaliacao_reclamacao": "Avaliação do consumidor: Resolvida, Não Resolvida ou Não Avaliada",
    "nota_do_consumidor": "Nota de satisfação dada pelo consumidor (1 a 5)",
    "analise_da_recusa": "Resultado da análise de recusa",
    "edicao_de_conteudo": "Indica se houve edição de conteúdo pelo gestor",
    "interacao_do_gestor": "Indica se houve interação do gestor",
    "total": "Contador de registros (normalmente 1)",
}

REGRAS = {
    "data (dd/mm/aaaa)": "Converter para DATE (dd/mm/aaaa)",
    "data (aaaa-mm-dd)": "Converter para DATE (ISO)",
    "inteiro": "Converter para INTEGER; valores não numéricos → quarentena",
    "decimal": "Converter para NUMERIC (trocar vírgula por ponto)",
    "texto": "Remover espaços extras; padronizar maiúsculas/minúsculas",
    "vazio": "Avaliar descarte da coluna",
}


def main():
    perfil = list(csv.DictReader(open(REPORTS_DIR / "perfil_colunas.csv", encoding="utf-8"), delimiter=";"))
    linhas = [
        "# Dicionário de dados – raw.reclamacoes",
        "",
        f"Versão 1 – gerado em {datetime.now():%d/%m/%Y}. Fonte: Consumidor.gov.br (dados abertos, 2025).",
        "Colunas de controle adicionadas pelo pipeline: `_arquivo` (CSV de origem), `_linha` (linha no CSV), "
        "`_carga_em` (data/hora da carga).",
        "",
        "| Campo | Descrição | Tipo sugerido | % nulos | Domínio / exemplos | Regra de tratamento (Sprint 2) |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for p in perfil:
        distintos = int(p["distintos"])
        exemplos = p["top_valores"] if distintos <= 15 else "; ".join(
            v.rsplit(" (", 1)[0] for v in p["top_valores"].split(" | ")[:3]) + f" … ({distintos:,} valores)"
        regra = REGRAS.get(p["tipo_sugerido"], "")
        if float(p["pct_nulos"]) > 0:
            regra += "; tratar nulos (manter NULL e documentar motivo)"
        if int(p["variacoes_grafia"]) > 0:
            regra += "; unificar variações de grafia"
        linhas.append(
            f"| {p['coluna']} | {DESCRICOES.get(p['coluna'], 'A DESCREVER')} | {p['tipo_sugerido']} | "
            f"{p['pct_nulos']}% | {exemplos.replace('|', '/')} | {regra} |"
        )
    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "dicionario_dados.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    faltam = sum(1 for p in perfil if p["coluna"] not in DESCRICOES)
    print(f"OK: docs/dicionario_dados.md ({len(perfil)} campos; {faltam} a descrever manualmente)")


if __name__ == "__main__":
    main()
