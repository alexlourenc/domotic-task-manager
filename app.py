import streamlit as st
from src.auth import authenticate_user, create_user
from src.tasks import get_sorted_tasks
from datetime import datetime

st.set_page_config(page_title="Domotic Task Manager", layout="wide")

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
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    with tab1:
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Enter"):
                user_data = authenticate_user(user, pw)
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_data
                    st.rerun()
                else: st.error("Invalid credentials.")
    with tab2:
        with st.form("signup_form"):
            new_user = st.text_input("New Username")
            full_name = st.text_input("Full Name")
            new_pw = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                success, msg = create_user(new_user, full_name, new_pw)
                if success: st.success(msg)
                else: st.error(msg)

def show_dashboard():
    st.sidebar.write(f"User: **{st.session_state.user_info['full_name']}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.title("📋 Home Tasks")
    
    tasks = get_sorted_tasks()
    
    if not tasks:
        st.warning("No tasks found. Please add tasks in admin panel (Coming soon).")
    else:
        for task in tasks:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.subheader(task['task_name'])
                
                with col2:
                    if task['status'] == 'open':
                        st.error("🔴 OVERDUE / EM ABERTO")
                    elif task['status'] == 'in_progress':
                        st.warning(f"🟡 IN PROGRESS / POR: {task['current_user']}")
                    else:
                        st.info(f"🔵 NEXT IN: {int(max(0, task['seconds_remaining'] // 60))} min")
                
                with col3:
                    if task['status'] == 'open':
                        if st.button("Claim / Assumir", key=task['_id']):
                            # Logic to update DB will be next phase
                            pass

if __name__ == "__main__":
    main()