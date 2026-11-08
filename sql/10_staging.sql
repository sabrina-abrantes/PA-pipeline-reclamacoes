-- =====================================================================
-- Sprint 2 · R05 + R06 – Limpeza, padronização, validação e quarentena
-- Origem: raw.reclamacoes (texto bruto)  →  staging.reclamacoes (tipado)
--                                         →  staging.quarentena (rejeitados + motivo)
-- Regras R1–R13 definidas no relatório de qualidade da Sprint 1.
-- Idempotente: recria as tabelas a cada execução.
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Colunas que só existem em parte do período (ex.: setembro/2025) podem não existir
-- na raw se nenhum arquivo as trouxe. Garante que existam (como TEXT) para o SQL abaixo.
ALTER TABLE raw.reclamacoes ADD COLUMN IF NOT EXISTS interacao_com_judiciario TEXT;
ALTER TABLE raw.reclamacoes ADD COLUMN IF NOT EXISTS ultimo_complemento_consumidor TEXT;

DROP TABLE IF EXISTS staging.reclamacoes;
DROP TABLE IF EXISTS staging.quarentena;
DROP TABLE IF EXISTS staging._base;

-- Função auxiliar: remove espaços nas pontas e espaços duplicados (R1)
CREATE OR REPLACE FUNCTION staging.limpa(t TEXT) RETURNS TEXT
LANGUAGE sql IMMUTABLE AS $$ SELECT nullif(regexp_replace(btrim(t), '\s+', ' ', 'g'), '') $$;

-- Função auxiliar: chave normalizada (maiúsculas, sem acento, sem espaços extras) (R2, R3)
CREATE OR REPLACE FUNCTION staging.chave(t TEXT) RETURNS TEXT
LANGUAGE sql STABLE AS $$ SELECT upper(unaccent(staging.limpa(t))) $$;

-- 1) Base limpa e tipada + motivos de rejeição ----------------------------------------
CREATE TABLE staging._base AS
WITH limpo AS (
    SELECT
        r._arquivo, r._linha,
        staging.limpa(r.regiao)                         AS regiao,
        upper(staging.limpa(r.uf))                      AS uf,
        staging.limpa(r.cidade)                         AS cidade_original,
        staging.chave(r.cidade)                         AS cidade_chave,
        coalesce(staging.limpa(r.sexo), 'Não informado') AS sexo,                    -- R9
        staging.limpa(r.faixa_etaria)                   AS faixa_etaria,
        staging.limpa(r.data_finalizacao)               AS data_finalizacao_txt,
        staging.limpa(r.tempo_resposta)                 AS tempo_resposta_txt,
        staging.limpa(r.nome_fantasia)                  AS nome_fantasia_original,
        staging.chave(r.nome_fantasia)                  AS empresa_chave,
        staging.limpa(r.segmento_de_mercado)            AS segmento_de_mercado,
        staging.limpa(r.area)                           AS area,
        staging.limpa(r.assunto)                        AS assunto,
        staging.limpa(r.grupo_problema)                 AS grupo_problema,
        staging.limpa(r.problema)                       AS problema,
        staging.limpa(r.como_comprou_contratou)         AS como_comprou_contratou,
        upper(staging.limpa(r.procurou_empresa))        AS procurou_empresa_txt,
        upper(staging.limpa(r.respondida))              AS respondida_txt,
        staging.limpa(r.situacao)                       AS situacao,
        staging.limpa(r.avaliacao_reclamacao)           AS avaliacao_reclamacao,
        staging.limpa(r.nota_do_consumidor)             AS nota_txt,
        upper(staging.limpa(r.interacao_com_judiciario)) AS interacao_txt,
        staging.limpa(r.ultimo_complemento_consumidor)  AS ultimo_complemento_txt,
        -- R11: a coluna existe no arquivo de origem? (só setembro/2025 traz as 2 colunas novas)
        (r.interacao_com_judiciario IS NOT NULL OR r.ultimo_complemento_consumidor IS NOT NULL
         OR r._arquivo IN (SELECT DISTINCT _arquivo FROM raw.reclamacoes
                           WHERE interacao_com_judiciario IS NOT NULL))  AS colunas_set_disponiveis,
        md5(concat_ws('§', r.regiao, r.uf, r.cidade, r.sexo, r.faixa_etaria, r.data_finalizacao,
                      r.tempo_resposta, r.nome_fantasia, r.segmento_de_mercado, r.area, r.assunto,
                      r.grupo_problema, r.problema, r.como_comprou_contratou, r.procurou_empresa,
                      r.respondida, r.situacao, r.avaliacao_reclamacao, r.nota_do_consumidor,
                      r.interacao_com_judiciario, r.ultimo_complemento_consumidor)) AS hash_linha
    FROM raw.reclamacoes r
),
tipado AS (
    SELECT l.*,
        CASE WHEN data_finalizacao_txt ~ '^\d{4}-\d{2}-\d{2}$'
             THEN to_date(data_finalizacao_txt, 'YYYY-MM-DD') END                      AS data_finalizacao,   -- R4
        CASE WHEN ultimo_complemento_txt ~ '^\d{2}/\d{2}/\d{4}$'
             THEN to_date(ultimo_complemento_txt, 'DD/MM/YYYY') END                    AS data_ultimo_complemento, -- R5
        CASE WHEN tempo_resposta_txt ~ '^\d{1,3}$' THEN tempo_resposta_txt::int END    AS tempo_resposta,     -- R6
        CASE WHEN nota_txt ~ '^[1-5]$' THEN nota_txt::smallint END                     AS nota_do_consumidor, -- R7
        CASE procurou_empresa_txt WHEN 'S' THEN true WHEN 'N' THEN false END           AS procurou_empresa,   -- R10
        CASE respondida_txt       WHEN 'S' THEN true WHEN 'N' THEN false END           AS respondida,
        CASE interacao_txt        WHEN 'S' THEN true WHEN 'N' THEN false END           AS interacao_com_judiciario
    FROM limpo l
)
SELECT t.*,
    -- R12: linhas idênticas são mantidas; a 2ª ocorrência em diante é sinalizada
    (row_number() OVER (PARTITION BY hash_linha ORDER BY _arquivo, _linha) > 1) AS possivel_duplicata,
    -- R6–R8 e validações de domínio: motivos de quarentena (vazio = registro aprovado)
    nullif(concat_ws('; ',
        CASE WHEN data_finalizacao IS NULL THEN 'data_finalizacao ausente ou inválida' END,
        CASE WHEN uf IS NULL OR uf NOT IN ('AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
                                           'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO')
             THEN 'UF inválida' END,
        CASE WHEN empresa_chave IS NULL THEN 'empresa ausente' END,
        CASE WHEN num_nulls(regiao, cidade_chave, faixa_etaria, segmento_de_mercado, area, assunto,
                            grupo_problema, problema, como_comprou_contratou, procurou_empresa, situacao) > 0
             THEN 'campo obrigatório vazio' END,
        CASE WHEN respondida IS NULL THEN 'respondida fora de S/N' END,
        CASE WHEN tempo_resposta_txt IS NOT NULL AND tempo_resposta IS NULL THEN 'tempo_resposta não numérico' END,
        CASE WHEN tempo_resposta > 30 THEN 'tempo_resposta acima de 30 dias' END,
        CASE WHEN respondida AND tempo_resposta IS NULL THEN 'respondida sem tempo_resposta' END,
        CASE WHEN avaliacao_reclamacao IS NULL THEN 'avaliacao_reclamacao vazia' END,
        CASE WHEN avaliacao_reclamacao IS NOT NULL
              AND (situacao = 'Finalizada avaliada') <> (avaliacao_reclamacao <> 'Não Avaliada')
             THEN 'situacao incompatível com avaliacao_reclamacao' END,
        CASE WHEN nota_txt IS NOT NULL AND nota_do_consumidor IS NULL THEN 'nota fora de 1 a 5' END,
        CASE WHEN avaliacao_reclamacao IN ('Resolvida','Não Resolvida') AND nota_do_consumidor IS NULL
             THEN 'reclamação avaliada sem nota' END
    ), '') AS motivo_quarentena
