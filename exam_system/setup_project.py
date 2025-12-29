#!/usr/bin/env python3
"""
Script tự động tạo cấu trúc thư mục components
Chạy: python setup_project_structure.py
"""

import os

def create_directory_structure():
    """Tạo cấu trúc thư mục"""
    
    directories = [
        "components",
        "components/common",
        "components/teacher",
        "components/student",
        "pages",
    ]
    
    print("📁 Đang tạo thư mục...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ {directory}/")
    
    print("\n✅ Đã tạo xong cấu trúc thư mục!")

def create_init_files():
    """Tạo các file __init__.py"""
    
    init_files = {
        "components/__init__.py": '''"""
Components package - Import tất cả để dễ dùng
"""

# Common components
from components.common.login import LoginForm
from components.common.header import UserHeader

# Teacher components
from components.teacher.question_form import QuestionCreationForm
from components.teacher.question_edit import QuestionEditForm
from components.teacher.grading import GradingInterface
from components.teacher.user_management import UserManagementPanel

# Student components
from components.student.exam_form import StudentExamForm
from components.student.result_view import ResultView

__all__ = [
    'LoginForm',
    'UserHeader',
    'QuestionCreationForm',
    'QuestionEditForm',
    'GradingInterface',
    'UserManagementPanel',
    'StudentExamForm',
    'ResultView',
]
''',
        
        "components/common/__init__.py": '''from .login import LoginForm
from .header import UserHeader

__all__ = ['LoginForm', 'UserHeader']
''',
        
        "components/teacher/__init__.py": '''from .question_form import QuestionCreationForm
from .question_edit import QuestionEditForm
from .grading import GradingInterface
from .user_management import UserManagementPanel

__all__ = [
    'QuestionCreationForm',
    'QuestionEditForm',
    'GradingInterface',
    'UserManagementPanel'
]
''',
        
        "components/student/__init__.py": '''from .exam_form import StudentExamForm
from .result_view import ResultView

__all__ = ['StudentExamForm', 'ResultView']
''',
        
        "pages/__init__.py": '''from .teacher_page import teacher_page
from .student_page import student_page

__all__ = ['teacher_page', 'student_page']
''',
    }
    
    print("\n📝 Đang tạo file __init__.py...")
    for filepath, content in init_files.items():
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ {filepath}")
    
    print("\n✅ Đã tạo xong các file __init__.py!")

def create_placeholder_files():
    """Tạo các file component placeholder"""
    
    placeholders = {
        "components/common/login.py": '''"""Form đăng nhập"""
import streamlit as st

class LoginForm:
    @staticmethod
    def render():
        st.title("🏫 Đăng Nhập")
        # TODO: Add login logic
''',
        
        "components/common/header.py": '''"""Header với user info"""
import streamlit as st

class UserHeader:
    @staticmethod
    def render(user):
        st.write(f"**{user['full_name']}**")
        # TODO: Add header logic
''',
        
        "components/teacher/question_form.py": '''"""Form tạo câu hỏi"""
import streamlit as st

class QuestionCreationForm:
    @staticmethod
    def render():
        st.subheader("📝 Tạo Câu Hỏi")
        # TODO: Add form logic
''',
        
        "components/teacher/question_edit.py": '''"""Form sửa câu hỏi"""
import streamlit as st

class QuestionEditForm:
    @staticmethod
    def render():
        st.subheader("✏️ Sửa Câu Hỏi")
        # TODO: Add edit logic
''',
        
        "components/teacher/grading.py": '''"""Giao diện chấm bài"""
import streamlit as st

class GradingInterface:
    @staticmethod
    def render():
        st.subheader("💯 Chấm Bài")
        # TODO: Add grading logic
''',
        
        "components/teacher/user_management.py": '''"""Quản lý tài khoản"""
import streamlit as st

class UserManagementPanel:
    @staticmethod
    def render():
        st.subheader("👥 Quản Lý User")
        # TODO: Add user management logic
''',
        
        "components/student/exam_form.py": '''"""Form làm bài thi"""
import streamlit as st

class StudentExamForm:
    @staticmethod
    def render(user):
        st.subheader("📝 Làm Bài Thi")
        # TODO: Add exam logic
''',
        
        "components/student/result_view.py": '''"""Xem kết quả thi"""
import streamlit as st

class ResultView:
    @staticmethod
    def render(user):
        st.subheader("📊 Kết Quả Thi")
        # TODO: Add result view logic
''',
        
        "pages/teacher_page.py": '''"""Trang giáo viên"""
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
''',
        
        "pages/student_page.py": '''"""Trang học sinh"""
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
''',
    }
    
    print("\n📄 Đang tạo placeholder files...")
    for filepath, content in placeholders.items():
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ {filepath}")
    
    print("\n✅ Đã tạo xong placeholder files!")

