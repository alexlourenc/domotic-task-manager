import requests
import streamlit as st

# Função para enviar uma mensagem no Telegram
def send_telegram_alert(message: str):
    try:
        # Carregar segredos
        bot_token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        
        # Checagem de segurança
        if bot_token == "YOUR_BOT_TOKEN_HERE" or not bot_token:
            print("Telegram não configurado.")
            return False
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown" # Permite negrito e itálico
        }
        
        # Enviar requisição POST para a API do Telegram
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return True
        else:
            print(f"Falha ao enviar alerta: {response.text}")
            return False
            
    except Exception as e:
        print(f"Erro ao enviar alerta no Telegram: {e}")
        return False