"""
Cấu hình Firebase và các services
"""
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage

def init_firebase():
    """Khởi tạo Firebase một lần duy nhất"""
    if not firebase_admin._apps:
        key_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'learning-with-kiwi.firebasestorage.app'
        })

def get_db():
    """Lấy Firestore client"""
    return firestore.client()

def get_storage():
    """Lấy Storage bucket"""
    return storage.bucket()