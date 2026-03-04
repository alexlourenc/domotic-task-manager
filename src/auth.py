import bcrypt
import streamlit as st
from datetime import datetime
from src.database import get_collection

# Function to hash a password for security
# Função para criar um hash de senha para segurança
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Function to check a password against a stored hash
# Função para verificar uma senha contra um hash armazenado
def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Function to create a new user in the system
# Função para criar um novo usuário no sistema
def create_user(username, full_name, password):
    users_collection = get_collection("usuarios")
    
    # Check if user already exists
    # Verifica se o usuário já existe
    if users_collection.find_one({"username": username}):
        return False, "User already exists! / Usuário já existe!"
    
    user_data = {
        "username": username.lower(),
        "full_name": full_name,
        "password_hash": hash_password(password),
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    users_collection.insert_one(user_data)
    return True, "User created successfully! / Usuário criado com sucesso!"

# Function to authenticate user login
# Função para autenticar o login do usuário
def authenticate_user(username, password):
    users_collection = get_collection("usuarios")
    user = users_collection.find_one({"username": username.lower()})
    
    if user and check_password(password, user["password_hash"]):
        # Update last login timestamp
        # Atualiza o carimbo de data/hora do último login
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return user
    return None