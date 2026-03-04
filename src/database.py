import streamlit as st
from pymongo import MongoClient
import sys

# Function to initialize connection to MongoDB Atlas
# Função para inicializar a conexão com o MongoDB Atlas
@st.cache_resource
def init_connection():
    try:
        # Pull URI from streamlit secrets
        # Puxa a URI dos segredos do streamlit
        uri = st.secrets["mongo"]["uri"]
        client = MongoClient(uri)
        
        # Test connection
        # Testar a conexão
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {e}")
        # Erro ao conectar ao MongoDB
        sys.exit(1)

# Function to get the specific database
# Função para obter o banco de dados específico
def get_database():
    client = init_connection()
    db_name = st.secrets["mongo"]["db_name"]
    return client[db_name]

# Helper to get collections
# Auxiliar para obter coleções
def get_collection(collection_name):
    db = get_database()
    return db[collection_name]