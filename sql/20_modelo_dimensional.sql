-- =====================================================================
-- Sprint 2 · R07 – Modelo dimensional (esquema estrela) no schema analytics
-- Grão da fato: 1 linha = 1 reclamação finalizada aprovada na staging.
-- Idempotente: recria as tabelas a cada execução.
-- =====================================================================
DROP TABLE IF EXISTS analytics.fato_reclamacao;
DROP TABLE IF EXISTS analytics.dim_tempo;
DROP TABLE IF EXISTS analytics.dim_empresa;
DROP TABLE IF EXISTS analytics.dim_localidade;
DROP TABLE IF EXISTS analytics.dim_problema;
DROP TABLE IF EXISTS analytics.dim_consumidor;

CREATE TABLE analytics.dim_tempo (
    sk_tempo        INTEGER PRIMARY KEY,           -- aaaammdd
    data            DATE        NOT NULL UNIQUE,
    ano             SMALLINT    NOT NULL,
    trimestre       SMALLINT    NOT NULL,
    mes             SMALLINT    NOT NULL,
    nome_mes        TEXT        NOT NULL,
    dia             SMALLINT    NOT NULL,
    dia_semana      SMALLINT    NOT NULL,          -- 1 = segunda ... 7 = domingo
    nome_dia_semana TEXT        NOT NULL,
    fim_de_semana   BOOLEAN     NOT NULL
);

CREATE TABLE analytics.dim_empresa (
    sk_empresa          SERIAL PRIMARY KEY,
    empresa_chave       TEXT NOT NULL,             -- nome normalizado (sem acento, maiúsculas)
    nome_fantasia       TEXT NOT NULL,             -- grafia canônica (a mais frequente)
    segmento_de_mercado TEXT NOT NULL,
    UNIQUE (empresa_chave, segmento_de_mercado)
);

CREATE TABLE analytics.dim_localidade (
    sk_localidade SERIAL PRIMARY KEY,
    regiao        TEXT NOT NULL,
    uf            CHAR(2) NOT NULL,
    cidade        TEXT NOT NULL,
    UNIQUE (uf, cidade)
);

CREATE TABLE analytics.dim_problema (
    sk_problema    SERIAL PRIMARY KEY,
    area           TEXT NOT NULL,
    assunto        TEXT NOT NULL,
    grupo_problema TEXT NOT NULL,
    problema       TEXT NOT NULL,
    UNIQUE (area, assunto, grupo_problema, problema)
);

-- Dimensão de perfil (junk dimension): atributos de baixa cardinalidade do consumidor e da compra
CREATE TABLE analytics.dim_consumidor (
    sk_consumidor          SERIAL PRIMARY KEY,
    sexo                   TEXT    NOT NULL,
    faixa_etaria           TEXT    NOT NULL,
    como_comprou_contratou TEXT    NOT NULL,
    procurou_empresa       BOOLEAN NOT NULL,
    UNIQUE (sexo, faixa_etaria, como_comprou_contratou, procurou_empresa)
);

CREATE TABLE analytics.fato_reclamacao (
    id_reclamacao            BIGSERIAL PRIMARY KEY,
    sk_tempo                 INTEGER  NOT NULL REFERENCES analytics.dim_tempo,
    sk_empresa               INTEGER  NOT NULL REFERENCES analytics.dim_empresa,
    sk_localidade            INTEGER  NOT NULL REFERENCES analytics.dim_localidade,
    sk_problema              INTEGER  NOT NULL REFERENCES analytics.dim_problema,
    sk_consumidor            INTEGER  NOT NULL REFERENCES analytics.dim_consumidor,
    respondida               BOOLEAN  NOT NULL,
    tempo_resposta           SMALLINT,             -- NULL quando não respondida
    situacao                 TEXT     NOT NULL,
    avaliacao_reclamacao     TEXT     NOT NULL,
    avaliada                 BOOLEAN  NOT NULL,
    resolvida                BOOLEAN  NOT NULL,
    nota_do_consumidor       SMALLINT,             -- NULL quando não avaliada
    interacao_com_judiciario BOOLEAN,              -- NULL quando não disponível na fonte
    data_ultimo_complemento  DATE,
    colunas_set_disponiveis  BOOLEAN  NOT NULL,    -- a fonte trazia as colunas de set/2025?
    possivel_duplicata       BOOLEAN  NOT NULL,
    origem_arquivo           TEXT     NOT NULL,    -- rastreabilidade até o CSV
    origem_linha             BIGINT   NOT NULL,
    UNIQUE (origem_arquivo, origem_linha)
);
