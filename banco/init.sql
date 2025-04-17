-- Cria tabela para armazenar os dados processados
CREATE TABLE IF NOT EXISTS dados_transporte (
    data_hora TIMESTAMP,
    id_veiculo VARCHAR(50),
    linha VARCHAR(50),
    latitude FLOAT,
    longitude FLOAT,
    passageiros INTEGER,
    tempo_viagem INTEGER,
    horario_pico BOOLEAN,
    situacao VARCHAR(10)
);