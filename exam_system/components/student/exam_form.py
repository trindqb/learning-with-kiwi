"""Giao diện làm bài thi cho học sinh (Đã sửa lỗi ID)"""
import streamlit as st
import time
from firebase_admin import firestore
from config import get_db
from utils import FileUtils, InputValidator
from audio_recorder_streamlit import audio_recorder

class StudentExamForm:
    @staticmethod
    def render(student_info):
        # --- ĐOẠN FIX LỖI KEY ERROR ---
        # Logic: Thử lấy 'id', nếu không có thì lấy 'student_code'
        student_id = student_info.get('student_code')
        
        # Nếu vẫn không lấy được ID (trường hợp data lỗi nặng), dừng lại để tránh crash
        if not student_id:
            st.error("❌ Lỗi dữ liệu phiên đăng nhập. Vui lòng đăng xuất và đăng nhập lại.")
            return
        # ------------------------------

        st.subheader(f"📝 Khu Vực Thi: {student_info.get('full_name', 'Học sinh')}")
        db = get_db()

        # 1. Chọn môn và đề thi
        col1, col2 = st.columns(2)
        with col1: subject = st.selectbox("Chọn Môn:", ["Toán", "Tiếng Việt", "Tiếng Anh"], key="exam_sub")
        with col2: set_num = st.selectbox("Chọn Mã Đề:", [1, 2, 3], key="exam_set")

        # 2. Kiểm tra Duplicate (Dùng biến student_id vừa fix ở trên)
        if StudentExamForm._check_duplicate(db, student_id, subject, set_num):
            st.warning(f"⚠️ Bạn đã hoàn thành bài thi môn {subject} - Đề {set_num} rồi!")
            return

        st.divider()

        # 3. Tải câu hỏi (Logic cache giữ nguyên)
        exam_key = f"questions_{subject}_{set_num}"
        if exam_key not in st.session_state:
            docs = db.collection("questions")\
                .where("subject", "==", subject)\
                .where("set_number", "==", set_num)\
                .stream()
            st.session_state[exam_key] = [d.to_dict() | {"id": d.id} for d in docs]
        
        questions = st.session_state[exam_key]

        if not questions:
            st.info("📭 Hiện chưa có câu hỏi nào cho đề thi này.")
            return

        # 4. Form làm bài
        with st.form("exam_submission_form"):
            user_answers = {}
            
            for idx, q in enumerate(questions):
                st.markdown(f"#### Câu {idx + 1}:")
                
                # Media
                if q.get('image_path'):
                    img_url = FileUtils.get_signed_url(q['image_path'])
                    if img_url: st.image(img_url, width=400)
                if q.get('audio_path'):
                    aud_url = FileUtils.get_signed_url(q['audio_path'])
                    if aud_url: st.audio(aud_url)

                st.write(q.get('content', ''))
                
                qid = q['id']
                q_type = q.get('type')

                # Inputs
                if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                    user_answers[qid] = st.radio("Chọn đáp án:", q.get('options', []), key=f"ans_{qid}", index=None)
                elif q_type == "Tự luận (Essay)":
                    user_answers[qid] = st.text_area("Bài làm:", key=f"ans_{qid}")
                elif q_type == "Nói (Speaking)":
                    st.write("🎙️ Ghi âm câu trả lời:")
                    audio_bytes = audio_recorder(text="", icon_size="2x", key=f"rec_{qid}")
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/wav")
                        user_answers[qid] = audio_bytes

                st.markdown("---")

            if st.form_submit_button("✅ NỘP BÀI THI", type="primary"):
                # Truyền student_id chuẩn vào hàm xử lý nộp bài
                StudentExamForm._handle_submission(db, student_id, student_info, subject, set_num, questions, user_answers)

    @staticmethod
    def _check_duplicate(db, student_id, subject, set_num):
        docs = db.collection("submissions")\
            .where("student_id", "==", student_id)\
            .where("subject", "==", subject)\
            .where("set_number", "==", set_num)\
            .limit(1).stream()
        return len(list(docs)) > 0

    @staticmethod
    def _handle_submission(db, student_id, student_info, subject, set_num, questions, user_answers):
        # (Logic xử lý nộp bài giữ nguyên, chỉ thay đổi tham số đầu vào)
        with st.spinner("Đang nộp bài..."):
            final_answers_data = {}
            total_score = 0.0
            
            for q in questions:
                qid = q['id']
                user_input = user_answers.get(qid)
                q_type = q.get('type')
                
                ans_data = {
                    "question_content": q.get('content'),
                    "type": q_type,
                    "max_score": 1.0,
                    "score": 0.0,
                    "teacher_comment": ""
                }

                if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                    ans_data["student_choice"] = user_input
                    ans_data["correct_choice"] = q.get("correct_answer")
                    if user_input == q.get("correct_answer"):
                        ans_data["score"] = 1.0
                        total_score += 1.0
                
                elif q_type == "Tự luận (Essay)":
                    ans_data["student_text"] = InputValidator.sanitize(user_input) if user_input else ""
                
                elif q_type == "Nói (Speaking)":
                    if user_input:
                        import io
                        class BytesFile:
                            def __init__(self, data, name):
                                self.getvalue = lambda: data
                                self.name = name
                                self.type = "audio/wav"
                                self.size = len(data)
                        
                        file_obj = BytesFile(user_input, f"{student_id}_{qid}.wav")
                        path = FileUtils.upload_to_storage(file_obj, "submission_recordings")
                        ans_data["audio_path"] = path

                final_answers_data[qid] = ans_data

            submission_payload = {
                "student_id": student_id, # Dùng ID đã fix
                "student_name": student_info.get('full_name', 'Học sinh'),
                "subject": subject,
                "set_number": set_num,
                "submitted_at": firestore.SERVER_TIMESTAMP,
                "status": "pending",
                "final_score": total_score,
                "answers": final_answers_data
            }
            
            db.collection("submissions").add(submission_payload)
            
            st.balloons()
            st.success(f"🎉 Nộp bài thành công! Điểm trắc nghiệm: {total_score}")
            
            if f"questions_{subject}_{set_num}" in st.session_state:
                del st.session_state[f"questions_{subject}_{set_num}"]
            
            time.sleep(2)
            st.rerun()