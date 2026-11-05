-- Camadas do pipeline (executado automaticamente na 1ª vez que o contêiner sobe)
CREATE SCHEMA IF NOT EXISTS raw;        -- dados como vieram da fonte (Sprint 1)
CREATE SCHEMA IF NOT EXISTS staging;    -- dados limpos e padronizados (Sprint 2)
CREATE SCHEMA IF NOT EXISTS analytics;  -- modelo dimensional e KPIs (Sprints 2 e 3)

CREATE TABLE IF NOT EXISTS raw.log_carga (
    id               BIGSERIAL PRIMARY KEY,
    arquivo          TEXT        NOT NULL,
    encoding         TEXT,
    separador        TEXT,
    colunas          INTEGER,
    linhas_carregadas BIGINT,
    tamanho_mb       NUMERIC(10,2),
    inicio           TIMESTAMPTZ NOT NULL,
    fim              TIMESTAMPTZ,
    duracao_seg      NUMERIC(10,1),
    status           TEXT        NOT NULL,
    observacao       TEXT
);
