# Carga do modelo dimensional (Sprint 2 – R07/R08)

Gerado em 08/11/2026 20:52.

## Modelo (esquema estrela)

- **fato_reclamacao** – 1 linha por reclamação; medidas: respondida, tempo_resposta, avaliada, resolvida, nota
- **dim_tempo** – data de finalização (ano, trimestre, mês, dia da semana)
- **dim_empresa** – empresa (nome canônico) e segmento de mercado
- **dim_localidade** – região, UF e cidade do consumidor
- **dim_problema** – área, assunto, grupo de problema e problema
- **dim_consumidor** – sexo, faixa etária, canal de compra e se procurou a empresa

## Idempotência (carga executada duas vezes)

| Tabela | 1ª execução | 2ª execução |
| --- | ---: | ---: |
| dim_tempo | 365 | 365 |
| dim_empresa | 1.732 | 1.732 |
| dim_localidade | 7.083 | 7.083 |
| dim_problema | 4.414 | 4.414 |
| dim_consumidor | 359 | 359 |
| fato_reclamacao | 2.328.857 | 2.328.857 |
| Tempo de carga | 827,7 s | 809,6 s |

Resultado: **idempotente – mesmos totais nas duas execuções**.

## Reconciliação

| Verificação | Valor |
| --- | ---: |
| Linhas na raw | 2.328.863 |
| Linhas na fato | 2.328.857 |
| Linhas em quarentena | 6 |
| raw − (fato + quarentena) | 0 |
| staging − fato (perdas na carga) | 0 |
| Linhas da fato sem origem na staging | 0 |

## Reclamações por mês na fato

| Mês | Reclamações |
| --- | ---: |
| janeiro | 148.779 |
| fevereiro | 153.600 |
| março | 140.158 |
| abril | 164.806 |
| maio | 168.829 |
| junho | 182.793 |
| julho | 200.456 |
| agosto | 213.305 |
| setembro | 245.645 |
| outubro | 243.397 |
| novembro | 192.037 |
| dezembro | 275.052 |
