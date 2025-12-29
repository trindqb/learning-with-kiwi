"""
Quản lý xác thực cho giáo viên và học sinh
"""
import streamlit as st
import hashlib
import time
import re
import logging
import os
from datetime import datetime

# Cấu hình logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"auth_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AuthManager:
    """Quản lý xác thực cho cả GV và HS"""
    
    @staticmethod
    def authenticate_teacher(username, password, db):
        """Đăng nhập giáo viên từ collection users"""
        logger.info(f"🔍 Bắt đầu đăng nhập giáo viên: {username}")
        
        if 'login_attempts' not in st.session_state:
            st.session_state['login_attempts'] = []
        
        current_time = time.time()
        st.session_state['login_attempts'] = [
            t for t in st.session_state['login_attempts']
            if current_time - t < 300
        ]
        
        attempt_count = len(st.session_state['login_attempts'])
        logger.debug(f"📊 Lần đăng nhập thất bại gần đây: {attempt_count}/5")
        
        if attempt_count >= 5:
            logger.warning(f"🚫 Quá nhiều lần thử đăng nhập từ: {username}")
            return False, "🚫 Quá nhiều lần thử. Chờ 5 phút."
        
        # Tìm giáo viên trong collection "users"
        logger.info(f"🔍 Tìm kiếm giáo viên trong 'users'")
        user_docs = db.collection("users")\
            .where("username", "==", username)\
            .where("role", "==", "teacher")\
            .limit(1)\
            .stream()
        
        user_docs_list = list(user_docs)
        if not user_docs_list:
            st.session_state['login_attempts'].append(current_time)
            logger.warning(f"❌ Giáo viên không tồn tại: {username}")
            return False, "❌ Tên đăng nhập không đúng!"
        
        teacher_doc = user_docs_list[0]
        teacher_data = teacher_doc.to_dict()
        doc_id = teacher_doc.id
        
        logger.info(f"✓ Tìm thấy giáo viên: {doc_id}")
        
        # Kiểm tra mật khẩu
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        stored_password_hash = teacher_data.get('password_hash', '').strip() if teacher_data.get('password_hash') else ''
        stored_password = teacher_data.get('password', '').strip() if teacher_data.get('password') else ''
        
        logger.debug(f"🔐 Kiểm tra mật khẩu")
        logger.debug(f"   - Doc ID: {doc_id}")
        logger.debug(f"   - Có password_hash: {bool(stored_password_hash)}")
        logger.debug(f"   - Có password: {bool(stored_password)}")
        logger.debug(f"   - Input hash: {input_hash[:20]}...")
        
        if stored_password_hash:
            logger.info(f"🔐 Kiểm tra mật khẩu dạng hash")
            if input_hash != stored_password_hash:
                st.session_state['login_attempts'].append(current_time)
                logger.error(f"❌ Hash không khớp")
                return False, "❌ Mật khẩu không đúng!"
            logger.info(f"✓ Hash khớp!")
        elif stored_password:
            logger.info(f"🔐 Kiểm tra mật khẩu dạng plaintext")
            if password != stored_password:
                st.session_state['login_attempts'].append(current_time)
                logger.error(f"❌ Mật khẩu plaintext không khớp")
                return False, "❌ Mật khẩu không đúng!"
            logger.info(f"✓ Mật khẩu plaintext khớp!")
        else:
            st.session_state['login_attempts'].append(current_time)
            logger.error(f"❌ Giáo viên không có mật khẩu")
            return False, "❌ Chưa thiết lập mật khẩu!"
        
        # Lưu session
        st.session_state['teacher_authenticated'] = True
        st.session_state['teacher_login_time'] = current_time
        st.session_state['teacher_info'] = teacher_data
        st.session_state['teacher_id'] = doc_id
        st.session_state['login_attempts'] = []
        
        logger.info(f"✅ Đăng nhập giáo viên thành công: {username}")
        return True, "✅ Đăng nhập thành công!"
    
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
    def login_student(student_code, password, db):
        """Đăng nhập học sinh từ collection users"""
        input_text = student_code.strip()
        student_data = None
        doc_id = None
        
        logger.info(f"🔍 Bắt đầu đăng nhập học sinh: {input_text}")
        
        # Thử tìm bằng Mã HS (HS001, HS12345...)
        if AuthManager.validate_student_code(input_text):
            code = input_text.upper()
            logger.info(f"✓ Nhập liệu có format mã HS: {code}")
            
            # Tìm trong collection "users"
            doc = db.collection("users").document(code).get()
            if doc.exists:
                student_data = doc.to_dict()
                doc_id = code
                logger.info(f"✓ Tìm thấy HS bằng mã HS001: {code}")
            else:
                logger.warning(f"✗ Không tìm thấy mã HS: {code}")
        
        # Nếu không tìm thấy, tìm bằng Username
        if not student_data:
            logger.info(f"🔍 Tìm kiếm bằng username: {input_text}")
            docs = db.collection("users")\
                .where("username", "==", input_text)\
                .where("role", "==", "student")\
                .limit(1)\
                .stream()
            docs_list = list(docs)
            if docs_list:
                doc = docs_list[0]
                student_data = doc.to_dict()
                doc_id = doc.id
                logger.info(f"✓ Tìm thấy HS bằng username: {doc_id}")
            else:
                logger.warning(f"✗ Không tìm thấy username: {input_text}")
        
        # Nếu vẫn không tìm thấy
        if not student_data:
            logger.error(f"❌ Tài khoản không tồn tại: {input_text}")
            return False, "❌ Mã HS hoặc tên đăng nhập không tồn tại!"
        
        # Kiểm tra mật khẩu
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        stored_password_hash = student_data.get('password_hash', '').strip() if student_data.get('password_hash') else ''
        stored_password = student_data.get('password', '').strip() if student_data.get('password') else ''
        
        logger.debug(f"📋 Dữ liệu tài khoản:")
        logger.debug(f"   - Doc ID: {doc_id}")
        logger.debug(f"   - Toàn bộ keys: {list(student_data.keys())}")
        logger.debug(f"   - Có password_hash: {bool(stored_password_hash)}")
        logger.debug(f"   - Có password: {bool(stored_password)}")
        
        # Cách 1: Kiểm tra hash (nếu có password_hash)
        if stored_password_hash:
            logger.info(f"🔐 Kiểm tra mật khẩu dạng hash")
            if input_hash != stored_password_hash:
                logger.error(f"❌ Hash không khớp")
                return False, "❌ Mật khẩu không chính xác!"
            logger.info(f"✓ Hash khớp!")
        # Cách 2: Kiểm tra trực tiếp (nếu password lưu dạng plaintext)
        elif stored_password:
            logger.info(f"🔐 Kiểm tra mật khẩu dạng plaintext")
            if password != stored_password:
                logger.error(f"❌ Mật khẩu plaintext không khớp")
                return False, "❌ Mật khẩu không chính xác!"
            logger.info(f"✓ Mật khẩu plaintext khớp!")
        # Cách 3: Nếu không có cả hai
        else:
            logger.error(f"❌ Tài khoản không có mật khẩu")
            return False, "❌ Chưa thiết lập mật khẩu cho tài khoản này!"
        
        # Lưu thông tin vào session
        student_data['id'] = doc_id
        st.session_state['student_info'] = student_data
        st.session_state['student_login_time'] = time.time()
        
        full_name = student_data.get('full_name', student_data.get('name', 'Học Sinh'))
        logger.info(f"✅ Đăng nhập thành công: {full_name} ({doc_id})")
        return True, full_name
    
    @staticmethod
    def logout_student():
        """Đăng xuất HS"""
        if 'student_info' in st.session_state:
            del st.session_state['student_info']
        if 'student_login_time' in st.session_state:
            del st.session_state['student_login_time']