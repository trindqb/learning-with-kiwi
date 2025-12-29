"""
Router cho các trang chính
"""
import streamlit as st
from auth import AuthManager
from config import get_db
from components import TeacherLoginForm, QuestionCreationForm, StudentExamForm
import time

def login_page():
    """Trang đăng nhập chính - chọn vai trò"""
    st.set_page_config(page_title="Hệ Thống Thi Trực Tuyến", layout="centered")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🏫 HỆ THỐNG HỌC VÀ THI CÙNG KIWI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Chọn vai trò của bạn để tiếp tục</p>", unsafe_allow_html=True)
        
        st.divider()
        
        col_teacher, col_student = st.columns(2)
        
        with col_teacher:
            st.markdown("<h3 style='text-align: center;'>👨‍🏫</h3>", unsafe_allow_html=True)
            if st.button("GIÁO VIÊN", use_container_width=True, key="btn_teacher"):
                st.session_state['user_role'] = 'teacher'
                st.rerun()
        
        with col_student:
            st.markdown("<h3 style='text-align: center;'>👨‍🎓</h3>", unsafe_allow_html=True)
            if st.button("HỌC SINH", use_container_width=True, key="btn_student"):
                st.session_state['user_role'] = 'student'
                st.rerun()
        
        st.divider()
        
        # Show role-specific login form
        if st.session_state['user_role'] == 'teacher':
            st.markdown("<h4 style='text-align: center;'>Đăng Nhập Giáo Viên</h4>", unsafe_allow_html=True)
            with st.form("teacher_login_page"):
                password = st.text_input("Mật khẩu:", type="password", key="teacher_pwd")
                col_back, col_submit = st.columns(2)
                
                with col_back:
                    if st.form_submit_button("← Quay lại", use_container_width=True):
                        st.session_state['user_role'] = None
                        st.rerun()
                
                with col_submit:
                    if st.form_submit_button("Đăng nhập", type="primary", use_container_width=True):
                        auth = AuthManager()
                        success, msg = auth.authenticate_teacher(password)
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
        
        elif st.session_state['user_role'] == 'student':
            st.markdown("<h4 style='text-align: center;'>Nhập Thông Tin Học Sinh</h4>", unsafe_allow_html=True)
            db = get_db()
            with st.form("student_login_page"):
                student_code = st.text_input("Mã số học sinh (VD: HS001):", key="student_code")
                col_back, col_submit = st.columns(2)
                
                with col_back:
                    if st.form_submit_button("← Quay lại", use_container_width=True):
                        st.session_state['user_role'] = None
                        st.rerun()
                
                with col_submit:
                    if st.form_submit_button("Vào thi", type="primary", use_container_width=True):
                        auth = AuthManager()
                        success, msg = auth.login_student(student_code, db)
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)


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
    
    tab1, tab2 = st.tabs(["➕ Tạo Câu Hỏi", "💯 Chấm Bài"])
    
    db = get_db()
    
    with tab1:
        QuestionCreationForm.render(db)
    
    with tab2:
        st.info("Chức năng đang phát triển...")


def student_page():
    """Trang học sinh"""
    st.title("✍️ KHU VỰC THI HỌC SINH")
    
    auth = AuthManager()
    db = get_db()
    
    if 'student_info' not in st.session_state:
        st.session_state['student_info'] = None
    
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
    
    student = st.session_state['student_info']
    st.success(f"**{student['name']}** - Lớp {student.get('class', 'N/A')}")
    
    if st.button("🚪 Đăng xuất"):
        auth.logout_student()
        st.rerun()
    
    StudentExamForm.render(student, db)