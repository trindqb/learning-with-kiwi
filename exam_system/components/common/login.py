"""Form đăng nhập UI cải tiến"""
import streamlit as st
import time

class LoginForm:
    @staticmethod
    def _apply_custom_css():
        """Thêm CSS để làm đẹp giao diện"""
        st.markdown("""
            <style>
                /* Ẩn menu mặc định của Streamlit để trông giống App hơn */
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                
                /* Style cho Tiêu đề */
                .login-title {
                    font-size: 2.5rem !important;
                    font-weight: 700 !important;
                    color: #1E88E5;
                    text-align: center;
                    margin-bottom: 20px;
                }
                
                /* Style cho Card đăng nhập */
                div.block-container {
                    padding-top: 2rem;
                }
            </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render():
        LoginForm._apply_custom_css()
        
        # Chia cột để form nằm gọn ở giữa màn hình (tỉ lệ 1-2-1 hoặc 1-1.5-1 tùy màn hình)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        
        with col2:
            # Container tạo khung viền (Streamlit >= 1.29)
            with st.container(border=True):
                st.markdown('<p class="login-title">🏫 E-Learning Portal</p>', unsafe_allow_html=True)
                st.write("Chào mừng quay trở lại! Vui lòng đăng nhập.")
                
                # Dùng Tabs thay vì Radio button nhìn hiện đại hơn
                tab_student, tab_teacher = st.tabs(["👨‍🎓 Học Sinh", "👨‍🏫 Giáo Viên"])
                
                with tab_student:
                    LoginForm._student_login_ui()
                
                with tab_teacher:
                    LoginForm._teacher_login_ui()

    @staticmethod
    def _teacher_login_ui():
        """Giao diện đăng nhập giáo viên"""
        from auth import AuthManager
        
        st.markdown("### 🔐 Cổng Giáo Viên")
        
        # Thêm icon vào label
        password = st.text_input(
            "Mật khẩu quản trị",
            type="password",
            placeholder="Nhập mật khẩu của bạn...",
            help="Liên hệ admin nếu quên mật khẩu"
        )
        
        st.markdown("---") # Đường kẻ phân cách
        
        # Nút bấm full chiều rộng
        if st.button("Đăng Nhập Ngay", key="teacher_login_btn", type="primary", use_container_width=True):
            if not password:
                st.toast("⚠️ Vui lòng nhập mật khẩu!") # Dùng toast thay vì error nhìn nhẹ nhàng hơn
            else:
                with st.spinner("Đang xác thực..."):
                    time.sleep(0.5) # Giả lập delay để tạo cảm giác xử lý
                    success, message = AuthManager.authenticate_teacher(password)
                    if success:
                        st.balloons() # Hiệu ứng chúc mừng
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

    @staticmethod
    def _student_login_ui():
        """Giao diện đăng nhập học sinh"""
        from auth import AuthManager
        from config import get_db
        
        st.markdown("### 📚 Cổng Học Sinh")
        
        student_code = st.text_input(
            "Mã số học sinh (ID)",
            placeholder="VD: HS001",
            max_chars=10,
            help="Mã số được in trên thẻ học sinh"
        )
        
        st.markdown("---")
        
        if st.button("Vào Phòng Thi", key="student_login_btn", type="primary", use_container_width=True):
            if not student_code:
                st.toast("⚠️ Vui lòng nhập mã học sinh!")
            else:
                try:
                    with st.spinner("Đang kết nối CSDL..."):
                        db = get_db()
                        success, message = AuthManager.login_student(student_code, db)
                        
                        if success:
                            st.success(message)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                except Exception as e:
                    st.error(f"❌ Lỗi hệ thống: {str(e)}")