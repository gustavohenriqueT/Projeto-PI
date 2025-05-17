-- Tabela principal de dados de transporte
CREATE TABLE IF NOT EXISTS transport_data (
    id SERIAL PRIMARY KEY,
    line VARCHAR(50) NOT NULL,
    passengers INTEGER CHECK (passengers >= 0),
    lat FLOAT NOT NULL,
    lon FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de clusters (com relação correta)
CREATE TABLE IF NOT EXISTS transport_clusters (
    id INTEGER PRIMARY KEY REFERENCES transport_data(id) ON DELETE CASCADE,
    cluster INTEGER NOT NULL,
    CONSTRAINT valid_cluster CHECK (cluster BETWEEN 0 AND 5)
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_transport_line ON transport_data(line);
CREATE INDEX IF NOT EXISTS idx_cluster ON transport_clusters(cluster);

-- Tabel