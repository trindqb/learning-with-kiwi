"""
Các hàm tiện ích: Upload file, validate input
"""
import streamlit as st
import re
import uuid
import time
from config import get_storage

class FileUtils:
    """Xử lý upload/download file"""
    
    @staticmethod
    def validate_file(file_obj, allowed_types, max_mb=3):
        """Kiểm tra file hợp lệ"""
        if not file_obj:
            return True, ""
        
        ext = file_obj.name.split(".")[-1].lower()
        if ext not in allowed_types:
            return False, f"Chỉ chấp nhận: {', '.join(allowed_types)}"
        
        if file_obj.size > max_mb * 1024 * 1024:
            return False, f"File quá {max_mb}MB"
        
        return True, ""
    
    @staticmethod
    def upload_to_storage(file_obj, folder):
        """Upload file lên Firebase Storage"""
        if not file_obj:
            return None
        
        allowed = ['jpg', 'jpeg', 'png', 'mp3', 'wav']
        valid, msg = FileUtils.validate_file(file_obj, allowed, 3)
        
        if not valid:
            st.error(msg)
            return None
        
        bucket = get_storage()
        ext = file_obj.name.split(".")[-1].lower()
        filename = f"{folder}/{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
        
        blob = bucket.blob(filename)
        blob.upload_from_string(
            file_obj.getvalue(),
            content_type=file_obj.type
        )
        
        return filename
    
    @staticmethod
    def get_signed_url(path, expiration=900):
        """Lấy URL tạm thời (15 phút)"""
        if not path:
            return None
        try:
            bucket = get_storage()
            blob = bucket.blob(path)
            return blob.generate_signed_url(version="v4", expiration=expiration)
        except Exception as e:
            st.error(f"Lỗi tải file: {str(e)}")
            return None


class InputValidator:
    """Validate và sanitize input"""
    
    @staticmethod
    def sanitize(text, max_len=500):
        """Loại bỏ ký tự nguy hiểm"""
        if not text or not isinstance(text, str):
            return ""
        text = re.sub(r'[<>\"\'%;()&+]', '', text)
        return text[:max_len].strip()