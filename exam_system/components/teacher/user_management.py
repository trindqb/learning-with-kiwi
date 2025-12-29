"""Quản lý tài khoản"""
import streamlit as st
import hashlib
from config import get_db
from utils import InputValidator

class UserManagementPanel:
    @staticmethod
    def render():
        st.subheader("👥 Quản Lý Tài Khoản")
        db = get_db()
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["➕ Tạo Tài Khoản", "📋 Danh Sách Tài Khoản", "⚙️ Thay Đổi Mật Khẩu"])
        
        with tab1:
            UserManagementPanel._create_account(db)
        
        with tab2:
            UserManagementPanel._list_accounts(db)
        
        with tab3:
            UserManagementPanel._change_password(db)
    
    @staticmethod
    def _create_account(db):
        """Tab tạo tài khoản mới"""
        st.write("#### ➕ Tạo Tài Khoản Mới")
        
        with st.form("create_account_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_id = st.text_input("Mã người dùng:", placeholder="HS001 hoặc GV001")
                username = st.text_input("Tên đăng nhập:", placeholder="hocsinh001")
                password = st.text_input("Mật khẩu:", type="password", placeholder="Mật khẩu mạnh")
            
            with col2:
                full_name = st.text_input("Họ tên:", placeholder="Nguyễn Văn A")
                role = st.selectbox("Vai trò:", ["student", "teacher"])
                email = st.text_input("Email:", placeholder="example@school.edu.vn")
            
            if role == "student":
                class_name = st.text_input("Lớp:", placeholder="4A")
            else:
                subjects = st.text_input("Môn dạy (cách nhau dấu phẩy):", placeholder="Toán, Tiếng Việt")
            
            if st.form_submit_button("✅ Tạo Tài Khoản", type="primary"):
                if not all([user_id, username, password, full_name]):
                    st.error("⚠️ Vui lòng điền đầy đủ thông tin")
                    return
                
                try:
                    user_data = {
                        "username": username.lower().strip(),
                        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
                        "role": role,
                        "full_name": full_name.strip(),
                        "email": email or f"{username}@school.edu.vn",
                        "is_active": True
                    }
                    
                    if role == "student":
                        user_data["metadata"] = {"class": class_name}
                    else:
                        user_data["metadata"] = {
                            "subjects": [s.strip() for s in subjects.split(",")]
                        }
                    
                    db.collection("users").document(user_id).set(user_data)
                    st.success(f"✅ Tạo tài khoản {user_id} thành công!")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
    
    @staticmethod
    def _list_accounts(db):
        """Tab danh sách tài khoản"""
        st.write("#### 📋 Danh Sách Tài Khoản")
        
        role_filter = st.selectbox("Lọc theo vai trò:", ["Tất cả", "student", "teacher"])
        
        if st.button("🔄 Tải danh sách"):
            if role_filter == "Tất cả":
                users = db.collection("users").stream()
            else:
                users = db.collection("users").where("role", "==", role_filter).stream()
            
            user_list = [{"id": doc.id, **doc.to_dict()} for doc in users]
            st.session_state['user_list'] = user_list
        
        if st.session_state.get('user_list'):
            users = st.session_state['user_list']
            
            # Hiển thị bảng
            for user in users:
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                
                with col1:
                    st.write(f"**{user['id']}**")
                with col2:
                    st.write(f"👤 {user['full_name']}")
                with col3:
                    role_badge = "🎓" if user['role'] == "student" else "👨‍🏫"
                    st.write(f"{role_badge} {user['username']}")
                with col4:
                    if st.button("🗑️", key=f"del_{user['id']}"):
                        db.collection("users").document(user['id']).delete()
                        st.success(f"Đã xóa {user['id']}")
                        st.rerun()
    
    @staticmethod
    def _change_password(db):
        """Tab thay đổi mật khẩu"""
        st.write("#### ⚙️ Thay Đổi Mật Khẩu")
        
        with st.form("change_password_form"):
            user_id = st.text_input("Mã người dùng (HS001, GV001...):", placeholder="HS001")
            new_password = st.text_input("Mật khẩu mới:", type="password")
            confirm_password = st.text_input("Xác nhận mật khẩu:", type="password")
            
            if st.form_submit_button("✅ Cập Nhật Mật Khẩu", type="primary"):
                if not user_id or not new_password:
                    st.error("⚠️ Vui lòng điền đầy đủ")
                    return
                
                if new_password != confirm_password:
                    st.error("❌ Mật khẩu không khớp")
                    return
                
                try:
                    db.collection("users").document(user_id).update({
                        "password_hash": hashlib.sha256(new_password.encode()).hexdigest()
                    })
                    st.success(f"✅ Đã cập nhật mật khẩu cho {user_id}")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
