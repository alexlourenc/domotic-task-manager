from datetime import datetime, timedelta
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

# Function to get tasks sorted by logic: Open first, then by time remaining
# Função para obter tarefas ordenadas: Abertas primeiro, depois por tempo restante
def get_sorted_tasks():
    tasks_col = get_collection("tasks")
    all_tasks = list(tasks_col.find())
    
    now = datetime.utcnow()
    
    for task in all_tasks:
        # Calculate time difference
        # Calcular diferença de tempo
        if task["next_run_at"]:
            diff = task["next_run_at"] - now
            task["seconds_remaining"] = diff.total_seconds()
            
            # If time is up, force status to open
            # Se o tempo acabou, força o status para aberto
            if task["seconds_remaining"] <= 0 and task["status"] == "finished":
                task["status"] = "open"
    
    # Sorting logic / Lógica de ordenação:
    # 1. Open tasks at top / Tarefas abertas no topo
    # 2. In progress / Em andamento
    # 3. Time remaining for others / Tempo restante para as demais
    df = pd.DataFrame(all_tasks)
    if df.empty: return []
    
    # Custom sort / Ordenação personalizada
    df['sort_order'] = df['status'].map({'open': 0, 'in_progress': 1, 'finished': 2})
    df = df.sort_values(by=['sort_order', 'seconds_remaining'])
    
    return df.to_dict('records')