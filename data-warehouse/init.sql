-- Tabela principal de dados de transporte atualizada
CREATE TABLE IF NOT EXISTS transport_data (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
    id_veiculo VARCHAR(50),
    linha VARCHAR(50) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    numero_passageiros INTEGER CHECK (numero_passageiros >= 0),
    tempo_viagem_minutos INTEGER,
    hora INTEGER,
    horario_pico BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices atualizados
CREATE INDEX IF NOT EXISTS idx_transport_line ON transport_data(linha);
CREATE INDEX IF NOT EXISTS idx_horario_pico ON transport_data(horario_pico);
CREATE INDEX IF NOT EXISTS idx_data_hora ON transport_data(data_hora);