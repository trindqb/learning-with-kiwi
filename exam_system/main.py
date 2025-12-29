"""
Entry point - File chạy chính
"""
import sys
from pathlib import Path

import streamlit as st
from config import init_firebase
from components.common.login import LoginForm

# Add parent directory to path to import pages module
sys.path.insert(0, str(Path(__file__).parent.parent))
from pages import teacher_page, student_page

# Khởi tạo
init_firebase()
st.set_page_config(
    page_title="Hệ Thống Thi Trực Tuyến",
    layout="wide",
    page_icon="🏫"
)

# Initialize session state
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

# Check if user is logged in
is_teacher_logged_in = st.session_state.get('teacher_authenticated', False)
is_student_logged_in = st.session_state.get('student_info') is not None

# Router logic
if is_teacher_logged_in:
    teacher_page()
elif is_student_logged_in:
    student_page()
else:
    LoginForm.render()