# Dicionário de dados – raw.reclamacoes

Versão 1 – gerado em 08/11/2026. Fonte: Consumidor.gov.br (dados abertos, 2025).
Colunas de controle adicionadas pelo pipeline: `_arquivo` (CSV de origem), `_linha` (linha no CSV), `_carga_em` (data/hora da carga).

| Campo | Descrição | Tipo sugerido | % nulos | Domínio / exemplos | Regra de tratamento (Sprint 2) |
| --- | --- | --- | ---: | --- | --- |
| regiao | Região do Brasil do consumidor (N, NE, CO, SE, S) | texto | 0.0% | SE (1,144,694) / NE (442,390) / S  (373,202) / CO (238,222) / N  (130,355) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| uf | Unidade da Federação do consumidor | texto | 0.0% | SP; MG; RJ … (27 valores) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| cidade | Município do consumidor | texto | 0.0% | São Paulo; Rio de Janeiro; Brasília … (6,586 valores) | Remover espaços extras; padronizar maiúsculas/minúsculas; unificar variações de grafia |
| sexo | Sexo informado pelo consumidor | texto | 0.0% | M (1,294,424) / F (1,032,732) / O (1,656) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| faixa_etaria | Faixa etária do consumidor | texto | 0.0% | entre 31 a 40 anos (765,373) / entre 21 a 30 anos (563,347) / entre 41 a 50 anos (516,386) / entre 51 a 60 anos (231,684) / entre 61 a 70 anos (144,381) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| data_finalizacao | Data de finalização da reclamação | data (aaaa-mm-dd) | 0.0% | 2025-11-14; 2025-12-10; 2025-12-08 … (365 valores) | Converter para DATE (ISO) |
| tempo_resposta | Dias entre a abertura e a resposta da empresa | inteiro | 3.06% | 10; 8; 9 … (27 valores) | Converter para INTEGER; valores não numéricos → quarentena; tratar nulos (manter NULL e documentar motivo) |
| nome_fantasia | Nome fantasia da empresa reclamada | texto | 0.0% | Nubank; Serasa Experian ; Banco Santander … (1,740 valores) | Remover espaços extras; padronizar maiúsculas/minúsculas; unificar variações de grafia |
| segmento_de_mercado | Segmento de mercado da empresa | texto | 0.0% | Bancos, Financeiras e Administradoras de Cartão; Operadoras de Telecomunicações (Telefonia, Internet, TV por assinatura); Bancos de Dados e Cadastros de Consumidores … (45 valores) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| area | Área temática da reclamação | texto | 0.0% | Serviços Financeiros (1,401,280) / Demais Serviços  (187,276) / Telecomunicações (180,903) / Transportes (115,946) / Demais Produtos (102,298) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| assunto | Assunto da reclamação | texto | 0.0% | Cartão de Crédito / Cartão de Débito / Cartão de Loja; Crédito Pessoal e Demais Empréstimos (exceto financiamento de imóveis e veículos); Aéreo … (141 valores) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| grupo_problema | Grupo do problema relatado | texto | 0.0% | Cobrança / Contestação (1,214,199) / Contrato / Oferta (292,467) / Atendimento / SAC (277,386) / Vício de Qualidade (235,967) / Dados Pessoais e Privacidade (184,449) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| problema | Problema específico relatado | texto | 0.0% | Cálculo de juros, saldo devedor (contestação, solicitação de histórico, dúvidas); Cobrança indevida / abusiva para alterar ou cancelar o contrato; Renegociação / parcelamento de dívida … (189 valores) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| como_comprou_contratou | Canal de compra ou contratação | texto | 0.0% | Internet (1,107,002) / Não comprei / contratei (476,841) / Loja física (373,842) / Telefone (279,913) / Domicílio (45,973) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| procurou_empresa | Se o consumidor procurou a empresa antes de reclamar (S/N) | texto | 0.0% | S (1,808,854) / N (520,009) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| respondida | Se a empresa respondeu a reclamação (S/N) | texto | 0.0% | S (2,257,501) / N (71,362) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| situacao | Situação final da reclamação | texto | 0.0% | Finalizada não avaliada (1,559,224) / Finalizada avaliada (769,639) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| avaliacao_reclamacao | Avaliação do consumidor: Resolvida, Não Resolvida ou Não Avaliada | texto | 0.0% | Não Avaliada (1,559,223) / Não Resolvida (432,572) / Resolvida (337,064) | Remover espaços extras; padronizar maiúsculas/minúsculas |
| nota_do_consumidor | Nota de satisfação dada pelo consumidor (1 a 5) | inteiro | 66.95% | 1 (386,704) / 5 (219,162) / 3 (65,266) / 4 (59,650) / 2 (38,858) | Converter para INTEGER; valores não numéricos → quarentena; tratar nulos (manter NULL e documentar motivo) |
| interacao_com_judiciario | A DESCREVER | texto | 89.45% | N (245,642) / S (4) | Remover espaços extras; padronizar maiúsculas/minúsculas; tratar nulos (manter NULL e documentar motivo) |
| ultimo_complemento_consumidor | A DESCREVER | data (dd/mm/aaaa) | 96.21% | 01/09/2025; 02/09/2025; 03/09/2025 … (72 valores) | Converter para DATE (dd/mm/aaaa); tratar nulos (manter NULL e documentar motivo) |
