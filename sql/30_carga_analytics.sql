-- =====================================================================
-- Sprint 2 · R08 – Carga do modelo dimensional a partir da staging
-- Idempotente: esvazia e recarrega tudo (rodar duas vezes dá o mesmo resultado).
-- =====================================================================
TRUNCATE analytics.fato_reclamacao, analytics.dim_tempo, analytics.dim_empresa,
         analytics.dim_localidade, analytics.dim_problema, analytics.dim_consumidor
         RESTART IDENTITY;

-- dim_tempo: todos os dias do ano (inclusive dias sem reclamação)
INSERT INTO analytics.dim_tempo
SELECT to_char(d, 'YYYYMMDD')::int, d::date,
       extract(year FROM d), extract(quarter FROM d), extract(month FROM d),
       (ARRAY['janeiro','fevereiro','março','abril','maio','junho','julho','agosto',
              'setembro','outubro','novembro','dezembro'])[extract(month FROM d)::int],
       extract(day FROM d), extract(isodow FROM d),
       (ARRAY['segunda','terça','quarta','quinta','sexta','sábado','domingo'])[extract(isodow FROM d)::int],
       extract(isodow FROM d) IN (6, 7)
FROM generate_series((SELECT date_trunc('year', min(data_finalizacao)) FROM staging.reclamacoes),
                     (SELECT date_trunc('year', max(data_finalizacao)) + interval '1 year - 1 day'
                        FROM staging.reclamacoes),
                     interval '1 day') AS d;

INSERT INTO analytics.dim_empresa (empresa_chave, nome_fantasia, segmento_de_mercado)
SELECT DISTINCT empresa_chave, nome_fantasia, segmento_de_mercado FROM staging.reclamacoes;

INSERT INTO analytics.dim_localidade (regiao, uf, cidade)
SELECT DISTINCT ON (uf, cidade) regiao, uf, cidade FROM staging.reclamacoes ORDER BY uf, cidade, regiao;

INSERT INTO analytics.dim_problema (area, assunto, grupo_problema, problema)
SELECT DISTINCT area, assunto, grupo_problema, problema FROM staging.reclamacoes;

INSERT INTO analytics.dim_consumidor (sexo, faixa_etaria, como_comprou_contratou, procurou_empresa)
SELECT DISTINCT sexo, faixa_etaria, como_comprou_contratou, procurou_empresa FROM staging.reclamacoes;

INSERT INTO analytics.fato_reclamacao (
    sk_tempo, sk_empresa, sk_localidade, sk_problema, sk_consumidor,
    respondida, tempo_resposta, situacao, avaliacao_reclamacao, avaliada, resolvida,
    nota_do_consumidor, interacao_com_judiciario, data_ultimo_complemento,
    colunas_set_disponiveis, possivel_duplicata, origem_arquivo, origem_linha)
SELECT
    to_char(s.data_finalizacao, 'YYYYMMDD')::int,
    e.sk_empresa, l.sk_localidade, p.sk_problema, c.sk_consumidor,
    s.respondida, s.tempo_resposta, s.situacao, s.avaliacao_reclamacao,
    s.avaliacao_reclamacao <> 'Não Avaliada',
    s.avaliacao_reclamacao = 'Resolvida',
    s.nota_do_consumidor, s.interacao_com_judiciario, s.data_ultimo_complemento,
    s.colunas_set_disponiveis, s.possivel_duplicata, s._arquivo, s._linha
FROM staging.reclamacoes s
JOIN analytics.dim_empresa    e ON e.empresa_chave = s.empresa_chave AND e.segmento_de_mercado = s.segmento_de_mercado
JOIN analytics.dim_localidade l ON l.uf = s.uf AND l.cidade = s.cidade
JOIN analytics.dim_problema   p ON (p.area, p.assunto, p.grupo_problema, p.problema)
                                 = (s.area, s.assunto, s.grupo_problema, s.problema)
JOIN analytics.dim_consumidor c ON (c.sexo, c.faixa_etaria, c.como_comprou_contratou, c.procurou_empresa)
                                 = (s.sexo, s.faixa_etaria, s.como_comprou_contratou, s.procurou_empresa);

CREATE INDEX IF NOT EXISTS ix_fato_tempo    ON analytics.fato_reclamacao (sk_tempo);
CREATE INDEX IF NOT EXISTS ix_fato_empresa  ON analytics.fato_reclamacao (sk_empresa);
CREATE INDEX IF NOT EXISTS ix_fato_problema ON analytics.fato_reclamacao (sk_problema);
ANALYZE analytics.fato_reclamacao;
