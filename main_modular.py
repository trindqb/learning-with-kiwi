"""
HỆ THỐNG THI TRỰC TUYẾN - MODULAR VERSION
"""
import streamlit as st
from config import init_firebase
from auth import check_session
from components import LoginForm
from pages import teacher_page, student_page

# Init
init_firebase()
st.set_page_config(
    page_title="Hệ Thống Thi Trực Tuyến",
    layout="wide",
    page_icon="🏫"
)

# Router
if not check_session():
    LoginForm.render()
else:
    user = st.session_state['user']
    
    if user['role'] == 'teacher':
        teacher_page()
    elif user['role'] == 'student':
        student_page()
    else:
        st.error("⚠️ Role không hợp lệ!")
