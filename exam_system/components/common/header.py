import streamlit as st
import time

class UserHeader:
    @staticmethod
    def render(user):
        """
        Render header với thông tin người dùng và nút đăng xuất
        user: dict chứa thông tin (full_name, role, id, v.v.)
        """
        
        # Tạo container cho header để dễ style hoặc cô lập layout
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Hiển thị avatar và tên dựa trên vai trò
                UserHeader._render_user_info(user)
                
            with col2:
                # Nút đăng xuất nằm bên phải
                UserHeader._render_logout_button()
        
        # Đường kẻ phân cách header và nội dung bên dưới
        st.divider()

    @staticmethod
    def _render_user_info(user):
        """Hiển thị thông tin người dùng đẹp mắt"""
        # Xác định role để chọn icon và màu sắc
        # Giả sử trong user dict có key 'role' hoặc ta đoán qua key khác
        is_teacher = user.get('role') == 'teacher' or 'teacher_id' in user
        
        if is_teacher:
            icon = "👨‍🏫"
            role_text = "Giáo Viên"
            sub_info = "Quản trị hệ thống"
            color = "blue"
        else:
            icon = "👨‍🎓"
            role_text = "Học Sinh"
            # Lấy mã học sinh nếu có, không thì để trống
            student_code = user.get('student_code', user.get('id', '')) 
            sub_info = f"MSSV: {student_code}" if student_code else "Thí sinh"
            color = "green"

        # Layout thông tin dạng: [Icon] [Tên to] / [Role nhỏ]
        st.markdown(
            f"""
            <div style='display: flex; align-items: center; gap: 10px;'>
                <div style='font-size: 2.5rem;'>{icon}</div>
                <div>
                    <div style='font-size: 1.2rem; font-weight: bold; color: {color};'>
                        {user.get('full_name', 'Người dùng')}
                    </div>
                    <div style='font-size: 0.9rem; color: gray; font-style: italic;'>
                        {role_text} | {sub_info}
                    </div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

    @staticmethod
    def _render_logout_button():
        """Nút đăng xuất có xử lý logic"""
        # Căn lề phải cho nút bấm bằng cách dùng cột trống hoặc custom css
        # Ở đây dùng logic đơn giản của Streamlit
        st.write("") # Spacer nhỏ để căn chỉnh chiều dọc với text bên trái
        
        if st.button("🚪 Đăng xuất", type="secondary", use_container_width=True):
            UserHeader.logout()

    @staticmethod
    def logout():
        """Hàm xử lý đăng xuất an toàn"""
        st.toast("Đang đăng xuất...", icon="👋")
        
        # Xóa toàn bộ session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
            
        time.sleep(0.5)
        st.rerun()