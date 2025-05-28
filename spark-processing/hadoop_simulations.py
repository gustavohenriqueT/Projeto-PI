import pandas as pd
import sqlite3
import os

# Caminho para o arquivo de dados processado pelo R, acessível dentro do contêiner
CSV_PATH_INPUT = '/data/transport_dataL.csv' 
# Caminho para salvar a saída da simulação Sqoop/HDFS, no volume compartilhado
OUTPUT_HDFS_SIM_PATH = '/data/simulated_hdfs_output.csv'

print(f"Iniciando simulações Hadoop com o arquivo: {CSV_PATH_INPUT}")

try:
    if not os.path.exists(CSV_PATH_INPUT):
        print(f"ERRO: Arquivo de entrada não encontrado em {CSV_PATH_INPUT}. Verifique se o r-processing foi concluído.")
        exit(1)
    
    df = pd.read_csv(CSV_PATH_INPUT)
    print(f"Arquivo CSV '{CSV_PATH_INPUT}' carregado com sucesso. Shape: {df.shape}")

    # Garantir que as colunas esperadas existem (nomes em minúsculo após processamento R)
    # Colunas usadas nas simulações do notebook original: Situacao, ID_Veiculo, Tempo_Viagem_Minutos, Horario_Pico, Numero_Passageiros
    # No seu transport_dataL.csv, os nomes são: situacao, id_veiculo, tempo_viagem_minutos, horario_pico, numero_passageiros, linha, data_hora, latitude, longitude, hora
    expected_cols_for_simulations = ['situacao', 'id_veiculo', 'tempo_viagem_minutos', 'horario_pico', 'numero_passageiros', 'linha', 'hora']
    
    actual_cols = df.columns.tolist()
    print(f"Colunas disponíveis no CSV carregado: {actual_cols}")

    missing_cols_in_df = [col for col in expected_cols_for_simulations if col not in actual_cols]
    if missing_cols_in_df:
        print(f"AVISO: As seguintes colunas esperadas para simulações Hadoop não foram encontradas no CSV: {missing_cols_in_df}. Algumas simulações podem falhar ou ser imprecisas.")

except FileNotFoundError:
    print(f"ERRO CRÍTICO: Arquivo de entrada '{CSV_PATH_INPUT}' não encontrado. O script não pode continuar.")
    exit(1)
except Exception as e:
    print(f"ERRO ao carregar ou verificar o arquivo CSV inicial: {e}")
    exit(1)

# --- MapReduce: contar ocorrências de 'situacao' ---
print("\n--- Iniciando Simulação MapReduce (Contagem de 'situacao') ---")
def mapper_situacao(linhas_situacao):
    pares = []
    if linhas_situacao is None:
        return pares
    for situacao_val in linhas_situacao:
        if pd.notna(situacao_val):
            situacao_limpa = str(situacao_val).strip()
            if situacao_limpa: 
                 pares.append((situacao_limpa, 1))
    return pares 

def shuffle_data(mapped_data):
    agrupado = {}
    if mapped_data is None:
        return agrupado
    for chave, valor in mapped_data:
        if chave not in agrupado:
            agrupado[chave] = []
        agrupado[chave].append(valor)
    return agrupado

def reducer_sum(agrupado):
    if agrupado is None:
        return {}
    return {chave: sum(valores) for chave, valores in agrupado.items()}

if 'situacao' in df.columns:
    mapeado_situacao = mapper_situacao(df["situacao"])
    if mapeado_situacao: 
        agrupado_situacao = shuffle_data(mapeado_situacao)
        resultado_mapreduce = reducer_sum(agrupado_situacao)
        print("Resultado MapReduce (Contagem de 'situacao'):")
        for situacao, contagem in resultado_mapreduce.items():
            print(f"  {situacao}: {contagem}")
    else:
        print("AVISO: Mapper não produziu dados para MapReduce (coluna 'situacao' pode estar vazia ou toda NaN).")
else:
    print("AVISO: Coluna 'situacao' não encontrada para a simulação MapReduce.")


# --- Simulação HIVE: SQL com Pandas ---
print("\n--- Iniciando Simulação HIVE (Consultas com Pandas) ---")
if 'id_veiculo' in df.columns and 'tempo_viagem_minutos' in df.columns and 'horario_pico' in df.columns:
    df_hive_sim = df[["id_veiculo", "tempo_viagem_minutos", "horario_pico"]]
    print("Simulação HIVE: Viagens FORA do horário de pico (horario_pico == 0 ou False):")
    # horario_pico é boolean (True/False) ou int (1/0) no CSV processado pelo R
    # A query com 0 funciona para ambos os casos se for int. Se for bool, usar 'horario_pico == False'
    try:
        # Tenta primeiro como numérico/booleano que pode ser comparado com 0
        print(df_hive_sim.query("horario_pico == 0").head())
    except pd.errors.UndefinedVariableError:
         # Se 'horario_pico' não puder ser diretamente usado em query (raro para colunas simples)
         # ou se a comparação com 0 falhar devido ao tipo, tente com False
        print(df_hive_sim[df_hive_sim['horario_pico'] == False].head())
    except Exception as e_hive:
        print(f"Erro na simulação HIVE: {e_hive}")

else:
    print("AVISO: Colunas 'id_veiculo', 'tempo_viagem_minutos' ou 'horario_pico' não encontradas para simulação HIVE.")


