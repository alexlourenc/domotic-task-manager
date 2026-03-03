import streamlit as st
from src.auth import authenticate_user, create_user
from src.tasks import get_sorted_tasks, claim_task, complete_task, create_task, delete_task

st.set_page_config(page_title="Domotic Task Manager", layout="wide")

# Session state initialization
# Inicialização do estado de sessão
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_dashboard()

def show_login_page():
    st.title("🏠 Domotic Manager - Login")
    tab1, tab2 = st.tabs(["Login", "Sign Up / Cadastrar"])
    
    with tab1:
        with st.form("login_form"):
            user = st.text_input("Username / Usuário")
            pw = st.text_input("Password / Senha", type="password")
            if st.form_submit_button("Enter / Entrar"):
                user_data = authenticate_user(user, pw)
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_data
                    st.rerun()
                else: 
                    st.error("Invalid credentials. / Credenciais inválidas.")
                    
    with tab2:
        with st.form("signup_form"):
            new_user = st.text_input("New Username / Novo Usuário")
            full_name = st.text_input("Full Name / Nome Completo")
            new_pw = st.text_input("New Password / Nova Senha", type="password")
            if st.form_submit_button("Register / Registrar"):
                success, msg = create_user(new_user, full_name, new_pw)
                if success: st.success(msg)
                else: st.error(msg)

def show_dashboard():
    # Sidebar layout / Layout da barra lateral
    st.sidebar.write(f"User / Usuário: **{st.session_state.user_info['full_name']}**")
    if st.sidebar.button("Logout / Sair"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.title("📋 Domotic Task Manager")
    
    # Create tabs for Main Dashboard and Admin Settings
    # Criar abas para o Dashboard Principal e Configurações Admin
    tab_home, tab_admin = st.tabs(["🏠 Dashboard (Home)", "⚙️ Admin / Configurações"])
    
    with tab_home:
        # Fetch tasks from DB / Buscar tarefas do BD
        tasks = get_sorted_tasks()
        
        if not tasks:
            st.warning("No tasks found. Go to the Admin tab to create them! / Nenhuma tarefa encontrada. Vá para a aba Admin para criá-las!")
        else:
            for task in tasks:
                # Create a visual card for each task / Criar um card visual para cada tarefa
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    task_id = str(task['_id'])
                    current_username = st.session_state.user_info['username']
                    
                    with col1:
                        st.subheader(task['task_name'])
                    
                    with col2:
                        if task['status'] == 'open':
                            st.error("🔴 OVERDUE / EM ABERTO")
                        elif task['status'] == 'in_progress':
                            st.warning(f"🟡 IN PROGRESS / POR: {task['current_user'].upper()}")
                        else:
                            minutes_left = int(max(0, task.get('seconds_remaining', 0) // 60))
                            hours_left = minutes_left // 60
                            mins_remainder = minutes_left % 60
                            st.info(f"🔵 NEXT IN / PRÓXIMA EM: {hours_left}h {mins_remainder}m")
                    
                    with col3:
                        # Action Buttons Logic / Lógica dos Botões de Ação
                        if task['status'] == 'open':
                            if st.button("Claim / Assumir", key=f"claim_{task_id}"):
                                claim_task(task_id, current_username)
                                st.rerun() # Refresh page / Recarregar página
                                
                        elif task['status'] == 'in_progress':
                            # Allow completion if the user is the one who claimed it
                            # Permitir conclusão se o usuário for o que assumiu
                            if task['current_user'] == current_username:
                                if st.button("Complete / Concluir", key=f"complete_{task_id}", type="primary"):
                                    complete_task(task_id, current_username, task['interval_hours'])
                                    st.rerun() # Refresh page / Recarregar página
                            else:
                                st.button("Waiting... / Aguardando...", key=f"wait_{task_id}", disabled=True)
                                
                st.divider() # Line separator / Linha separadora

    with tab_admin:
        st.subheader("➕ Create New Routine / Cadastrar Nova Rotina")
        st.write("Defina a tarefa e de quantas em quantas horas ela deve ser refeita.")
        
        with st.form("new_task_form"):
            t_name = st.text_input("Task Name / Nome da Tarefa (ex: Lavar Louça, Trocar Areia do Gato)")
            t_interval = st.number_input("Interval (Hours) / Intervalo (Horas)", min_value=1, value=24, step=1)
            
            submit_task = st.form_submit_button("Save Routine / Salvar Rotina")
            
            if submit_task:
                if t_name.strip():
                    create_task(t_name, t_interval)
                    st.success(f"Routine '{t_name}' added successfully! / Rotina adicionada com sucesso!")
                    st.rerun()
                else:
                    st.error("Please insert a valid name. / Por favor, insira um nome válido.")
        
        st.divider()
        
        # New section to manage and delete tasks
        # Nova seção para gerenciar e excluir tarefas
        st.subheader("🗑️ Manage Existing Routines / Gerenciar Rotinas Existentes")
        
        admin_tasks = get_sorted_tasks()
        if admin_tasks:
            for t in admin_tasks:
                col_name, col_interval, col_btn = st.columns([3, 1, 1])
                t_id = str(t['_id'])
                
                with col_name:
                    st.write(f"**{t['task_name']}**")
                with col_interval:
                    st.write(f"⏱️ {t['interval_hours']}h")
                with col_btn:
                    if st.button("Delete / Excluir", key=f"del_{t_id}", type="secondary"):
                        delete_task(t_id)
                        st.rerun()
        else:
            st.info("No routines to manage. / Nenhuma rotina para gerenciar.")

if __name__ == "__main__":
    main()