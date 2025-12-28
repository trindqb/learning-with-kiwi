import streamlit as st
import hashlib
import time
import re

class AuthManager:
    """Quản lý xác thực cho cả GV và HS"""
    
    @staticmethod
    def authenticate_teacher(password):
        """Đăng nhập giáo viên với rate limiting"""
        if 'login_attempts' not in st.session_state:
            st.session_state['login_attempts'] = []
        
        current_time = time.time()
        st.session_state['login_attempts'] = [
            t for t in st.session_state['login_attempts']
            if current_time - t < 300
        ]
        
        if len(st.session_state['login_attempts']) >= 5:
            return False, "🚫 Quá nhiều lần thử. Chờ 5 phút."
        
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        stored_hash = st.secrets.get("admin", {}).get("password_hash", "")
        
        if input_hash == stored_hash:
            st.session_state['teacher_authenticated'] = True
            st.session_state['teacher_login_time'] = current_time
            st.session_state['login_attempts'] = []
            return True, "✅ Đăng nhập thành công!"
        else:
            st.session_state['login_attempts'].append(current_time)
            return False, "❌ Sai mật khẩu!"
    
    @staticmethod
    def check_teacher_session():
        """Kiểm tra session GV còn hiệu lực không"""
        if not st.session_state.get('teacher_authenticated', False):
            return False
        
        if 'teacher_login_time' in st.session_state:
            elapsed = time.time() - st.session_state['teacher_login_time']
            if elapsed > 1800:  # 30 phút
                st.session_state['teacher_authenticated'] = False
                return False
        
        return True
    
    @staticmethod
    def logout_teacher():
        """Đăng xuất GV"""
        st.session_state['teacher_authenticated'] = False
        if 'teacher_login_time' in st.session_state:
            del st.session_state['teacher_login_time']
    
    @staticmethod
    def validate_student_code(code):
        """Validate mã HS (HS001, HS12345...)"""
        return bool(re.match(r'^HS\d{3,6}$', code.upper().strip()))
    
    @staticmethod
    def login_student(student_code, db):
        """Đăng nhập học sinh"""
        code = student_code.upper().strip()
        
        if not AuthManager.validate_student_code(code):
            return False, "❌ Mã không hợp lệ (VD: HS001)"
        
        doc = db.collection("students").document(code).get()
        if doc.exists:
            student_data = doc.to_dict()
            student_data['id'] = code
            st.session_state['student_info'] = student_data
            st.session_state['student_login_time'] = time.time()
            return True, f"Xin chào {student_data['name']}!"
        else:
            return False, "❌ Mã số không tồn tại!"
    
    @staticmethod
    def logout_student():
        """Đăng xuất HS"""
        if 'student_info' in st.session_state:
            del st.session_state['student_info']
        if 'student_login_time' in st.session_state:
            del st.session_state['student_login_time']
