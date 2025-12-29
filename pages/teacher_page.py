"""Trang giáo viên"""
import streamlit as st
from components import (
    UserHeader,
    QuestionCreationForm,
    QuestionEditForm,
    GradingInterface,
    UserManagementPanel
)

def teacher_page():
    st.title("👩‍🏫 QUẢN LÝ GIÁO VIÊN")
    user = st.session_state['user']
    UserHeader.render(user)
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Tạo Câu Hỏi",
        "✏️ Sửa Câu Hỏi", 
        "💯 Chấm Bài",
        "👥 Quản Lý"
    ])
    
    with tab1:
        QuestionCreationForm.render()
    with tab2:
        QuestionEditForm.render()
    with tab3:
        GradingInterface.render()
    with tab4:
        UserManagementPanel.render()
