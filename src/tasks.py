from datetime import datetime, timedelta
from bson.objectid import ObjectId
from src.database import get_collection
import pandas as pd

# Function to calculate the next execution time based on frequency
# Função para calcular o próximo horário de execução com base na frequência
def calculate_next_run(interval_hours):
    return datetime.utcnow() + timedelta(hours=interval_hours)

# Function to create a new predefined task
# Função para criar uma nova tarefa pré-definida
def create_task(name, interval_hours):
    tasks_col = get_collection("tasks")
    
    new_task = {
        "task_name": name,
        "interval_hours": interval_hours,
        "status": "open", # open, in_progress, finished
        "current_user": None,
        "last_finished_at": None,
        "next_run_at": datetime.utcnow(), # Starts immediately by default / Começa imediatamente por padrão
        "history": []
    }
    tasks_col.insert_one(new_task)

# Function to claim a task and set it to in progress
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

# Function to complete a task and reset the timer
# Função para concluir uma tarefa e reiniciar o cronômetro
def complete_task(task_id: str, username: str, interval_hours: int):
    tasks_col = get_collection("tasks")
    now = datetime.utcnow()
    next_run = now + timedelta(hours=interval_hours)
    
    # Create history entry
    # Criar registro de histórico
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

# Function to delete a task from the database
# Função para deletar uma tarefa do banco de dados
def delete_task(task_id: str):
    tasks_col = get_collection("tasks")
    tasks_col.delete_one({"_id": ObjectId(task_id)})

# Function to get tasks sorted by logic: Open first, then by time remaining
# Função para obter tarefas ordenadas: Abertas primeiro, depois por tempo restante
def get_sorted_tasks():
    tasks_col = get_collection("tasks")
    all_tasks = list(tasks_col.find())
    
    now = datetime.utcnow()
    
    for task in all_tasks:
        # Calculate time difference
        # Calcular diferença de tempo
        if task.get("next_run_at"):
            diff = task["next_run_at"] - now
            task["seconds_remaining"] = diff.total_seconds()
            
            # If time is up, force status to open
            # Se o tempo acabou, força o status para aberto
            if task["seconds_remaining"] <= 0 and task["status"] == "finished":
                task["status"] = "open"
                # Update DB to reflect open status automatically
                # Atualizar BD para refletir o status aberto automaticamente
                tasks_col.update_one({"_id": task["_id"]}, {"$set": {"status": "open"}})
    
    # Sorting logic / Lógica de ordenação:
    df = pd.DataFrame(all_tasks)
    if df.empty: return []
    
    # Custom sort / Ordenação personalizada
    df['sort_order'] = df['status'].map({'open': 0, 'in_progress': 1, 'finished': 2})
    df = df.sort_values(by=['sort_order', 'seconds_remaining'])
    
    return df.to_dict('records')