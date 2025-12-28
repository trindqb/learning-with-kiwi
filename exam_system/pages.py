import streamlit as st
from auth import AuthManager
from config import get_db
from models import QuestionRepository, SubmissionRepository
from components import (
    TeacherLoginForm,
    QuestionCreationForm,
    QuestionEditForm,
    GradingInterface,
    StudentExamForm
)

def teacher_page():
    """Trang giáo viên"""
    auth = AuthManager()
    
    if not auth.check_teacher_session():
        TeacherLoginForm.render()
        return
    
    st.title("👩‍🏫 QUẢN LÝ GIÁO VIÊN")
    
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🚪 Đăng xuất"):
            auth.logout_teacher()
            st.rerun()
    
    tab1, tab2, tab3 = st.tabs([
        "➕ Tạo Câu Hỏi",
        "✏️ Sửa Câu Hỏi",
        "💯 Chấm Bài"
    ])
    
    db = get_db()
    
    with tab1:
        QuestionCreationForm.render(db)
    
    with tab2:
        QuestionEditForm.render(db)
    
    with tab3:
        GradingInterface.render(db)


def student_page():
    """Trang học sinh"""
    st.title("✍️ KHU VỰC THI HỌC SINH")
    
    auth = AuthManager()
    db = get_db()
    
    if 'student_info' not in st.session_state:
        st.session_state['student_info'] = None
    
    # Chưa đăng nhập
    if not st.session_state['student_info']:
        with st.form("student_login"):
            code = st.text_input("Mã số học sinh:")
            if st.form_submit_button("Vào thi"):
                success, msg = auth.login_student(code, db)
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
        return
    
    # Đã đăng nhập
    student = st.session_state['student_info']
    st.success(f"**{student['name']}** - Lớp {student.get('class', 'N/A')}")
    
    if st.button("🚪 Đăng xuất"):
        auth.logout_student()
        st.rerun()
    
    StudentExamForm.render(student, db)
