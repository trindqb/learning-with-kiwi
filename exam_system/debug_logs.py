"""
Trang debug để xem logs
"""
import streamlit as st
import os
from datetime import datetime

st.set_page_config(page_title="Debug Logs", layout="wide")

st.title("🔍 Debug Logs")

# Kiểm tra nếu người dùng là admin
if not st.session_state.get('teacher_authenticated', False):
    st.warning("⚠️ Chỉ giáo viên mới có thể xem logs")
    st.stop()

# Thư mục logs
log_dir = "logs"
if not os.path.exists(log_dir):
    st.error("Chưa có logs")
    st.stop()

# Danh sách file logs
log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')], reverse=True)

if not log_files:
    st.info("Chưa có log files")
    st.stop()

# Chọn log file
selected_file = st.selectbox("Chọn log file:", log_files)

if selected_file:
    log_path = os.path.join(log_dir, selected_file)
    
    # Đọc nội dung
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Thống kê
    lines = content.split('\n')
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tổng dòng log", len([l for l in lines if l.strip()]))
    
    with col2:
        error_count = len([l for l in lines if 'ERROR' in l or '❌' in l])
        st.metric("Lỗi", error_count)
    
    with col3:
        success_count = len([l for l in lines if 'thành công' in l or '✅' in l])
        st.metric("Thành công", success_count)
    
    # Filters
    st.subheader("🔎 Lọc logs")
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.selectbox("Cấp độ log:", ["Tất cả", "DEBUG", "INFO", "WARNING", "ERROR"])
    
    with col2:
        search_text = st.text_input("Tìm kiếm:", "")
    
    # Lọc nội dung
    filtered_lines = []
    for line in lines:
        if not line.strip():
            continue
        
        # Lọc theo cấp độ
        if log_level != "Tất cả" and log_level not in line:
            continue
        
        # Lọc theo text
        if search_text and search_text.lower() not in line.lower():
            continue
        
        filtered_lines.append(line)
    
    # Hiển thị logs
    st.subheader(f"📋 Logs ({len(filtered_lines)} dòng)")
    
    # Reverse để xem logs mới nhất ở trên
    log_text = '\n'.join(reversed(filtered_lines[-500:]))  # Hiển thị 500 dòng cuối cùng
    
    st.code(log_text, language="log")
    
    # Tải logs
    st.download_button(
        label="📥 Tải file log",
        data=content,
        file_name=selected_file,
        mime="text/plain"
    )
