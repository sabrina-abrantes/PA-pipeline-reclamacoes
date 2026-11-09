# Validação da camada staging (Sprint 2 – R05/R06)

Gerado em 08/11/2026 18:09. Tempo de processamento: 302.6 s.

## Rastreabilidade (meta: 100% dos registros carregados ou em quarentena)

| Camada | Linhas |
| --- | ---: |
| raw.reclamacoes | 2.328.863 |
| staging.reclamacoes (aprovados) | 2.328.857 |
| staging.quarentena (rejeitados com motivo) | 6 |
| **Rastreados (staging + quarentena) ÷ raw** | **100,00%** |

## Quarentena por motivo

| Motivo | Linhas |
| --- | ---: |
| avaliacao_reclamacao vazia | 4 |
| situacao incompatível com avaliacao_reclamacao | 1 |
| tempo_resposta acima de 30 dias | 1 |

## Antes × depois da limpeza

| Verificação | raw | staging |
| --- | ---: | ---: |
| Valores com espaços nas pontas (todas as colunas de texto) | 816.849 | 0 |
| Nomes de empresa distintos | 1.741 | 1.730 |
| Cidades distintas (por UF) | 7.095 | 7.083 |
| Valores de região distintos | 5 | 5 |
| Sexo vazio | 51 | 0 |

## Tipagem (registros válidos na staging)

| Coluna / regra | Registros válidos | % |
| --- | ---: | ---: |
| data_finalizacao (DATE) | 2.328.857 | 100,00% |
| tempo_resposta (INTEGER, só nulo se não respondida) | 2.328.857 | 100,00% |
| nota_do_consumidor (1–5, só nula se não avaliada) | 2.328.857 | 100,00% |
| respondida / procurou_empresa (BOOLEAN) | 2.328.857 | 100,00% |

## Sinalizações

- Possíveis duplicatas sinalizadas (mantidas, não removidas – R12): **23.416**
- Registros de arquivos com as colunas de setembro/2025 disponíveis (R11): **245.645**

## Empresas com grafias unificadas (top 10)

| Nome canônico | Grafias na origem | Variações encontradas |
| --- | ---: | --- |
| SEGURO BET | 2 | "Seguro Bet", "SEGURO BET" |
| Suprema Bet | 2 | "Suprema Bet", "SUPREMA BET" |
| Estoque | 2 | "Estoque", "ESTOQUE" |
| Lottoland | 2 | "Lottoland", "LOTTOLAND" |
| BetFusion | 2 | "BetFusion", "BETFUSION" |
| Viação Sete | 2 | "VIACAO SETE", "Viação Sete" |
| Coopercred Unilever | 2 | "Coopercred Unilever", "COOPERCRED UNILEVER" |
| BrasilBet | 2 | "BrasilBet", "BRASILBET" |
| Unimed De Bebedouro | 2 | "Unimed De Bebedouro", "UNIMED DE BEBEDOURO" |
| Fabbitur | 2 | "Fabbitur", "FABBITUR" |
