import streamlit as st
import time

class LoginForm:
    @staticmethod
    def _apply_custom_css():
        st.markdown("""
            <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                .login-title {
                    font-size: 2.2rem !important;
                    font-weight: 700 !important;
                    color: #1E88E5;
                    text-align: center;
                    margin-bottom: 10px;
                }
                /* Tùy chỉnh input field cho đẹp hơn */
                .stTextInput > div > div > input {
                    border-radius: 10px;
                }
            </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render():
        LoginForm._apply_custom_css()
        
        # Căn giữa form
        col1, col2, col3 = st.columns([1, 1.5, 1])
        
        with col2:
            with st.container(border=True):
                st.markdown('<p class="login-title">🏫 Hệ Thống Thi Online</p>', unsafe_allow_html=True)
                
                # Tabs chuyển đổi vai trò
                tab_student, tab_teacher = st.tabs(["👨‍🎓 Học Sinh", "👨‍🏫 Giáo Viên"])
                
                with tab_student:
                    LoginForm._student_login_ui()
                
                with tab_teacher:
                    LoginForm._teacher_login_ui()

    @staticmethod
    def _student_login_ui():
        """Form đăng nhập Học sinh: Cần Mã HS + Mật khẩu"""
        from auth import AuthManager
        from config import get_db
        
        st.write("#### 🔐 Đăng nhập làm bài")
        
        # 1. Nhập Mã Học Sinh (Tài khoản)
        student_code = st.text_input(
            "Mã Học Sinh", 
            placeholder="Ví dụ: HS001", 
            key="std_user"
        )
        
        # 2. Nhập Mật Khẩu (Mới thêm)
        password = st.text_input(
            "Mật khẩu", 
            type="password", 
            placeholder="Nhập mật khẩu cá nhân", 
            key="std_pass"
        )
        
        if st.button("Vào Phòng Thi", key="btn_std_login", type="primary", use_container_width=True):
            # Validate nhập liệu
            if not student_code or not password:
                st.toast("⚠️ Vui lòng nhập đầy đủ Mã HS và Mật khẩu!")
                return

            try:
                with st.spinner("Đang xác thực thông tin..."):
                    db = get_db()
                    
                    # LƯU Ý: Bạn cần cập nhật hàm login_student trong auth.py 
                    # để nhận thêm tham số password: login_student(code, password, db)
                    success, message = AuthManager.login_student(student_code, password, db) 
                    
                    if success:
                        st.success("Đăng nhập thành công!")
                        
                        # --- LƯU SESSION CHO HEADER ---
                        st.session_state["user"] = {
                            "full_name": message,  # Giả sử hàm trả về tên HS
                            "role": "student",
                            "student_code": student_code
                        }
                        
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)
            except Exception as e:
                # Fallback nếu hàm login cũ chưa sửa (chỉ nhận 2 tham số)
                st.error(f"Lỗi hệ thống (Auth): {str(e)}")
                st.info("💡 Gợi ý: Hãy cập nhật hàm AuthManager.login_student để nhận thêm mật khẩu.")

    @staticmethod
    def _teacher_login_ui():
        """Form đăng nhập Giáo viên: Cần Username + Password"""
        from auth import AuthManager
        from config import get_db
        
        st.write("#### 🛠️ Quản trị viên")
        
        # 1. Nhập Tên đăng nhập (Mới thêm)
        username = st.text_input(
            "Tên đăng nhập", 
            placeholder="admin / gv01",
            key="teach_user"
        )
        
        # 2. Nhập Mật Khẩu
        password = st.text_input(
            "Mật khẩu", 
            type="password", 
            key="teach_pass"
        )
        
        if st.button("Đăng Nhập Quản Trị", key="btn_teach_login", type="primary", use_container_width=True):
            if not username or not password:
                st.toast("⚠️ Vui lòng nhập Tên đăng nhập và Mật khẩu!")
                return

            with st.spinner("Đang đăng nhập..."):
                db = get_db()
                success, message = AuthManager.authenticate_teacher(username, password, db)
                
                if success:
                    st.balloons()
                    st.success(message)
                    
                    # --- LƯU SESSION CHO HEADER ---
                    st.session_state["user"] = {
                        "full_name": message if message else "Giáo Viên",
                        "role": "teacher",
                        "id": username
                    }
                    
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(message)