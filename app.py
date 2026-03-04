import streamlit as st
from src.auth import authenticate_user, create_user, get_all_users, update_user_password, delete_user
from src.tasks import get_sorted_tasks, claim_task, complete_task, create_task, delete_task, get_task_history, update_task

st.set_page_config(page_title="Gerenciador de Tarefas Domésticas", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_dashboard()

def show_login_page():
    st.title("🏠 Gerenciador Doméstico")
    st.subheader("Acesso Restrito")
    
    with st.form("login_form"):
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            user_data = authenticate_user(user, pw)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_info = user_data
                st.rerun()
            else: 
                st.error("Credenciais inválidas ou usuário inexistente.")

def show_dashboard():
    is_admin = st.session_state.user_info.get('role', 'user') == 'admin'
    perfil_nome = "Administrador" if is_admin else "Usuário Padrão"
    
    st.sidebar.write(f"Olá, **{st.session_state.user_info['full_name']}**")
    st.sidebar.caption(f"Perfil: {perfil_nome}")
    st.sidebar.divider()
    
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.title("📋 Gerenciador de Tarefas Domésticas")
    
    if is_admin:
        tabs = st.tabs(["🏠 Dashboard (Home)", "📊 Histórico", "⚙️ Configurações (Admin)"])
        tab_home, tab_hist, tab_admin = tabs[0], tabs[1], tabs[2]
    else:
        tabs = st.tabs(["🏠 Dashboard (Home)", "📊 Histórico"])
        tab_home, tab_hist = tabs[0], tabs[1]
        tab_admin = None 
    
    with tab_home:
        tasks = get_sorted_tasks()
        if not tasks:
            st.warning("Nenhuma tarefa cadastrada no momento.")
        else:
            for task in tasks:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    task_id = str(task['_id'])
                    current_username = st.session_state.user_info['username']
                    
                    with col1:
                        st.subheader(task['task_name'])
                    with col2:
                        if task['status'] == 'open':
                            st.error("🔴 EM ABERTO")
                        elif task['status'] == 'in_progress':
                            st.warning(f"🟡 EM ANDAMENTO POR: {task['current_user'].upper()}")
                        else:
                            minutes_left = int(max(0, task.get('seconds_remaining', 0) // 60))
                            hours_left = minutes_left // 60
                            mins_remainder = minutes_left % 60
                            st.info(f"🔵 PRÓXIMA EM: {hours_left}h {mins_remainder}m")
                    with col3:
                        if task['status'] == 'open':
                            if st.button("Assumir", key=f"claim_{task_id}"):
                                claim_task(task_id, current_username)
                                st.rerun()
                        
                        btn_text = "Concluir"
                        if task['status'] == 'finished':
                            btn_text = "Refazer Agora"
                        elif task['status'] == 'open':
                            btn_text = "Concluir Direto"
                            
                        if st.button(btn_text, key=f"complete_{task_id}", type="primary"):
                            complete_task(task_id, current_username, task['interval_hours'])
                            st.rerun()
                st.divider()

    with tab_hist:
        st.subheader("📜 Histórico de Conclusões")
        df_hist = get_task_history()
        if df_hist.empty:
            st.info("Ninguém concluiu nenhuma tarefa ainda.")
        else:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("🏆 Ranking de Moradores")
            ranking = df_hist['Morador'].value_counts().reset_index()
            ranking.columns = ['Morador', 'Total de Tarefas']
            st.bar_chart(data=ranking, x='Morador', y='Total de Tarefas')

    if tab_admin is not None:
        with tab_admin:
            # 1. BLOCO DE CRIAÇÃO
            st.subheader("➕ Cadastrar Nova Rotina")
            with st.form("new_task_form"):
                t_name = st.text_input("Nome da Tarefa")
                t_interval = st.number_input("Intervalo (Horas)", min_value=1, value=24, step=1)
                submit_task = st.form_submit_button("Salvar Rotina")
                if submit_task:
                    if t_name.strip():
                        create_task(t_name, t_interval)
                        st.success(f"Rotina adicionada!")
                        st.rerun()
                    else:
                        st.error("Insira um nome válido.")
            
            st.divider()

            # 2. NOVO BLOCO: EDITAR ROTINAS
            st.subheader("✏️ Editar Rotina Existente")
            admin_tasks = get_sorted_tasks()
            if admin_tasks:
                task_dict = {str(t['_id']): t for t in admin_tasks}
                
                # Seleciona a tarefa fora do formulário para carregar os dados dinamicamente
                selected_task_id = st.selectbox(
                    "Selecione a Rotina para alterar:", 
                    options=list(task_dict.keys()), 
                    format_func=lambda x: task_dict[x]['task_name']
                )
                
                selected_task = task_dict[selected_task_id]
                
                with st.form("edit_task_form"):
                    new_name = st.text_input("Nome da Tarefa", value=selected_task['task_name'])
                    new_interval = st.number_input("Intervalo (Horas)", min_value=1, value=int(selected_task['interval_hours']), step=1)
                    
                    if st.form_submit_button("Salvar Alterações"):
                        if new_name.strip():
                            update_task(selected_task_id, new_name, new_interval)
                            st.success("Rotina atualizada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Insira um nome válido.")
            else:
                st.info("Cadastre uma rotina primeiro para poder editá-la.")
            
            st.divider()
            
            # 3. BLOCO DE EXCLUSÃO DE ROTINAS
            st.subheader("🗑️ Remover Rotinas")
            if admin_tasks:
                for t in admin_tasks:
                    col_name, col_interval, col_btn = st.columns([3, 1, 1])
                    t_id = str(t['_id'])
                    with col_name: st.write(f"**{t['task_name']}**")
                    with col_interval: st.write(f"⏱️ {t['interval_hours']}h")
                    with col_btn:
                        if st.button("Excluir", key=f"del_{t_id}", type="secondary"):
                            delete_task(t_id)
                            st.rerun()
            else:
                st.info("Nenhuma rotina para excluir.")

            st.divider()
            
            # 4. BLOCOS DE USUÁRIOS
            st.subheader("👤 Cadastrar Novo Morador")
            with st.form("admin_signup_form"):
                new_user = st.text_input("Usuário de Login")
                full_name = st.text_input("Nome Completo")
                new_pw = st.text_input("Senha Padrão", type="password")
                new_role = st.selectbox("Perfil de Acesso", ["user", "admin"], format_func=lambda x: "Usuário Padrão" if x == "user" else "Administrador")
                
                if st.form_submit_button("Cadastrar Morador"):
                    if new_user and full_name and new_pw:
                        success, msg = create_user(new_user, full_name, new_pw, new_role)
                        if success: 
                            st.success(msg)
                            st.rerun()
                        else: st.error(msg)
                    else: st.error("Preencha todos os campos!")
                        
            st.divider()

            st.subheader("🗑️ Remover Moradores")
            all_users = get_all_users()
            for u in all_users:
                col_u_name, col_u_role, col_u_btn = st.columns([3, 1, 1])
                u_name = u['username']
                with col_u_name: st.write(f"**{u['full_name']}** (@{u_name})")
                with col_u_role: st.write(f"{u.get('role', 'user').upper()}")
                with col_u_btn:
                    if u_name == st.session_state.user_info['username']:
                        st.button("Sua Conta", key=f"del_u_{u_name}", disabled=True)
                    else:
                        if st.button("Excluir", key=f"del_u_{u_name}", type="secondary"):
                            delete_user(u_name)
                            st.rerun()

            st.divider()

            st.subheader("🔑 Alterar Senhas de Moradores")
            user_dict = {u['username']: f"{u['full_name']} ({u.get('role', 'user').upper()})" for u in all_users}
            with st.form("change_pw_form"):
                selected_u = st.selectbox("Selecione o Usuário", options=list(user_dict.keys()), format_func=lambda x: user_dict[x])
                new_pw_update = st.text_input("Nova Senha", type="password")
                if st.form_submit_button("Atualizar Senha"):
                    if new_pw_update.strip():
                        update_user_password(selected_u, new_pw_update)
                        st.success(f"Senha atualizada!")
                    else: st.error("A senha não pode estar vazia.")

if __name__ == "__main__":
    main()