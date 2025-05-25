import pandas as pd
import numpy as np
import re
import nltk
import matplotlib.pyplot as plt
import seaborn as sns

from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    classification_report
)

# --- Carregar dataset ---
df = pd.read_csv('/app/data/transport_dataL.csv')
# print(df.head())

# --- Pré-processamento texto ---

nltk.download('stopwords')
nltk.download('rslp')
stop_words = set(stopwords.words('portuguese'))
stemmer = RSLPStemmer()

def preprocess_text(text):
    # Permite letras, acentos, e espaços, remove outros caracteres
    text = re.sub(r'[^a-zA-ZáéíóúãõâêîôûçÁÉÍÓÚÃÕÂÊÎÔÛÇ\s]', '', str(text))
    text = text.lower()
    # Remove stopwords
    text = ' '.join(word for word in text.split() if word not in stop_words)
    # Aplica stemmer
    text = ' '.join(stemmer.stem(word) for word in text.split())
    return text

# --- Criar coluna texto concatenando colunas relevantes ---

colunas_texto = [
    'Data_Hora', 'ID_Veiculo', 'Linha', 'Latitude',
    'Longitude', 'Numero_Passageiros', 'Tempo_Viagem_Minutos', 'Hora'
]

df['texto'] = df[colunas_texto].astype(str).agg(' '.join, axis=1)
df['rótulo'] = df['Situacao'].astype(str)

# Aplicar pré-processamento
df['texto'] = df['texto'].apply(preprocess_text)

# print(df[['texto', 'rótulo']].head())

# --- Dividir dados para classificação NLP ---

x_train, x_test, y_train, y_test = train_test_split(
    df['texto'], df['rótulo'],
    test_size=0.2, random_state=42, stratify=df['rótulo']
)

# --- Pipeline NLP: TF-IDF + RandomForest ---

pipeline_nlp = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_df=1.0, min_df=1)),
    ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
])

# Treina o modelo
pipeline_nlp.fit(x_train, y_train)

# Previsões e métricas
y_pred = pipeline_nlp.predict(x_test)

print("Acurácia NLP:", accuracy_score(y_test, y_pred))
print("Relatório de Classificação NLP:\n", classification_report(y_test, y_pred, zero_division=1))

# --- Gerar dados aleatórios embaralhando colunas (para simular novas entradas) ---

def embaralhar_coluna(col):
    return col.sample(frac=1).reset_index(drop=True)

df_random = pd.DataFrame({
    col: embaralhar_coluna(df[col]) for col in colunas_texto
})
df_random['rótulo'] = embaralhar_coluna(df['Situacao'].astype(str))

df_random['texto'] = df_random[colunas_texto].astype(str).agg(' '.join, axis=1)
df_random['texto'] = df_random['texto'].apply(preprocess_text)

# print(df_random[['texto', 'rótulo']].head())

# Prever no pipeline NLP usando os dados aleatórios
predicoes_random = pipeline_nlp.predict(df_random['texto'])
print("Previsões em dados embaralhados (NLP):", predicoes_random)

# --- Classificação com dados estruturados (RandomForest) ---

# Adicionar ruído na coluna alvo para simular variações
df['Tempo_Viagem_Minutos'] += np.random.normal(0, 10, size=len(df))

# Embaralhar 10% dos rótulos 'Horario_Pico' para simular erros
mask = np.random.rand(len(df)) < 0.1
df.loc[mask, 'Horario_Pico'] = np.random.permutation(df.loc[mask, 'Horario_Pico'])

# Selecionar features e target
X = df.drop(columns=['Horario_Pico', 'Hora', 'ID_Veiculo', 'Linha', 'Data_Hora', 'texto', 'rótulo', 'Situacao'], errors='ignore')
y = df['Horario_Pico']

numeric_features = X.select_dtypes(include=['int64', 'float64']).columns
categorical_features = X.select_dtypes(include=['object', 'category']).columns

numeric_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor_classif = ColumnTransformer([
    ('num', numeric_transformer, numeric_features),
    ('cat', categorical_transformer, categorical_features)
])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model_rf = RandomForestClassifier(n_estimators=100, random_state=42)

pipeline_classif = Pipeline([
    ('preprocessor', preprocessor_classif),
    ('classifier', model_rf)
])

pipeline_classif.fit(X_train, y_train)
y_pred_classif = pipeline_classif.predict(X_test)

print("Acurácia Classificação Estruturada:", accuracy_score(y_test, y_pred_classif))
print("Relatório Classificação Estruturada:\n", classification_report(y_test, y_pred_classif, zero_division=1))