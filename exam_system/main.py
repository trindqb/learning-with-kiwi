"""
Entry point - File chạy chính
"""
import streamlit as st
from config import init_firebase
from pages import teacher_page, student_page

# Khởi tạo
init_firebase()
st.set_page_config(
    page_title="Hệ Thống Thi Trực Tuyến",
    layout="wide",
    page_icon="🏫"
)

# Router
role = st.sidebar.radio("Vai trò:", ["Học sinh", "Giáo viên"])

if role == "Giáo viên":
    teacher_page()
else:
    student_page()