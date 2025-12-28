"""
UI Components: Forms và interfaces
"""
import streamlit as st
import time
from auth import AuthManager
from config import get_storage  # ← ĐÃ THÊM!
from utils import FileUtils, InputValidator
from models import Question, QuestionRepository, SubmissionRepository
from firebase_admin import firestore

class TeacherLoginForm:
    """Form đăng nhập GV"""
    
    @staticmethod
    def render():
        st.title("👩‍🏫 ĐĂNG NHẬP GIÁO VIÊN")
        
        with st.form("teacher_login"):
            password = st.text_input("Mật khẩu:", type="password")
            
            if st.form_submit_button("Đăng nhập", type="primary"):
                success, msg = AuthManager.authenticate_teacher(password)
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)


class QuestionCreationForm:
    """Form tạo câu hỏi"""
    
    @staticmethod
    def render(db):
        st.subheader("📝 Tạo Câu Hỏi Mới")
        repo = QuestionRepository(db)
        
        with st.form("create_question"):
            col1, col2, col3 = st.columns(3)
            with col1:
                subject = st.selectbox("Môn:", ["Toán", "Tiếng Việt", "Tiếng Anh"])
            with col2:
                set_num = st.selectbox("Mã đề:", [1, 2, 3])
            with col3:
                q_type = st.selectbox("Loại:", [
                    "Trắc nghiệm (MC)",
                    "Nghe (Listening)",
                    "Nói (Speaking)",
                    "Tự luận (Essay)"
                ])
            
            content = st.text_area("Nội dung:", max_chars=1000)
            
            st.markdown("##### 📂 File đính kèm")
            col_a, col_b = st.columns(2)
            
            with col_a:
                img = st.file_uploader("📷 Hình ảnh", type=["jpg", "png"])
            with col_b:
                audio = None
                if q_type in ["Nghe (Listening)", "Trắc nghiệm (MC)"]:
                    audio = st.file_uploader("🎧 Audio", type=["mp3", "wav"])
            
            options = []
            correct = ""
            if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                opts_str = st.text_input("Các lựa chọn (phân cách bằng dấu phẩy):")
                if opts_str:
                    options = [InputValidator.sanitize(x) for x in opts_str.split(",")]
                correct = st.selectbox("Đáp án đúng:", options or ["Chưa nhập"])
            
            if st.form_submit_button("💾 Lưu", type="primary"):
                if not content.strip():
                    st.error("❌ Vui lòng nhập nội dung!")
                    return
                
                with st.spinner("Đang lưu..."):
                    img_path = FileUtils.upload_to_storage(img, "question_images")
                    aud_path = FileUtils.upload_to_storage(audio, "question_audio")
                    
                    question = Question(
                        subject=subject,
                        set_number=set_num,
                        q_type=q_type,
                        content=InputValidator.sanitize(content, 1000),
                        options=options,
                        correct_answer=InputValidator.sanitize(correct),
                        image_path=img_path,
                        audio_path=aud_path
                    )
                    
                    repo.create(question)
                    st.success("✅ Đã tạo câu hỏi!")


class StudentExamForm:
    """Form thi của học sinh"""
    
    @staticmethod
    def render(student, db):
        q_repo = QuestionRepository(db)
        sub_repo = SubmissionRepository(db)
        
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("Môn:", ["Toán", "Tiếng Việt", "Tiếng Anh"])
        with col2:
            set_num = st.selectbox("Mã đề:", [1, 2, 3])
        
        if sub_repo.check_duplicate(student['id'], subject, set_num):
            st.warning("⚠️ Bạn đã nộp bài đề này rồi!")
            return
        
        st.divider()
        questions = q_repo.get_by_exam(subject, set_num)
        
        if not questions:
            st.info("📭 Chưa có câu hỏi.")
            return
        
        with st.form("exam_form"):
            answers = {}
            
            for idx, q in enumerate(questions):
                st.markdown(f"### Câu {idx + 1}")
                
                if q.get('audio_path'):
                    url = FileUtils.get_signed_url(q['audio_path'])
                    if url:
                        st.audio(url)
                
                if q.get('image_path'):
                    url = FileUtils.get_signed_url(q['image_path'])
                    if url:
                        st.image(url, width=400)
                
                st.write(q['content'])
                
                qid = q['id']
                if q['type'] in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                    answers[qid] = st.radio(
                        "Chọn:",
                        q.get('options', []),
                        key=f"q_{qid}",
                        index=None
                    )
                elif q['type'] == "Tự luận (Essay)":
                    answers[qid] = st.text_area("Bài làm:", key=f"q_{qid}", max_chars=2000)
                
                st.markdown("---")
            
            if st.form_submit_button("📤 NỘP BÀI", type="primary"):
                StudentExamForm._submit_exam(
                    student, subject, set_num, answers, questions, db, sub_repo
                )
    
    @staticmethod
    def _submit_exam(student, subject, set_num, answers, questions, db, sub_repo):
        """Xử lý nộp bài"""
        if sub_repo.check_duplicate(student['id'], subject, set_num):
            st.error("❌ Đã nộp rồi!")
            return
        
        with st.spinner("Đang nộp..."):
            correct_answers = {}
            for qid in answers.keys():
                doc = db.collection("questions").document(qid).get()
                if doc.exists:
                    correct_answers[qid] = doc.to_dict()
            
            formatted_answers = {}
            total_score = 0
            
            for qid, user_ans in answers.items():
                q_data = correct_answers.get(qid, {})
                
                ans_obj = {
                    "type": q_data.get('type'),
                    "question_content": q_data.get('content'),
                    "max_score": 1.0,
                    "score": 0,
                    "teacher_comment": ""
                }
                
                if q_data.get('type') in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                    ans_obj["student_choice"] = user_ans
                    ans_obj["correct_choice"] = q_data.get("correct_answer")
                    
                    if user_ans == q_data.get("correct_answer"):
                        ans_obj["score"] = 1.0
                        total_score += 1.0
                
                elif q_data.get('type') == "Tự luận (Essay)":
                    ans_obj["student_text"] = InputValidator.sanitize(user_ans, 2000)
                
                formatted_answers[qid] = ans_obj
            
            submission = {
                "student_id": student['id'],
                "student_name": student['name'],
                "student_class": student.get('class', ''),
                "subject": subject,
                "set_number": set_num,
                "submitted_at": firestore.SERVER_TIMESTAMP,
                "status": "pending",
                "final_score": total_score,
                "answers": formatted_answers
            }
            
            sub_repo.create(submission)
            
            st.balloons()
            st.success(f"✅ Nộp bài thành công! Điểm tạm: {total_score}")
            time.sleep(2)
            st.session_state['student_info'] = None
            st.rerun()