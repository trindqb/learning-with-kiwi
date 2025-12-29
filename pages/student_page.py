"""Trang học sinh"""
import streamlit as st
from components import UserHeader, StudentExamForm, ResultView

def student_page():
    st.title("✍️ KHU VỰC THI HỌC SINH")
    user = st.session_state['user']
    UserHeader.render(user)
    
    tab1, tab2 = st.tabs(["📝 Làm Bài", "📊 Kết Quả"])
    
    with tab1:
        StudentExamForm.render(user)
    with tab2:
        ResultView.render(user)