def create_main_file():
    """Tạo file main.py mới"""
    
    main_content = '''"""
HỆ THỐNG THI TRỰC TUYẾN - MODULAR VERSION
"""
import streamlit as st
from config import init_firebase
from auth import check_session
from components import LoginForm
from pages import teacher_page, student_page

# Init
init_firebase()
st.set_page_config(
    page_title="Hệ Thống Thi Trực Tuyến",
    layout="wide",
    page_icon="🏫"
)

# Router
if not check_session():
    LoginForm.render()
else:
    user = st.session_state['user']
    
    if user['role'] == 'teacher':
        teacher_page()
    elif user['role'] == 'student':
        student_page()
    else:
        st.error("⚠️ Role không hợp lệ!")
'''
    
    print("\n📝 Tạo main.py mới...")
    with open("main_modular.py", 'w', encoding='utf-8') as f:
        f.write(main_content)
    print("  ✅ main_modular.py")
    print("\n💡 Lưu ý: File main cũ vẫn giữ nguyên. Chạy:")
    print("   streamlit run main_modular.py")

def print_structure():
    """In cấu trúc thư mục"""
    
    print("\n" + "="*50)
    print("📁 CẤU TRÚC THƯ MỤC ĐÃ TẠO")
    print("="*50)
    print("""
exam_system/
│
├── main_modular.py          ← File main mới (gọn hơn!)
├── config.py
├── auth.py
├── utils.py
├── models.py
│
├── components/
│   ├── __init__.py
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── login.py
│   │   └── header.py
│   │
│   ├── teacher/
│   │   ├── __init__.py
│   │   ├── question_form.py
│   │   ├── question_edit.py
│   │   ├── grading.py
│   │   └── user_management.py
│   │
│   └── student/
│       ├── __init__.py
│       ├── exam_form.py
│       └── result_view.py
│
└── pages/
    ├── __init__.py
    ├── teacher_page.py
    └── student_page.py
""")

def main():
    """Main function"""
    print("""
╔══════════════════════════════════════════════╗
║   TẠO CẤU TRÚC COMPONENTS DIRECTORY          ║
╚══════════════════════════════════════════════╝
""")
    
    # Check nếu đã có components/
    if os.path.exists("components"):
        confirm = input("\n⚠️  Thư mục 'components/' đã tồn tại. Ghi đè? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Đã hủy!")
            return
    
    # Tạo cấu trúc
    create_directory_structure()
    create_init_files()
    create_placeholder_files()
    create_main_file()
    print_structure()
    
    print("\n" + "="*50)
    print("✅ HOÀN TẤT!")
    print("="*50)
    print("""
📌 BƯỚC TIẾP THEO:

1. Copy code từ các artifact vào các file tương ứng:
   - components/common/login.py
   - components/teacher/question_form.py
   - ... (các file khác)

2. Test import:
   python -c "from components import LoginForm; print('OK!')"

3. Chạy app:
   streamlit run main_modular.py

4. Nếu lỗi import, check:
   - Tất cả thư mục đều có __init__.py
   - Import đúng tên class
   - Đúng relative path
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Đã hủy!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()