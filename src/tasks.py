from datetime import datetime, timedelta
from bson.objectid import ObjectId
from src.database import get_collection
from src.notifications import send_telegram_alert
import pandas as pd

def calculate_next_run(interval_hours):
    return datetime.utcnow() + timedelta(hours=interval_hours)

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

def claim_task(task_id: str, username: str):
    tasks_col = get_collection("tasks")
    tasks_col.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "status": "in_progress",
            "current_user": username
        }}
    )

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

def delete_task(task_id: str):
    tasks_col = get_collection("tasks")
    tasks_col.delete_one({"_id": ObjectId(task_id)})

def get_sorted_tasks():
    tasks_col = get_collection("tasks")
    all_tasks = list(tasks_col.find())
    now = datetime.utcnow()
    
    for task in all_tasks:
        if task.get("next_run_at"):
            diff = task["next_run_at"] - now
            task["seconds_remaining"] = diff.total_seconds()
            
            if task["seconds_remaining"] <= 0 and task["status"] == "finished":
                task["status"] = "open"
                tasks_col.update_one({"_id": task["_id"]}, {"$set": {"status": "open"}})
                
                msg = f"🚨 *TAREFA VENCIDA!* 🚨\n\nA rotina *{task['task_name']}* está em aberto e aguardando alguém assumir!"
                send_telegram_alert(msg)
    
    df = pd.DataFrame(all_tasks)
    if df.empty: return []
    
    df['sort_order'] = df['status'].map({'open': 0, 'in_progress': 1, 'finished': 2})
    df = df.sort_values(by=['sort_order', 'seconds_remaining'])
    return df.to_dict('records')

def get_task_history():
    tasks_col = get_collection("tasks")
    all_tasks = list(tasks_col.find({"history": {"$exists": True, "$ne": []}}))
    
    history_list = []
    for task in all_tasks:
        task_name = task["task_name"]
        for entry in task.get("history", []):
            history_list.append({
                "Tarefa": task_name,
                "Morador": entry["user"],
                "Data/Hora (UTC)": entry["completed_at"]
            })
            
    if not history_list:
        return pd.DataFrame()
        
    df = pd.DataFrame(history_list)
    df["Data/Hora"] = pd.to_datetime(df["Data/Hora (UTC)"]) - pd.Timedelta(hours=3)
    df = df.sort_values(by="Data/Hora", ascending=False)
    df["Data/Hora"] = df["Data/Hora"].dt.strftime('%d/%m/%Y %H:%M')
    return df[["Tarefa", "Morador", "Data/Hora"]]

# NOVA FUNÇÃO: Atualizar o nome e o intervalo de uma tarefa existente
def update_task(task_id: str, new_name: str, new_interval: int):
    tasks_col = get_collection("tasks")
    tasks_col.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "task_name": new_name,
            "interval_hours": new_interval
        }}
    )