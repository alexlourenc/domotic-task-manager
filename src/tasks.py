from datetime import datetime, timedelta
from bson.objectid import ObjectId
from src.database import get_collection
from src.notifications import send_telegram_alert
import pandas as pd

# Função para calcular o próximo horário de execução com base na frequência
def calculate_next_run(interval_hours):
    return datetime.utcnow() + timedelta(hours=interval_hours)

# Função para criar uma nova tarefa pré-definida
def create_task(name, interval_hours):
    tasks_col = get_collection("tasks")
    
    new_task = {
        "task_name": name,
        "interval_hours": interval_hours,
        "status": "open", 
        "current_user": None,
        "last_finished_at": None,
        "next_run_at": datetime.utcnow(), 
        "history": []
    }
    tasks_col.insert_one(new_task)

# Função para assumir uma tarefa e colocá-la em andamento
def claim_task(task_id: str, username: str):
    tasks_col = get_collection("tasks")
    tasks_col.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "status": "in_progress",
            "current_user": username
        }}
    )

# Função para concluir uma tarefa e reiniciar o cronômetro
def complete_task(task_id: str, username: str, interval_hours: int):
    tasks_col = get_collection("tasks")
    now = datetime.utcnow()
    next_run = now + timedelta(hours=interval_hours)
    
    history_entry = {
        "user": username,
        "completed_at": now
    }
    
    tasks_col.update_one(
        {"_id": ObjectId(task_id)},
        {
            "$set": {
                "status": "finished",
                "current_user": None,
                "last_finished_at": now,
                "next_run_at": next_run
            },
            "$push": {
                "history": history_entry
            }
        }
    )

# Função para deletar uma tarefa
def delete_task(task_id: str):
    tasks_col = get_collection("tasks")
    tasks_col.delete_one({"_id": ObjectId(task_id)})

# Função para obter tarefas ordenadas: Abertas primeiro, depois por tempo restante
def get_sorted_tasks():
    tasks_col = get_collection("tasks")
    all_tasks = list(tasks_col.find())
    
    now = datetime.utcnow()
    
    for task in all_tasks:
        if task.get("next_run_at"):
            diff = task["next_run_at"] - now
            task["seconds_remaining"] = diff.total_seconds()
            
            # Se o tempo acabou, força o status para aberto
            if task["seconds_remaining"] <= 0 and task["status"] == "finished":
                task["status"] = "open"
                tasks_col.update_one({"_id": task["_id"]}, {"$set": {"status": "open"}})
                
                # Gatilho do Telegram
                msg = f"🚨 *TAREFA VENCIDA!* 🚨\n\nA rotina *{task['task_name']}* está em aberto e aguardando alguém assumir!"
                send_telegram_alert(msg)
    
    df = pd.DataFrame(all_tasks)
    if df.empty: return []
    
    df['sort_order'] = df['status'].map({'open': 0, 'in_progress': 1, 'finished': 2})
    df = df.sort_values(by=['sort_order', 'seconds_remaining'])
    
    return df.to_dict('records')