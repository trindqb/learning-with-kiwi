import streamlit as st
from audio_recorder_streamlit import audio_recorder
import firebase_admin
from firebase_admin import credentials, storage, firestore
import time
import uuid
import hashlib
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
# --- UTILS ---
def upload_to_storage(file_obj, folder_name):
    """
    Upload file lên Firebase Storage
    Input: file_obj (từ st.file_uploader), folder_name (ví dụ 'images')
    Output: Đường dẫn lưu trong DB (ví dụ: images/abc.jpg)
    """
    if file_obj is None:
        return None
    
    # 1. Tạo tên file độc nhất (dùng thời gian + mã ngẫu nhiên)
    # Lấy đuôi file (jpg, mp3...)
    file_ext = file_obj.name.split(".")[-1]
    file_name = f"{folder_name}/{int(time.time())}_{str(uuid.uuid4())[:8]}.{file_ext}"
    
    # 2. Upload
    blob = bucket.blob(file_name)
    blob.upload_from_string(file_obj.getvalue(), content_type=file_obj.type)
    
    return file_name

def get_public_url(storage_path):
    """Lấy link tạm (Signed URL) để hiển thị ảnh/audio private"""
    if not storage_path:
        return None
    try:
        blob = bucket.blob(storage_path)
        # Link sống trong 1 giờ (3600s)
        return blob.generate_signed_url(version="v4", expiration=3600)
    except Exception as e:
        return None

