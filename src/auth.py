import bcrypt
import streamlit as st
from datetime import datetime
from src.database import get_collection

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(username, full_name, password, role="user"):
    users_collection = get_collection("usuarios")
    
    if users_collection.find_one({"username": username.lower()}):
        return False, "Usuário já existe!"
    
    if users_collection.count_documents({}) == 0:
        role = "admin"
    
    user_data = {
        "username": username.lower(),
        "full_name": full_name,
        "password_hash": hash_password(password),
        "role": role,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    users_collection.insert_one(user_data)
    return True, f"Usuário criado com sucesso! Perfil: {role.upper()}"

def authenticate_user(username, password):
    users_collection = get_collection("usuarios")
    user = users_collection.find_one({"username": username.lower()})
    
    if user and check_password(password, user["password_hash"]):
        if "role" not in user:
            users_collection.update_one({"_id": user["_id"]}, {"$set": {"role": "admin"}})
            user["role"] = "admin"
            
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return user
    return None

def update_user_password(username, new_password):
    users_collection = get_collection("usuarios")
    users_collection.update_one(
        {"username": username.lower()},
        {"$set": {"password_hash": hash_password(new_password)}}
    )

def get_all_users():
    users_collection = get_collection("usuarios")
    return list(users_collection.find({}, {"password_hash": 0}))

def delete_user(username: str):
    users_collection = get_collection("usuarios")
    users_collection.delete_one({"username": username.lower()})