# --- Simulação PIG: transformações ---
print("\n--- Iniciando Simulação PIG (Transformações com Pandas) ---")
if 'numero_passageiros' in df.columns and 'tempo_viagem_minutos' in df.columns and 'horario_pico' in df.columns:
    dados_pig_source = df[["numero_passageiros", "tempo_viagem_minutos", "horario_pico"]].dropna().head(100)
    
    if not dados_pig_source.empty:
        dados_pig_list = dados_pig_source.values.tolist()
        # Filtrar por horario_pico == 1 (True)
        filtrado_pig = [x for x in dados_pig_list if x[2] == 1 or x[2] is True]

        transformado_pig = []
        for x in filtrado_pig:
            try:
                num_pass = int(x[0])
                tempo_viagem = int(x[1])
                indice_transito = num_pass * tempo_viagem 
                transformado_pig.append((num_pass, tempo_viagem, indice_transito))
            except (ValueError, TypeError): # Captura TypeError se x[0] ou x[1] for None, etc.
                print(f"AVISO (PIG): Não foi possível converter valor para int ou realizar operação na linha: {x}")
                continue
        
        print("Simulação PIG: Nível de Trânsito (Numero_Passageiros * Tempo_Viagem_Minutos para Horario_Pico == 1)")
        print("Passageiros | Tempo Viagem | Índice Calculado")
        for num, tempo, indice in transformado_pig[:10]: 
            print(f"{num:<11} | {tempo:<12.1f} | {indice:<.2f}")
    else:
        print("AVISO (PIG): DataFrame de origem para PIG estava vazio após dropna/head.")
else:
    print("AVISO: Colunas 'numero_passageiros', 'tempo_viagem_minutos' ou 'horario_pico' não encontradas para simulação PIG.")

# --- Simulação HBase: banco NoSQL orientado a colunas ---
print("\n--- Iniciando Simulação HBase (Dicionário Python) ---")
# Usando as mesmas colunas da simulação PIG como exemplo
if 'numero_passageiros' in df.columns and 'tempo_viagem_minutos' in df.columns and 'horario_pico' in df.columns:
    hbase_sim = {}
    # iterrows() pode ser lento para DataFrames grandes, mas para simulação/amostra é ok.
    df_hbase_sample = df[['numero_passageiros', 'tempo_viagem_minutos', 'horario_pico']].dropna().head(100)

    for i, row in df_hbase_sample.iterrows(): 
        try:
            # Chave única com base no índice original do DataFrame (se disponível e útil) ou um novo índice
            # Usando o índice do df_hbase_sample que é de 0 a N-1 para a amostra
            row_key = f"viagem_info:{i}" 
            hbase_sim[row_key] = {
                "info:n_passageiros": int(row["numero_passageiros"]),
                "info:tempo_min": int(row["tempo_viagem_minutos"]),
                "info:pico": bool(row["horario_pico"]) 
            }
        except (ValueError, TypeError):
            print(f"AVISO (HBase): Não foi possível converter valor para int/bool na linha com índice de amostra: {i}, dados: {row.to_dict()}")
            continue

    print("Simulação HBase: Amostra dos 5 primeiros registros:")
    count = 0
    for chave, colunas in hbase_sim.items():
        print(f"{chave} => {colunas}")
        count += 1
        if count >= 5:
            break
    if count == 0:
        print("Nenhum dado processado para a simulação HBase (possivelmente devido a NaNs ou erros de conversão).")
else:
    print("AVISO: Colunas 'numero_passageiros', 'tempo_viagem_minutos' ou 'horario_pico' não encontradas para simulação HBase.")


# --- Simulação Sqoop: transferir dados para "HDFS" (um arquivo CSV) ---
print("\n--- Iniciando Simulação Sqoop (SQLite para CSV) ---")
if 'numero_passageiros' in df.columns and 'tempo_viagem_minutos' in df.columns and 'horario_pico' in df.columns:
    conn_sqlite_sim = sqlite3.connect(':memory:') 
    
    # Seleciona algumas colunas e remove NaNs antes de enviar para o "banco relacional"
    df_for_sqoop = df[["numero_passageiros", "tempo_viagem_minutos", "horario_pico"]].dropna()

    if not df_for_sqoop.empty:
        try:
            df_for_sqoop.to_sql('dados_origem_simulados', conn_sqlite_sim, if_exists='replace', index=False)
            
            df_from_sql_sim = pd.read_sql('SELECT * FROM dados_origem_simulados', conn_sqlite_sim)
            df_from_sql_sim.to_csv(OUTPUT_HDFS_SIM_PATH, index=False)
            
            print(f"Simulação Sqoop: Dados exportados para '{OUTPUT_HDFS_SIM_PATH}'")
            
            # Opcional: Ler de volta para verificar
            # df_hdfs_check = pd.read_csv(OUTPUT_HDFS_SIM_PATH)
            # print("Conteúdo do arquivo HDFS simulado (primeiras linhas):")
            # print(df_hdfs_check.head())
        except Exception as e_sqoop:
            print(f"Erro durante a simulação Sqoop: {e_sqoop}")
        finally:
            conn_sqlite_sim.close()
    else:
        print("AVISO (Sqoop): DataFrame de origem para Sqoop estava vazio após dropna.")
else:
    print("AVISO: Colunas 'numero_passageiros', 'tempo_viagem_minutos' ou 'horario_pico' não encontradas para simulação Sqoop.")

print("\n--- Simulações Hadoop concluídas ---")