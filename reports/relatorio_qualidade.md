# Relatório de qualidade – camada bruta (raw.reclamacoes)

Gerado em 08/11/2026 16:50. Fonte: Consumidor.gov.br, reclamações finalizadas em 2025.

## Visão geral

| Indicador | Valor |
| --- | --- |
| Linhas | 2.328.863 |
| Arquivos | 12 |
| Colunas de negócio | 21 |
| Linhas duplicadas (idênticas em todas as colunas) | 23.416 (1,01%) |

## Linhas por arquivo

| Arquivo | Linhas |
| --- | ---: |
| finalizadas_2025-01.csv | 148.779 |
| finalizadas_2025-02.csv | 153.600 |
| finalizadas_2025-03.csv | 140.158 |
| finalizadas_2025-04.csv | 164.806 |
| finalizadas_2025-05.csv | 168.829 |
| finalizadas_2025-06.csv | 182.794 |
| finalizadas_2025-07.csv | 200.456 |
| finalizadas_2025-08.csv | 213.306 |
| finalizadas_2025-09.csv | 245.646 |
| finalizadas_2025-10.csv | 243.398 |
| finalizadas_2025-11.csv | 192.038 |
| finalizadas_2025-12.csv | 275.053 |

## Perfil por coluna

| Coluna | % nulos | Distintos | Variações de grafia | Tipo sugerido | Tam. mín–máx |
| --- | ---: | ---: | ---: | --- | --- |
| regiao | 0,0% | 5 | 0 | texto | 2–2 |
| uf | 0,0% | 27 | 0 | texto | 2–2 |
| cidade | 0,0% | 6.586 | 8 | texto | 2–35 |
| sexo | 0,0% | 3 | 0 | texto | 1–1 |
| faixa_etaria | 0,0% | 7 | 0 | texto | 11–18 |
| data_finalizacao | 0,0% | 365 | 0 | data (aaaa-mm-dd) | 10–10 |
| tempo_resposta | 3,06% | 27 | 0 | inteiro | 1–2 |
| nome_fantasia | 0,0% | 1.740 | 10 | texto | 2–97 |
| segmento_de_mercado | 0,0% | 45 | 0 | texto | 6–71 |
| area | 0,0% | 14 | 0 | texto | 5–40 |
| assunto | 0,0% | 141 | 0 | texto | 3–161 |
| grupo_problema | 0,0% | 8 | 0 | texto | 10–28 |
| problema | 0,0% | 189 | 0 | texto | 12–200 |
| como_comprou_contratou | 0,0% | 9 | 0 | texto | 8–23 |
| procurou_empresa | 0,0% | 2 | 0 | texto | 1–1 |
| respondida | 0,0% | 2 | 0 | texto | 1–1 |
| situacao | 0,0% | 2 | 0 | texto | 19–23 |
| avaliacao_reclamacao | 0,0% | 3 | 0 | texto | 9–13 |
| nota_do_consumidor | 66,95% | 5 | 0 | inteiro | 1–1 |
| interacao_com_judiciario | 89,45% | 2 | 0 | texto | 1–1 |
| ultimo_complemento_consumidor | 96,21% | 72 | 0 | data (dd/mm/aaaa) | 10–10 |

## Regras de domínio

| Coluna | Regra | Violações |
| --- | --- | ---: |
| uf | UF válida (27 siglas) | 0 |
| nota_do_consumidor | Nota entre 1 e 5 | 0 |
| tempo_resposta | Tempo de resposta inteiro entre 0 e 30 dias | 1 |
| respondida | Respondida = S ou N | 0 |
| sexo | Sexo = F, M ou O | 0 |

## Valores mais frequentes

- **regiao**: SE (1.144.694) | NE (442.390) | S  (373.202) | CO (238.222) | N  (130.355)
- **uf**: SP (593.573) | MG (271.341) | RJ (233.198) | PR (164.289) | BA (136.215)
- **cidade**: São Paulo (209.867) | Rio de Janeiro (115.855) | Brasília (84.312) | Belo Horizonte (72.690) | Salvador (61.500)
- **sexo**: M (1.294.424) | F (1.032.732) | O (1.656)
- **faixa_etaria**: entre 31 a 40 anos (765.373) | entre 21 a 30 anos (563.347) | entre 41 a 50 anos (516.386) | entre 51 a 60 anos (231.684) | entre 61 a 70 anos (144.381)
- **data_finalizacao**: 2025-11-14 (16.574) | 2025-12-10 (16.265) | 2025-12-08 (15.333) | 2025-06-27 (15.257) | 2025-11-18 (15.220)
- **tempo_resposta**: 10 (358.540) | 8 (310.551) | 9 (283.069) | 7 (240.717) | 1 (226.178)
- **nome_fantasia**: Nubank (151.493) | Serasa Experian  (144.110) | Banco Santander (83.667) | Banco do Brasil (78.188) | Banco Bradesco (73.308)
- **segmento_de_mercado**: Bancos, Financeiras e Administradoras de Cartão (997.651) | Operadoras de Telecomunicações (Telefonia, Internet, TV por assinatura) (217.849) | Bancos de Dados e Cadastros de Consumidores (149.633) | Transporte Aéreo (99.480) | Empresas de Pagamento Eletrônico (91.746)
- **area**: Serviços Financeiros (1.401.280) | Demais Serviços  (187.276) | Telecomunicações (180.903) | Transportes (115.946) | Demais Produtos (102.298)
- **assunto**: Cartão de Crédito / Cartão de Débito / Cartão de Loja (433.240) | Crédito Pessoal e Demais Empréstimos (exceto financiamento de imóveis e veículos) (278.775) | Aéreo (105.578) | Consulta / Monitoramento de CPF (93.534) | Crédito Consignado / Cartão de Crédito Consignado / RMC (para beneficiários do INSS) (92.085)
- **grupo_problema**: Cobrança / Contestação (1.214.199) | Contrato / Oferta (292.467) | Atendimento / SAC (277.386) | Vício de Qualidade (235.967) | Dados Pessoais e Privacidade (184.449)
- **problema**: Cálculo de juros, saldo devedor (contestação, solicitação de histórico, dúvidas) (201.522) | Cobrança indevida / abusiva para alterar ou cancelar o contrato (190.231) | Renegociação / parcelamento de dívida (168.580) | Cobrança por serviço/produto não contratado / não reconhecido / não solicitado (116.827) | Dificuldade / atraso na devolução de valores pagos / reembolso / retenção de valores (102.761)
- **como_comprou_contratou**: Internet (1.107.002) | Não comprei / contratei (476.841) | Loja física (373.842) | Telefone (279.913) | Domicílio (45.973)
- **procurou_empresa**: S (1.808.854) | N (520.009)
- **respondida**: S (2.257.501) | N (71.362)
- **situacao**: Finalizada não avaliada (1.559.224) | Finalizada avaliada (769.639)
- **avaliacao_reclamacao**: Não Avaliada (1.559.223) | Não Resolvida (432.572) | Resolvida (337.064)
- **nota_do_consumidor**: 1 (386.704) | 5 (219.162) | 3 (65.266) | 4 (59.650) | 2 (38.858)
- **interacao_com_judiciario**: N (245.642) | S (4)
- **ultimo_complemento_consumidor**: 01/09/2025 (3.819) | 02/09/2025 (3.737) | 03/09/2025 (3.487) | 09/09/2025 (3.481) | 08/09/2025 (3.416)

## Achados e próximos passos

_Preencha aqui as suas conclusões (ex.: colunas com muitos nulos e por quê, problemas de grafia, o que vira regra de limpeza na Sprint 2)._
