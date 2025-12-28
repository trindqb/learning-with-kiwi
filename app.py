import streamlit as st
from audio_recorder_streamlit import audio_recorder
import firebase_admin
from firebase_admin import credentials, storage, firestore
import time

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Hệ Thống Thi Trực Tuyến", layout="wide", page_icon="🏫")

# Kết nối Firebase (Dùng Secrets)
if not firebase_admin._apps:
    key_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'TEN-PROJECT-CUA-BAN.appspot.com' # <--- Thay đúng tên bucket
    })

db = firestore.client()
bucket = storage.bucket()

# --- 2. CÁC HÀM HỖ TRỢ (UTILS) ---

def upload_file_to_storage(file_obj, path):
    """Upload file lên Firebase Storage và trả về đường dẫn"""
    blob = bucket.blob(path)
    blob.upload_from_string(file_obj.getvalue(), content_type=file_obj.type)
    # Trả về đường dẫn để lưu vào DB (Không cần public URL để bảo mật)
    return path

def get_audio_url(path):
    """Lấy URL tạm thời (có hạn) để phát file private"""
    blob = bucket.blob(path)
    return blob.generate_signed_url(version="v4", expiration=3600)

# --- 3. GIAO DIỆN GIÁO VIÊN (ADMIN) ---
def teacher_page():
    st.title("👩‍🏫 TRANG QUẢN LÝ CỦA GIÁO VIÊN")
    
    # Bảo mật đơn giản bằng mật khẩu
    password = st.text_input("Nhập mật khẩu quản trị:", type="password")
    if password != "admin123": # Thay mật khẩu của bạn vào đây
        st.warning("Vui lòng nhập đúng mật khẩu để thao tác.")
        return

    st.markdown("---")
    st.subheader("📝 Tạo Câu Hỏi Mới")
    
    with st.form("create_question_form"):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("Môn thi:", ["Toán", "Tiếng Việt", "Tiếng Anh"])
            set_num = st.selectbox("Mã đề (Bộ đề):", [1, 2, 3])
        with col2:
            q_type = st.selectbox("Loại câu hỏi:", ["Trắc nghiệm (MC)", "Nghe (Listening)", "Nói (Speaking)", "Tự luận (Essay)"])
        
        content = st.text_area("Nội dung câu hỏi:", placeholder="Nhập đề bài vào đây...")
        
        # Logic riêng cho từng loại câu hỏi
        options = []
        correct_ans = ""
        audio_path = ""
        
        if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
            st.write("Nhập các đáp án lựa chọn (cách nhau bởi dấu phẩy):")
            opts_str = st.text_input("Ví dụ: 10, 15, 20, 25", key="opts")
            if opts_str:
                options = [x.strip() for x in opts_str.split(",")]
            correct_ans = st.text_input("Đáp án đúng (Copy y hệt 1 trong các lựa chọn trên):")
        
        uploaded_file = None
        if q_type == "Nghe (Listening)":
            uploaded_file = st.file_uploader("Upload file nghe (MP3 < 3MB):", type=["mp3"])
            
        submitted = st.form_submit_button("Lưu Câu Hỏi")
        
        if submitted:
            # Kiểm tra file size
            if uploaded_file and uploaded_file.size > 3 * 1024 * 1024:
                st.error("❌ File quá lớn! Vui lòng chọn file < 3MB.")
            else:
                with st.spinner("Đang lưu vào cơ sở dữ liệu..."):
                    # 1. Upload Audio nếu có
                    if uploaded_file:
                        timestamp = int(time.time())
                        fname = f"audio_de_thi/{subject}_de{set_num}_{timestamp}.mp3"
                        audio_path = upload_file_to_storage(uploaded_file, fname)
                    
                    # 2. Lưu câu hỏi vào Firestore
                    # Lưu ý: Không hardcode, lưu thẳng vào DB
                    question_data = {
                        "subject": subject,
                        "set_number": set_num,
                        "type": q_type,
                        "content": content,
                        "options": options,
                        "correct_answer": correct_ans, # Lưu để chấm, nhưng HS không thấy
                        "audio_path": audio_path,
                        "created_at": firestore.SERVER_TIMESTAMP
                    }
                    db.collection("questions").add(question_data)
                    st.success("✅ Đã thêm câu hỏi thành công!")