# --- 3. GIAO DIỆN GIÁO VIÊN (ADMIN) ---
def teacher_page():
    st.title("👩‍🏫 TRANG QUẢN LÝ CỦA GIÁO VIÊN")
    
    # Ô nhập mật khẩu
    input_password = st.text_input("Nhập mật khẩu quản trị:", type="password")
    
    # Nút đăng nhập
    if st.button("Đăng nhập") or input_password:
        # 1. Băm mật khẩu vừa nhập
        input_hash = hashlib.sha256(input_password.encode()).hexdigest()
        
        # 2. Lấy mã hash chuẩn từ Secrets
        # (Dùng .get để tránh lỗi nếu quên cấu hình)
        stored_hash = st.secrets.get("admin", {}).get("password_hash", "")
        
        # 3. So sánh
        if input_hash == stored_hash:
            st.success("Đăng nhập thành công!")
            # --- HIỂN THỊ NỘI DUNG QUẢN LÝ Ở DƯỚI ĐÂY ---
            # (Copy toàn bộ phần code tạo câu hỏi, upload file... bỏ vào đây)
            
            st.markdown("---")
            st.subheader("📝 Tạo Câu Hỏi Mới")
            # ... (Phần code form tạo câu hỏi cũ của bạn) ...
            st.markdown("---")
            st.subheader("📝 Tạo Câu Hỏi Mới")
            
            with st.form("create_question_form"):
                # 1. Thông tin chung
                c1, c2, c3 = st.columns(3)
                with c1: subject = st.selectbox("Môn thi:", ["Toán", "Tiếng Việt", "Tiếng Anh"])
                with c2: set_num = st.selectbox("Mã đề:", [1, 2, 3])
                with c3: q_type = st.selectbox("Loại câu:", ["Trắc nghiệm (MC)", "Nghe (Listening)", "Nói (Speaking)", "Tự luận (Essay)"])
                
                # 2. Nội dung câu hỏi
                content = st.text_area("Đề bài (Câu hỏi):", placeholder="Ví dụ: Look at the picture and choose...")
                
                # 3. KHU VỰC UPLOAD FILE (MỚI)
                st.markdown("##### 📂 Đính kèm tệp (Nếu có)")
                col_up1, col_up2 = st.columns(2)
                
                with col_up1:
                    # Upload ẢNH (Cho mọi loại câu hỏi)
                    image_file = st.file_uploader("📷 Hình ảnh minh họa (JPG, PNG)", type=["jpg", "png", "jpeg"])
                
                with col_up2:
                    # Upload MP3 (Chỉ hiện nếu là bài Nghe hoặc Trắc nghiệm có nghe)
                    audio_file = None
                    if q_type in ["Nghe (Listening)", "Trắc nghiệm (MC)"]:
                        audio_file = st.file_uploader("🎧 File âm thanh (MP3 < 3MB)", type=["mp3", "wav"])
        
                # 4. Đáp án (Cho trắc nghiệm)
                options = []
                correct_ans = ""
                if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                    st.markdown("##### ✅ Đáp án")
                    opts_str = st.text_input("Các lựa chọn (cách nhau dấu phẩy):", placeholder="Apple, Banana, Orange")
                    if opts_str:
                        options = [x.strip() for x in opts_str.split(",")]
                    correct_ans = st.selectbox("Chọn đáp án ĐÚNG:", options if options else ["Chưa nhập option"])
        
                # NÚT LƯU
                submitted = st.form_submit_button("Lưu Câu Hỏi", type="primary")
                
                if submitted:
                    # Validate file size
                    if audio_file and audio_file.size > 3 * 1024 * 1024:
                        st.error("❌ File MP3 quá nặng (>3MB).")
                        st.stop()
                    
                    with st.spinner("Đang upload file và lưu dữ liệu..."):
                        # A. Upload file lên Firebase Storage
                        img_path = upload_to_storage(image_file, "question_images")
                        aud_path = upload_to_storage(audio_file, "question_audio")
                        
                        # B. Tạo dữ liệu JSON
                        question_data = {
                            "subject": subject,
                            "set_number": set_num,
                            "type": q_type,
                            "content": content,
                            "options": options,
                            "correct_answer": correct_ans,
                            # Lưu đường dẫn storage (không phải link public)
                            "image_path": img_path, 
                            "audio_path": aud_path,
                            "created_at": firestore.SERVER_TIMESTAMP
                        }
                        
                        # C. Đẩy vào Firestore
                        db.collection("questions").add(question_data)
                        st.success("✅ Đã tạo câu hỏi thành công!")
        else:
            if input_password: # Chỉ báo lỗi nếu đã nhập gì đó
                st.error("❌ Sai mật khẩu! Vui lòng thử lại.")
            st.stop() # Dừng chương trình, không hiện nội dung bên dưới

    
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
            st.markdown(f"#### Câu {idx + 1}")
            
            # --- 1. HIỂN THỊ FILE AUDIO (Nếu có) ---
            if q.get('audio_path'):
                audio_url = get_public_url(q['audio_path'])
                if audio_url:
                    st.audio(audio_url)
                else:
                    st.error("Không tải được file nghe.")

            # --- 2. HIỂN THỊ HÌNH ẢNH (Nếu có) ---
            if q.get('image_path'):
                img_url = get_public_url(q['image_path'])
                if img_url:
                    # Hiển thị ảnh chiều rộng vừa phải (400px)
                    st.image(img_url, caption="Hình minh họa", width=400) 
            
            # --- 3. HIỂN THỊ NỘI DUNG VÀ LỰA CHỌN ---
            st.write(q['content'])
            
            # (Phần hiển thị Radio button / Text area / Recorder giữ nguyên như cũ)
            qid = q['id']
            if q['type'] in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                choice = st.radio("Chọn đáp án:", q.get('options', []), key=f"q_{qid}", index=None)
                user_answers[qid] = choice
            
            elif q['type'] == "Nói (Speaking)":
                 st.info("Ghi âm câu trả lời:")
                 audio_bytes = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#3498db", key=f"rec_{qid}")
                 user_answers[qid] = audio_bytes
                 if audio_bytes: st.audio(audio_bytes, format='audio/wav')

            elif q['type'] == "Tự luận (Essay)":
                user_answers[qid] = st.text_area("Bài làm:", key=f"q_{qid}")
            
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
