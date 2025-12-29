"""Form sửa câu hỏi"""
import streamlit as st
import time
from config import get_db
from utils import FileUtils, InputValidator

class QuestionEditForm:
    @staticmethod
    def render():
        st.subheader("✏️ Sửa Câu Hỏi")
        # Logic tìm kiếm và sửa câu hỏi (Rút gọn từ code gốc của bạn)
        col1, col2 = st.columns(2)
        with col1: find_sub = st.selectbox("Môn:", ["Toán", "Tiếng Việt", "Tiếng Anh"], key="edit_sub")
        with col2: find_set = st.selectbox("Mã đề:", [1, 2, 3], key="edit_set")
        
        if st.button("🔍 Tìm kiếm"):
            db = get_db()
            docs = db.collection("questions").where("subject", "==", find_sub).where("set_number", "==", find_set).stream()
            st.session_state['edit_list'] = [d.to_dict() | {"id": d.id} for d in docs]
            
        if st.session_state.get('edit_list'):
            q_list = st.session_state['edit_list']
            label_map = {f"({q['type']}) {q['content'][:40]}...": i for i, q in enumerate(q_list)}
            sel = st.selectbox("Chọn câu:", list(label_map.keys()))
            q_data = q_list[label_map[sel]]
            
            with st.form(f"edit_{q_data['id']}"):
                new_content = st.text_area("Nội dung:", value=q_data['content'])
                old_opts = ", ".join(q_data.get('options', []))
                new_opts_str = st.text_input("Các lựa chọn (cách nhau dấu phẩy):", value=old_opts)
                new_correct = st.text_input("Đáp án đúng:", value=q_data.get('correct_answer', ''))
                
                st.markdown("##### 📂 Cập nhật file (Bỏ qua nếu không muốn đổi)")
                if q_data.get('image_path'):
                    st.caption(f"Ảnh hiện tại: {q_data['image_path']}")
                new_image = st.file_uploader("Thay ảnh mới (JPG/PNG):", type=["jpg", "png", "jpeg"], key="edit_img")
                
                if q_data.get('audio_path'):
                    st.caption(f"Audio hiện tại: {q_data['audio_path']}")
                new_audio = st.file_uploader("Thay audio mới (MP3/WAV):", type=["mp3", "wav"], key="edit_aud")
                
                if st.form_submit_button("Lưu Thay Đổi", type="primary"):
                    db = get_db()
                    update_data = {
                        "content": InputValidator.sanitize(new_content, 1000),
                        "options": [x.strip() for x in new_opts_str.split(",")] if new_opts_str else [],
                        "correct_answer": new_correct
                    }
                    
                    with st.spinner("Đang cập nhật..."):
                        if new_image:
                            new_img_path = FileUtils.upload_to_storage(new_image, "question_images")
                            if new_img_path:
                                update_data["image_path"] = new_img_path
                        
                        if new_audio:
                            new_aud_path = FileUtils.upload_to_storage(new_audio, "question_audio")
                            if new_aud_path:
                                update_data["audio_path"] = new_aud_path
                        
                        db.collection("questions").document(q_data['id']).update(update_data)
                        st.success("✅ Đã sửa thành công! Vui lòng bấm 'Tìm kiếm' lại để thấy thay đổi.")
                        if 'edit_list' in st.session_state:
                            del st.session_state['edit_list']
                        time.sleep(1)
                        st.rerun()
