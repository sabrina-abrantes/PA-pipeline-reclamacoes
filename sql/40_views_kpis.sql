-- =====================================================================
-- Sprint 3 · R09 – Views SQL dos indicadores (KPIs)
--
-- Os 5 KPIs do projeto, calculados da mesma forma em todas as views:
--   1. reclamacoes                 volume de reclamações finalizadas
--   2. indice_solucao_pct          metodologia Senacon: (resolvidas + não avaliadas) ÷ finalizadas
--   3. tempo_medio_resposta_dias   média de tempo_resposta das reclamações respondidas
--   4. respondidas_pct             respondidas ÷ finalizadas
--   5. nota_media                  média da nota (1 a 5) das reclamações avaliadas
-- Complementares:
--   indice_resolucao_avaliadas_pct  resolvidas ÷ avaliadas (visão "estrita", sem as não avaliadas)
--   avaliadas_pct                   avaliadas ÷ finalizadas
--
-- Views: vw_kpi_geral, vw_kpi_mensal, vw_kpi_segmento, vw_kpi_empresa, vw_kpi_uf
--        + vw_reclamacoes (fato com os atributos das dimensões, para consultas livres)
-- =====================================================================
DROP VIEW IF EXISTS analytics.vw_kpi_geral, analytics.vw_kpi_mensal, analytics.vw_kpi_segmento,
                    analytics.vw_kpi_empresa, analytics.vw_kpi_uf, analytics.vw_reclamacoes;

CREATE VIEW analytics.vw_reclamacoes AS
SELECT f.id_reclamacao, t.data AS data_finalizacao, t.ano, t.mes, t.nome_mes,
       e.nome_fantasia AS empresa, e.segmento_de_mercado,
       l.regiao, l.uf, l.cidade,
       p.area, p.assunto, p.grupo_problema, p.problema,
       c.sexo, c.faixa_etaria, c.como_comprou_contratou, c.procurou_empresa,
       f.respondida, f.tempo_resposta, f.situacao, f.avaliacao_reclamacao,
       f.avaliada, f.resolvida, f.nota_do_consumidor, f.possivel_duplicata
FROM analytics.fato_reclamacao f
JOIN analytics.dim_tempo      t USING (sk_tempo)
JOIN analytics.dim_empresa    e USING (sk_empresa)
JOIN analytics.dim_localidade l USING (sk_localidade)
JOIN analytics.dim_problema   p USING (sk_problema)
JOIN analytics.dim_consumidor c USING (sk_consumidor);

CREATE VIEW analytics.vw_kpi_geral AS
SELECT count(*)                                                                    AS reclamacoes,
       round(100.0 * count(*) FILTER (WHERE resolvida OR NOT avaliada) / count(*), 2) AS indice_solucao_pct,
       round(avg(tempo_resposta) FILTER (WHERE respondida), 2)                     AS tempo_medio_resposta_dias,
       round(100.0 * count(*) FILTER (WHERE respondida) / count(*), 2)             AS respondidas_pct,
       round(avg(nota_do_consumidor), 2)                                           AS nota_media,
       round(100.0 * count(*) FILTER (WHERE resolvida)
             / nullif(count(*) FILTER (WHERE avaliada), 0), 2)                     AS indice_resolucao_avaliadas_pct,
       round(100.0 * count(*) FILTER (WHERE avaliada) / count(*), 2)               AS avaliadas_pct
FROM analytics.fato_reclamacao;

CREATE VIEW analytics.vw_kpi_mensal AS
SELECT t.ano, t.mes, t.nome_mes,
       count(*)                                                                    AS reclamacoes,
       round(100.0 * count(*) FILTER (WHERE f.resolvida OR NOT f.avaliada) / count(*), 2) AS indice_solucao_pct,
       round(avg(f.tempo_resposta) FILTER (WHERE f.respondida), 2)                 AS tempo_medio_resposta_dias,
       round(100.0 * count(*) FILTER (WHERE f.respondida) / count(*), 2)           AS respondidas_pct,
       round(avg(f.nota_do_consumidor), 2)                                         AS nota_media,
       round(100.0 * count(*) FILTER (WHERE f.resolvida)
             / nullif(count(*) FILTER (WHERE f.avaliada), 0), 2)                   AS indice_resolucao_avaliadas_pct,
       round(100.0 * count(*) FILTER (WHERE f.avaliada) / count(*), 2)             AS avaliadas_pct
