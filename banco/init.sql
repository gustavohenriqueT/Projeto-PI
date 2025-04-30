-- Cria tabela para armazenar os dados processados
CREATE TABLE IF NOT EXISTS dados_transporte (
    Data_Hora DATETIME),
    ID_Veiculo VARCHAR(50),
    Linha VARCHAR(50),
    Latitude DECIMAL(10, 6),
    Longitude DECIMAL(10, 6),
    Numero_Passageiros INT,
    Tempo_Viagem_Minutos INT,
    Dado_Correto BOOLEAN,
    Hora INT,
    Horario_Pico INT,
    Situacao VARCHAR(10)