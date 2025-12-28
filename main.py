import streamlit as st
from audio_recorder_streamlit import audio_recorder
import firebase_admin
from firebase_admin import credentials, storage, firestore
import time

# --- 1. CẤU HÌNH & KẾT NỐI FIREBASE ---
st.set_page_config(page_title="Thi Tiếng Anh Lớp 4", page_icon="🎙️")

if not firebase_admin._apps:
    # Đọc key từ hệ thống bảo mật của Streamlit (Secrets)
    key_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(key_dict)
    
    firebase_admin.initialize_app(cred, {
        # LƯU Ý: Thay đúng tên Bucket của bạn vào dòng dưới
        'storageBucket': 'TEN-PROJECT-CUA-BAN.appspot.com' 
    })

db = firestore.client()
bucket = storage.bucket()

if 'user_answers' not in st.session_state:
    st.session_state['user_answers'] = {}

# --- 2. LOGIC CÁC CÂU HỎI (OOP) ---
class QuestionBase:
    def __init__(self, q_id, title):
        self.q_id = q_id
        self.title = title
    def render(self):
        st.markdown(f"**Câu {self.q_id}:** {self.title}")

class SpeakingQuestion(QuestionBase):
    def render(self):
        super().render()
        st.info("Bấm Micro để ghi âm - Bấm lại để dừng:")
        audio_bytes = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#3498db", icon_size="2x", key=f"rec_{self.q_id}")
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            st.session_state['user_answers'][self.q_id] = {"type": "Speaking", "data": audio_bytes}

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🎙️ BÀI THI NÓI - LỚP 4")
student_name = st.text_input("Họ và tên học sinh:")
st.divider()

# Tạo đề thi mẫu
questions = [
    SpeakingQuestion(1, "What is your name?"),
    SpeakingQuestion(2, "What animals do you like?")
]

for q in questions:
    q.render()
    st.write("---")

# --- 4. XỬ LÝ NỘP BÀI ---
if st.button("NỘP BÀI (SUBMIT)", type="primary"):
    if not student_name:
        st.error("Con chưa nhập tên!")
    else:
        answers = st.session_state['user_answers']
        if not answers:
            st.warning("Con chưa ghi âm câu nào cả!")
        else:
            with st.spinner("Đang nộp bài lên hệ thống..."):
                try:
                    # Upload file ghi âm lên Firebase Storage
                    for q_id, val in answers.items():
                        if val['type'] == 'Speaking':
                            timestamp = int(time.time())
                            # Tạo tên file an toàn (không dấu)
                            safe_name = "".join([c for c in student_name if c.isalnum() or c==' ']).strip().replace(" ", "_")
                            blob_name = f"bai_thi/{safe_name}_cau{q_id}_{timestamp}.wav"
                            
                            blob = bucket.blob(blob_name)
                            blob.upload_from_string(val['data'], content_type='audio/wav')
                            val['data'] = blob_name # Chỉ lưu đường dẫn text vào DB cho nhẹ
                    
                    # Lưu thông tin vào Firestore
                    db.collection("ket_qua_thi").add({
                        "name": student_name,
                        "answers": str(answers), # Lưu dạng chuỗi để dễ đọc
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.balloons()
                    st.success("✅ Nộp bài thành công! Con giỏi lắm.")
                except Exception as e:
                    st.error(f"Lỗi: {e}")