FROM analytics.fato_reclamacao f JOIN analytics.dim_tempo t USING (sk_tempo)
GROUP BY t.ano, t.mes, t.nome_mes;

CREATE VIEW analytics.vw_kpi_segmento AS
SELECT e.segmento_de_mercado,
       count(*)                                                                    AS reclamacoes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2)                          AS participacao_pct,
       round(100.0 * count(*) FILTER (WHERE f.resolvida OR NOT f.avaliada) / count(*), 2) AS indice_solucao_pct,
       round(avg(f.tempo_resposta) FILTER (WHERE f.respondida), 2)                 AS tempo_medio_resposta_dias,
       round(100.0 * count(*) FILTER (WHERE f.respondida) / count(*), 2)           AS respondidas_pct,
       round(avg(f.nota_do_consumidor), 2)                                         AS nota_media,
       round(100.0 * count(*) FILTER (WHERE f.resolvida)
             / nullif(count(*) FILTER (WHERE f.avaliada), 0), 2)                   AS indice_resolucao_avaliadas_pct
FROM analytics.fato_reclamacao f JOIN analytics.dim_empresa e USING (sk_empresa)
GROUP BY e.segmento_de_mercado;

-- Empresa = nome canônico (agrega os segmentos, se a empresa aparece em mais de um)
CREATE VIEW analytics.vw_kpi_empresa AS
SELECT e.nome_fantasia AS empresa,
       string_agg(DISTINCT e.segmento_de_mercado, ' | ')                           AS segmentos,
       count(*)                                                                    AS reclamacoes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 3)                          AS participacao_pct,
       round(100.0 * count(*) FILTER (WHERE f.resolvida OR NOT f.avaliada) / count(*), 2) AS indice_solucao_pct,
       round(avg(f.tempo_resposta) FILTER (WHERE f.respondida), 2)                 AS tempo_medio_resposta_dias,
       round(100.0 * count(*) FILTER (WHERE f.respondida) / count(*), 2)           AS respondidas_pct,
       round(avg(f.nota_do_consumidor), 2)                                         AS nota_media,
       round(100.0 * count(*) FILTER (WHERE f.resolvida)
             / nullif(count(*) FILTER (WHERE f.avaliada), 0), 2)                   AS indice_resolucao_avaliadas_pct
FROM analytics.fato_reclamacao f JOIN analytics.dim_empresa e USING (sk_empresa)
GROUP BY e.nome_fantasia;

CREATE VIEW analytics.vw_kpi_uf AS
SELECT l.regiao, l.uf,
       count(*)                                                                    AS reclamacoes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2)                          AS participacao_pct,
       round(100.0 * count(*) FILTER (WHERE f.resolvida OR NOT f.avaliada) / count(*), 2) AS indice_solucao_pct,
       round(avg(f.tempo_resposta) FILTER (WHERE f.respondida), 2)                 AS tempo_medio_resposta_dias,
       round(100.0 * count(*) FILTER (WHERE f.respondida) / count(*), 2)           AS respondidas_pct,
       round(avg(f.nota_do_consumidor), 2)                                         AS nota_media,
       round(100.0 * count(*) FILTER (WHERE f.resolvida)
             / nullif(count(*) FILTER (WHERE f.avaliada), 0), 2)                   AS indice_resolucao_avaliadas_pct
FROM analytics.fato_reclamacao f JOIN analytics.dim_localidade l USING (sk_localidade)
GROUP BY l.regiao, l.uf;