# --- 4. GIAO DIỆN HỌC SINH (USER) ---
def student_page():
    st.title("✍️ KHU VỰC THI HỌC SINH")
    
    # Session state để quản lý đăng nhập
    if 'student_info' not in st.session_state:
        st.session_state['student_info'] = None

    # --- BƯỚC 1: ĐĂNG NHẬP ---
    if not st.session_state['student_info']:
        st.subheader("Đăng nhập")
        student_code = st.text_input("Nhập MÃ SỐ HỌC SINH (Ví dụ: HS001):")
        
        if st.button("Vào thi"):
            # Check mã số trong Firestore
            student_ref = db.collection("students").document(student_code).get()
            if student_ref.exists:
                st.session_state['student_info'] = student_ref.to_dict()
                st.session_state['student_info']['id'] = student_code
                st.rerun()
            else:
                st.error("Mã số không tồn tại! Vui lòng liên hệ giáo viên.")
        
        # Hướng dẫn tạo mã nhanh cho bạn test (Xóa khi deploy thật)
        with st.expander("Dành cho Admin (Tạo mã test)"):
             if st.button("Tạo mã HS001 mẫu"):
                 db.collection("students").document("HS001").set({"name": "Học Sinh Mẫu", "class": "4A"})
                 st.success("Đã tạo HS001")
        return

    # --- BƯỚC 2: CHỌN ĐỀ THI ---
    student = st.session_state['student_info']
    st.success(f"Xin chào: **{student['name']}** - Lớp: {student['class']}")
    
    col1, col2 = st.columns(2)
    with col1:
        subject_choice = st.selectbox("Chọn Môn Thi:", ["Toán", "Tiếng Việt", "Tiếng Anh"])
    with col2:
        set_choice = st.selectbox("Chọn Mã Đề:", [1, 2, 3])
    
    st.divider()

    # --- BƯỚC 3: LẤY CÂU HỎI TỪ DB ---
    # Query Firestore: Lấy câu hỏi theo Môn và Mã đề
    questions_ref = db.collection("questions")\
        .where("subject", "==", subject_choice)\
        .where("set_number", "==", set_choice)\
        .stream()
    
    questions_list = [doc.to_dict() | {"id": doc.id} for doc in questions_ref]

    if not questions_list:
        st.info("📭 Chưa có câu hỏi nào cho bộ đề này.")
        return

    # Form làm bài
    with st.form("exam_submission"):
        user_answers = {}
        
        for idx, q in enumerate(questions_list):
            st.markdown(f"**Câu {idx + 1}:** {q['content']}")
            
            # Xử lý hiển thị theo loại
            if q['type'] == "Nghe (Listening)" and q.get('audio_path'):
                # Lấy link file nghe
                try:
                    audio_url = get_audio_url(q['audio_path'])
                    st.audio(audio_url)
                except:
                    st.error("Lỗi tải file nghe.")

            if q['type'] in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                # Trắc nghiệm
                choice = st.radio(
                    "Chọn đáp án:", 
                    q['options'], 
                    key=f"q_{q['id']}",
                    index=None
                )
                user_answers[q['id']] = choice
                
            elif q['type'] == "Tự luận (Essay)":
                ans = st.text_area("Bài làm:", key=f"q_{q['id']}")
                user_answers[q['id']] = ans

            # Lưu ý: Phần Speaking cần xử lý ngoài form (như bài trước)
            # Để đơn giản trong ví dụ này, mình tập trung vào cơ chế DB
            
            st.markdown("---")
        
        submit_exam = st.form_submit_button("NỘP BÀI THI")
        
        if submit_exam:
            with st.spinner("Đang nộp bài..."):
                # 1. Chuẩn bị cấu trúc dữ liệu answers
                formatted_answers = {}
                total_auto_score = 0
                
                # Duyệt qua từng câu hỏi trong đề thi (questions_list đã lấy từ DB về)
                for q in questions_list:
                    qid = q['id'] # ID câu hỏi từ Firestore
                    user_response = user_answers.get(qid) # Cái HS chọn/nhập/ghi âm
                    
                    # Cấu trúc chung cho 1 câu trả lời
                    ans_data = {
                        "type": q['type'],
                        "question_content": q['content'], # Lưu lại đề phòng đề bị sửa sau này
                        "max_score": 1.0, # Giả sử mỗi câu 1 điểm (hoặc lấy từ DB nếu có field points)
                        "score": 0,       # Điểm đạt được
                        "teacher_comment": ""
                    }
        
                    # XỬ LÝ THEO LOẠI
                    if q['type'] in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                        ans_data["student_choice"] = user_response
                        ans_data["correct_choice"] = q.get("correct_answer")
                        
                        # Chấm điểm tự động luôn
                        if user_response == q.get("correct_answer"):
                            ans_data["score"] = 1.0
                            total_auto_score += 1.0
                        else:
                            ans_data["score"] = 0
        
                    elif q['type'] == "Tự luận (Essay)":
                        ans_data["student_text"] = user_response
                        ans_data["score"] = 0 # Chờ GV chấm
        
                    elif q['type'] == "Nói (Speaking)":
                        # user_response lúc này là bytes (dữ liệu âm thanh)
                        if user_response:
                            # Upload file lên Storage
                            timestamp = int(time.time())
                            # Path: student_recordings/MãHS_Môn_MãĐề_CauHoi.wav
                            path = f"student_recordings/{student['id']}_{subject_choice}_De{set_choice}_{qid}.wav"
                            blob = bucket.blob(path)
                            blob.upload_from_string(user_response, content_type='audio/wav')
                            
                            ans_data["audio_path"] = path # Chỉ lưu đường dẫn
                        else:
                            ans_data["audio_path"] = None
                        ans_data["score"] = 0 # Chờ GV chấm
        
                    # Lưu vào map tổng
                    formatted_answers[qid] = ans_data
        
                # 2. Tạo gói dữ liệu Submission
                submission_data = {
                    "student_id": student['id'],
                    "student_name": student['name'],
                    "student_class": student.get('class', ''),
                    "subject": subject_choice,
                    "set_number": set_choice,
                    "submitted_at": firestore.SERVER_TIMESTAMP,
                    "status": "pending", # Trạng thái chờ chấm
                    "final_score": total_auto_score, # Điểm tạm tính (trắc nghiệm)
                    "answers": formatted_answers
                }
        
                # 3. Đẩy lên Firestore
                db.collection("submissions").add(submission_data)
                
                st.balloons()
                st.success(f"✅ Nộp bài thành công! Điểm trắc nghiệm tạm tính: {total_auto_score}")

# --- 5. ĐIỀU HƯỚNG CHÍNH (MAIN ROUTER) ---
# Sidebar để chọn chế độ
role = st.sidebar.radio("Chọn vai trò:", ["Học sinh", "Giáo viên"])

if role == "Giáo viên":
    teacher_page()
else:
    student_page()
