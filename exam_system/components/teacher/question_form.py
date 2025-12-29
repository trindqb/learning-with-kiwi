"""Form tạo câu hỏi"""
import streamlit as st
from firebase_admin import firestore
from config import get_db
from utils import FileUtils, InputValidator

class QuestionCreationForm:
    @staticmethod
    def render():
        st.subheader("📝 Tạo Câu Hỏi Mới")
        with st.form("create_question_form"):
            c1, c2, c3 = st.columns(3)
            with c1: subject = st.selectbox("Môn thi:", ["Toán", "Tiếng Việt", "Tiếng Anh"])
            with c2: set_num = st.selectbox("Mã đề:", [1, 2, 3])
            with c3: q_type = st.selectbox("Loại câu:", ["Trắc nghiệm (MC)", "Nghe (Listening)", "Nói (Speaking)", "Tự luận (Essay)"])
            
            content = st.text_area("Đề bài:", max_chars=1000)
            col_up1, col_up2 = st.columns(2)
            with col_up1: image_file = st.file_uploader("📷 Hình ảnh", type=["jpg", "png"])
            with col_up2: audio_file = st.file_uploader("🎧 Audio", type=["mp3", "wav"]) if q_type in ["Nghe (Listening)", "Trắc nghiệm (MC)"] else None
            
            options = []
            correct_ans = ""
            if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                opts_str = st.text_input("Các lựa chọn (cách nhau dấu phẩy):")
                if opts_str: options = [InputValidator.sanitize(x.strip()) for x in opts_str.split(",")]
                correct_ans = st.selectbox("Đáp án đúng:", options if options else ["Chưa nhập"])
            
            if st.form_submit_button("Lưu Câu Hỏi", type="primary"):
                if not content.strip():
                    st.error("Thiếu nội dung câu hỏi")
                    return
                
                with st.spinner("Đang lưu..."):
                    db = get_db()
                    img_path = FileUtils.upload_to_storage(image_file, "question_images")
                    aud_path = FileUtils.upload_to_storage(audio_file, "question_audio")
                    
                    db.collection("questions").add({
                        "subject": subject, "set_number": set_num, "type": q_type,
                        "content": InputValidator.sanitize(content, 1000), "options": options,
                        "correct_answer": correct_ans, "image_path": img_path, "audio_path": aud_path,
                        "created_at": firestore.SERVER_TIMESTAMP
                    })
                    st.success("✅ Đã tạo câu hỏi!")