FROM tipado t;

-- R2: nome canônico da empresa = grafia mais frequente dentro da mesma chave
CREATE TEMP TABLE _empresa_canonica AS
SELECT DISTINCT ON (empresa_chave) empresa_chave, nome_fantasia_original AS nome_fantasia
FROM (SELECT empresa_chave, nome_fantasia_original, count(*) AS n
      FROM staging._base WHERE empresa_chave IS NOT NULL GROUP BY 1, 2) x
ORDER BY empresa_chave, n DESC, nome_fantasia_original;

-- R3: idem para cidade (por UF)
CREATE TEMP TABLE _cidade_canonica AS
SELECT DISTINCT ON (uf, cidade_chave) uf, cidade_chave, cidade_original AS cidade
FROM (SELECT uf, cidade_chave, cidade_original, count(*) AS n
      FROM staging._base WHERE cidade_chave IS NOT NULL GROUP BY 1, 2, 3) x
ORDER BY uf, cidade_chave, n DESC, cidade_original;

-- 2) Registros aprovados ------------------------------------------------------------------
CREATE TABLE staging.reclamacoes AS
SELECT
    b._arquivo, b._linha,
    b.regiao, b.uf, c.cidade, b.cidade_chave, b.sexo, b.faixa_etaria,
    b.data_finalizacao,
    extract(year FROM b.data_finalizacao)::int  AS ano_finalizacao,             -- R13
    extract(month FROM b.data_finalizacao)::int AS mes_finalizacao,
    b.tempo_resposta,
    e.nome_fantasia, b.empresa_chave, b.nome_fantasia_original,
    b.segmento_de_mercado, b.area, b.assunto, b.grupo_problema, b.problema,
    b.como_comprou_contratou, b.procurou_empresa, b.respondida,
    b.situacao, b.avaliacao_reclamacao, b.nota_do_consumidor,
    b.interacao_com_judiciario, b.data_ultimo_complemento, b.colunas_set_disponiveis,
    b.possivel_duplicata
FROM staging._base b
LEFT JOIN _empresa_canonica e USING (empresa_chave)
LEFT JOIN _cidade_canonica  c ON c.uf = b.uf AND c.cidade_chave = b.cidade_chave
WHERE b.motivo_quarentena IS NULL;

-- 3) Quarentena: linha bruta original + motivo -----------------------------------------------
CREATE TABLE staging.quarentena AS
SELECT b.motivo_quarentena, r.*
FROM staging._base b
JOIN raw.reclamacoes r ON r._arquivo = b._arquivo AND r._linha = b._linha
WHERE b.motivo_quarentena IS NOT NULL;

DROP TABLE staging._base;

CREATE INDEX ix_stg_reclamacoes_data    ON staging.reclamacoes (data_finalizacao);
CREATE INDEX ix_stg_reclamacoes_empresa ON staging.reclamacoes (empresa_chave);
ANALYZE staging.reclamacoes;
