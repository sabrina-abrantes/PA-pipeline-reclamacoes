# Pipeline de Engenharia de Dados para Análise de Reclamações de Consumidores

Projeto Aplicado – Pós-graduação em Engenharia e Arquitetura de Dados com IA (XP Educação).
Autora: Sabrina Abrantes Loures.

Pipeline em Python/Pandas e PostgreSQL que transforma os arquivos públicos de reclamações do
[Consumidor.gov.br](https://www.consumidor.gov.br) (ano de 2025) em uma base analítica confiável.

## Arquitetura (camadas)

| Camada | Schema | Conteúdo | Sprint |
| --- | --- | --- | --- |
| Bruta | `raw` | CSVs como vieram da fonte, tudo como texto, + log de carga | 1 |
| Tratada | `staging` | Dados limpos, tipados e padronizados; quarentena | 2 |
| Analítica | `analytics` | Modelo dimensional e views de KPIs | 2 e 3 |

## Pré-requisitos

- Python 3.10+
- Docker Desktop (ou Docker Engine + Compose)
- Git

## Como executar

```bash
# 1. Ambiente Python
python -m venv .venv
# Windows: .venv\Scripts\activate    |  Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. Configuração e banco
cp .env.example .env          # Windows: copy .env.example .env
docker compose up -d          # sobe o PostgreSQL e cria os schemas raw/staging/analytics

# 3. Dados: coloque os 12 CSVs mensais de 2025 em data/raw/

# 4. Pipeline da Sprint 1
python src/ingest_raw.py      # R02 – ingestão na camada bruta + log
python src/profile_raw.py     # R03 – relatório de qualidade (reports/)
python src/gerar_dicionario.py  # R04 – rascunho do dicionário (docs/)

# 5. Pipeline da Sprint 2
python src/transform_staging.py   # R05/R06 – limpeza, validação e quarentena (raw → staging)
python src/load_analytics.py      # R07/R08 – modelo dimensional e carga idempotente (staging → analytics)
```

O modelo dimensional está em `docs/modelo_dimensional.png` e os scripts SQL em `sql/`
(`10_staging.sql`, `20_modelo_dimensional.sql`, `30_carga_analytics.sql`).

## Estrutura

```
data/raw/      CSVs de origem (não versionados)
docs/          dicionário de dados e documentação
evidencias/    prints usados no relatório do Projeto Aplicado
logs/          log de carga (log_carga.csv)
reports/       relatório de qualidade e perfil das colunas
sql/           scripts SQL (00_init.sql cria os schemas)
src/           código do pipeline
```

## Status

- [x] Sprint 1 – Fundação e ingestão (R01–R04)
- [ ] Sprint 2 – Tratamento, modelagem e carga (R05–R08)
- [ ] Sprint 3 – Indicadores e análise (R09–R12)
