import streamlit as st
from audio_recorder_streamlit import audio_recorder
import firebase_admin
from firebase_admin import credentials, storage, firestore
import time
import uuid
import hashlib
import re
from datetime import datetime, timedelta

# ========================
# 1. CẤU HÌNH HỆ THỐNG
# ========================
st.set_page_config(page_title="Hệ Thống Thi Trực Tuyến", layout="wide", page_icon="🏫")

# Khởi tạo Firebase
if not firebase_admin._apps:
    key_dict = dict(st.secrets["firebase"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'learning-with-kiwi.firebasestorage.app'
    })

db = firestore.client()
bucket = storage.bucket()

# ========================
# 2. HÀM BẢO MẬT
# ========================

def validate_input(text, max_length=500):
    """Sanitize và validate input từ user"""
    if not text or not isinstance(text, str):
        return ""
    # Loại bỏ ký tự nguy hiểm
    text = re.sub(r'[<>\"\'%;()&+]', '', text)
    return text[:max_length].strip()

def check_teacher_session():
    """Kiểm tra session giáo viên có hợp lệ không"""
    if 'teacher_authenticated' not in st.session_state:
        return False
    
    # Kiểm tra timeout (30 phút)
    if 'teacher_login_time' in st.session_state:
        elapsed = time.time() - st.session_state['teacher_login_time']
        if elapsed > 1800:  # 30 phút
            st.session_state['teacher_authenticated'] = False
            st.warning("⏰ Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.")
            return False
    
    return st.session_state.get('teacher_authenticated', False)

def authenticate_teacher(password):
    """Xác thực giáo viên với rate limiting"""
    # Rate limiting: Tối đa 5 lần thử trong 5 phút
    if 'login_attempts' not in st.session_state:
        st.session_state['login_attempts'] = []
    
    # Xóa các lần thử cũ hơn 5 phút
    current_time = time.time()
    st.session_state['login_attempts'] = [
        t for t in st.session_state['login_attempts'] 
        if current_time - t < 300
    ]
    
    if len(st.session_state['login_attempts']) >= 5:
        st.error("🚫 Quá nhiều lần đăng nhập sai. Vui lòng thử lại sau 5 phút.")
        return False
    
    # Băm và so sánh mật khẩu
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    stored_hash = st.secrets.get("admin", {}).get("password_hash", "")
    
    if input_hash == stored_hash:
        st.session_state['teacher_authenticated'] = True
        st.session_state['teacher_login_time'] = current_time
        st.session_state['login_attempts'] = []
        return True
    else:
        st.session_state['login_attempts'].append(current_time)
        return False

def check_duplicate_submission(student_id, subject, set_number):
    """Kiểm tra học sinh đã nộp bài chưa"""
    existing = db.collection("submissions")\
        .where("student_id", "==", student_id)\
        .where("subject", "==", subject)\
        .where("set_number", "==", set_number)\
        .limit(1)\
        .get()
    
    return len(existing) > 0

def validate_file_upload(file_obj, allowed_types, max_size_mb=3):
    """Validate file upload"""
    if not file_obj:
        return True, ""
    
    # Check extension
    file_ext = file_obj.name.split(".")[-1].lower()
    if file_ext not in allowed_types:
        return False, f"Chỉ chấp nhận file: {', '.join(allowed_types)}"
    
    # Check size
    if file_obj.size > max_size_mb * 1024 * 1024:
        return False, f"File vượt quá {max_size_mb}MB"
    
    return True, ""

def upload_to_storage_secure(file_obj, folder_name):
    """Upload file với validation bảo mật"""
    if not file_obj:
        return None
    
    # Validate file
    allowed_exts = ['jpg', 'jpeg', 'png', 'mp3', 'wav']
    is_valid, error_msg = validate_file_upload(file_obj, allowed_exts, max_size_mb=3)
    
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return None
    
    # Tạo tên file an toàn
    file_ext = file_obj.name.split(".")[-1].lower()
    safe_filename = f"{folder_name}/{int(time.time())}_{str(uuid.uuid4())[:8]}.{file_ext}"
    
    # Upload
    blob = bucket.blob(safe_filename)
    blob.upload_from_string(file_obj.getvalue(), content_type=file_obj.type)
    
    return safe_filename

def get_public_url(storage_path):
    """Lấy signed URL với thời hạn ngắn"""
    if not storage_path:
        return None
    try:
        blob = bucket.blob(storage_path)
        # Giảm thời hạn xuống 15 phút cho bảo mật cao hơn
        return blob.generate_signed_url(version="v4", expiration=900)
    except Exception as e:
        st.error(f"Lỗi tải file: {str(e)}")
        return None

# ========================
# 3. GIAO DIỆN GIÁO VIÊN
# ========================

def teacher_login_page():
    """Trang đăng nhập giáo viên"""
    st.title("👩‍🏫 ĐĂNG NHẬP GIÁO VIÊN")
    
    with st.form("teacher_login"):
        password = st.text_input("Mật khẩu quản trị:", type="password")
        submit = st.form_submit_button("Đăng nhập", type="primary")
        
        if submit:
            if authenticate_teacher(password):
                st.success("✅ Đăng nhập thành công!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Sai mật khẩu!")

def create_question_tab():
    """Tab tạo câu hỏi (đã được bảo mật)"""
    st.subheader("📝 Tạo Câu Hỏi Mới")
    
    with st.form("create_question_form"):
        c1, c2, c3 = st.columns(3)
        with c1: subject = st.selectbox("Môn thi:", ["Toán", "Tiếng Việt", "Tiếng Anh"])
        with c2: set_num = st.selectbox("Mã đề:", [1, 2, 3])
        with c3: q_type = st.selectbox("Loại câu:", ["Trắc nghiệm (MC)", "Nghe (Listening)", "Nói (Speaking)", "Tự luận (Essay)"])
        
        content = st.text_area("Đề bài:", max_chars=1000)
        
        st.markdown("##### 📂 Đính kèm tệp")
        col_up1, col_up2 = st.columns(2)
        
        with col_up1:
            image_file = st.file_uploader("📷 Hình ảnh", type=["jpg", "png", "jpeg"])
        with col_up2:
            audio_file = None
            if q_type in ["Nghe (Listening)", "Trắc nghiệm (MC)"]:
                audio_file = st.file_uploader("🎧 Audio", type=["mp3", "wav"])
        
        options = []
        correct_ans = ""
        if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
            opts_str = st.text_input("Các lựa chọn (cách nhau dấu phẩy):")
            if opts_str:
                options = [validate_input(x) for x in opts_str.split(",")]
            correct_ans = st.selectbox("Đáp án đúng:", options if options else ["Chưa nhập"])
        
        submitted = st.form_submit_button("Lưu Câu Hỏi", type="primary")
        
        if submitted:
            if not content.strip():
                st.error("❌ Vui lòng nhập nội dung câu hỏi!")
                return
            
            with st.spinner("Đang lưu..."):
                # Upload files với validation
                img_path = upload_to_storage_secure(image_file, "question_images")
                aud_path = upload_to_storage_secure(audio_file, "question_audio")
                
                # Sanitize input
                question_data = {
                    "subject": subject,
                    "set_number": set_num,
                    "type": q_type,
                    "content": validate_input(content, 1000),
                    "options": options,
                    "correct_answer": validate_input(correct_ans),
                    "image_path": img_path,
                    "audio_path": aud_path,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "created_by": "admin"  # Thêm audit trail
                }
                
                db.collection("questions").add(question_data)
                st.success("✅ Đã tạo câu hỏi!")

def grading_tab():
    """Tab chấm bài (giữ logic cũ nhưng thêm validation)"""
    st.subheader("💯 Chấm Bài Thi")
    
    c1, c2, c3 = st.columns(3)
    with c1: filter_subject = st.selectbox("Môn:", ["Toán", "Tiếng Việt", "Tiếng Anh"], key="g_sub")
    with c2: filter_set = st.selectbox("Mã đề:", [1, 2, 3], key="g_set")
    with c3: filter_status = st.selectbox("Trạng thái:", ["Tất cả", "pending", "graded"])
    
    if st.button("📂 Tải danh sách"):
        query = db.collection("submissions")\
            .where("subject", "==", filter_subject)\
            .where("set_number", "==", filter_set)\
            .limit(100)  # Giới hạn kết quả
        
        if filter_status != "Tất cả":
            query = query.where("status", "==", filter_status)
        
        docs = query.stream()
        st.session_state['grading_list'] = [doc.to_dict() | {"id": doc.id} for doc in docs]
    
    # Phần còn lại giữ nguyên logic cũ...
    if 'grading_list' in st.session_state and st.session_state['grading_list']:
        submissions = st.session_state['grading_list']
        
        if not submissions:
            st.info("Không tìm thấy bài thi nào.")
        else:
            # Tạo list hiển thị: "Tên HS - Điểm hiện tại - Trạng thái"
            options_map = {f"{s['student_name']} ({s['student_id']}) - {s['status']}": i for i, s in enumerate(submissions)}
            selected_label = st.selectbox("Chọn bài thi cần chấm:", list(options_map.keys()))
            
            # Lấy data bài thi
            selected_sub = submissions[options_map[selected_label]]
            sub_id = selected_sub['id']
            answers = selected_sub['answers'] # Map chứa chi tiết câu trả lời

            st.divider()
            st.markdown(f"### 📝 Đang chấm: {selected_sub['student_name']}")
            st.caption(f"Thời gian nộp: {selected_sub['submitted_at']}")

            # --- BƯỚC 3: FORM CHẤM ĐIỂM CHI TIẾT ---
            with st.form(f"grading_form_{sub_id}"):
                total_new_score = 0.0
                
                # Duyệt qua từng câu trả lời trong Map answers
                # Sort theo key (ID câu hỏi) để hiển thị thứ tự cho đẹp
                sorted_qids = sorted(answers.keys())

                for qid in sorted_qids:
                    ans = answers[qid]
                    q_type = ans.get('type', 'Unknown')
                    
                    st.markdown(f"**Câu hỏi ({q_type}):** {ans.get('question_content', 'Không có nội dung')}")
                    
                    # --- XỬ LÝ HIỂN THỊ THEO LOẠI ---
                    
                    # 1. TRẮC NGHIỆM (Máy đã chấm, GV chỉ xem lại)
                    if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                        col_a, col_b = st.columns(2)
                        with col_a: 
                            st.write(f"HS chọn: **{ans.get('student_choice')}**")
                        with col_b: 
                            st.write(f"Đáp án đúng: `{ans.get('correct_choice')}`")
                        
                        # Cho phép sửa điểm nếu máy chấm sai (ít khi dùng)
                        new_score = st.number_input(f"Điểm câu {qid}:", value=float(ans.get('score', 0)), step=0.25, key=f"score_{qid}")
                        ans['score'] = new_score # Cập nhật vào dict tạm
                    
                    # 2. TỰ LUẬN (GV đọc và chấm)
                    elif q_type == "Tự luận (Essay)":
                        st.text_area("Bài làm của HS:", value=ans.get('student_text', ''), disabled=True)
                        
                        c_score, c_comment = st.columns([1, 3])
                        with c_score:
                            new_score = st.number_input(f"Chấm điểm (Max {ans.get('max_score', 1)}):", value=float(ans.get('score', 0)), step=0.25, key=f"score_{qid}")
                        with c_comment:
                            comment = st.text_input("Lời phê:", value=ans.get('teacher_comment', ''), key=f"cmt_{qid}")
                        
                        ans['score'] = new_score
                        ans['teacher_comment'] = comment

                    # 3. NÓI - SPEAKING (GV nghe và chấm)
                    elif q_type == "Nói (Speaking)":
                        audio_path = ans.get('audio_path')
                        if audio_path:
                            # Lấy link Signed URL để phát
                            audio_url = get_public_url(audio_path)
                            if audio_url:
                                st.audio(audio_url)
                            else:
                                st.error("File lỗi hoặc đã bị xóa.")
                        else:
                            st.warning("Học sinh không ghi âm câu này.")

                        c_score, c_comment = st.columns([1, 3])
                        with c_score:
                            new_score = st.number_input(f"Chấm điểm Nói (Max {ans.get('max_score', 1)}):", value=float(ans.get('score', 0)), step=0.25, key=f"score_{qid}")
                        with c_comment:
                            comment = st.text_input("Nhận xét phát âm/ngữ pháp:", value=ans.get('teacher_comment', ''), key=f"cmt_{qid}")
                            
                        ans['score'] = new_score
                        ans['teacher_comment'] = comment
                    
                    total_new_score += ans['score']
                    st.markdown("---")

                # --- BƯỚC 4: LƯU TỔNG KẾT ---
                st.subheader(f"📊 Tổng điểm: {total_new_score}")
                
                if st.form_submit_button("Lưu Kết Quả Chấm", type="primary"):
                    with st.spinner("Đang lưu điểm số..."):
                        # Cập nhật Firestore
                        db.collection("submissions").document(sub_id).update({
                            "answers": answers, # Lưu lại toàn bộ answers đã sửa điểm/comment
                            "final_score": total_new_score,
                            "status": "graded"  # Đổi trạng thái thành Đã chấm
                        })
                        st.success(f"Đã chấm xong cho {selected_sub['student_name']}! Điểm: {total_new_score}")
                        
                        # Update lại list bên ngoài để hiển thị trạng thái mới ngay lập tức
                        selected_sub['status'] = 'graded'
                        selected_sub['final_score'] = total_new_score
                        time.sleep(1)
                        st.rerun()
def edit_question_tab():
    st.subheader("✏️ Chỉnh Sửa Câu Hỏi Đã Tạo")
    
    # BƯỚC 1: LỌC CÂU HỎI ĐỂ TÌM
    col1, col2 = st.columns(2)
    with col1:
        find_subject = st.selectbox("Chọn Môn cần sửa:", ["Toán", "Tiếng Việt", "Tiếng Anh"], key="find_sub")
    with col2:
        find_set = st.selectbox("Chọn Mã đề cần sửa:", [1, 2, 3], key="find_set")
    
    if st.button("🔍 Tìm kiếm câu hỏi"):
        # Lưu kết quả tìm kiếm vào session state để không bị mất khi reload
        questions_ref = db.collection("questions")\
            .where("subject", "==", find_subject)\
            .where("set_number", "==", find_set)\
            .stream()
        
        # Chuyển thành list và lưu ID
        st.session_state['edit_list'] = [doc.to_dict() | {"id": doc.id} for doc in questions_ref]

    # BƯỚC 2: HIỂN THỊ DANH SÁCH ĐỂ CHỌN
    if 'edit_list' in st.session_state and st.session_state['edit_list']:
        q_list = st.session_state['edit_list']
        
        if len(q_list) == 0:
            st.warning("Không tìm thấy câu hỏi nào.")
        else:
            # Tạo dictionary để mapping tên hiển thị -> ID câu hỏi
            # Hiển thị: "Câu 1: Nội dung..." (tạm tính theo index)
            q_options = {f"({q['type']}) {q['content'][:50]}...": idx for idx, q in enumerate(q_list)}
            
            selected_label = st.selectbox("Chọn câu hỏi muốn sửa:", list(q_options.keys()))
            
            # Lấy data câu hỏi được chọn
            selected_index = q_options[selected_label]
            q_data = q_list[selected_index]
            q_id = q_data['id']

            st.markdown("---")
            st.write(f"Đang sửa ID: `{q_id}`")

            # BƯỚC 3: FORM SỬA DỮ LIỆU (PRE-FILLED)
            with st.form(f"edit_form_{q_id}"):
                # Load dữ liệu cũ vào các ô input (dùng tham số value=...)
                new_content = st.text_area("Nội dung câu hỏi:", value=q_data.get('content', ''))
                
                # Xử lý options (List -> String)
                old_opts = ", ".join(q_data.get('options', []))
                new_opts_str = st.text_input("Các lựa chọn (cách nhau dấu phẩy):", value=old_opts)
                
                new_correct = st.text_input("Đáp án đúng:", value=q_data.get('correct_answer', ''))
                
                # --- XỬ LÝ FILE (ẢNH & AUDIO) ---
                st.markdown("##### 📂 Cập nhật file (Bỏ qua nếu không muốn đổi)")
                
                # Ảnh
                if q_data.get('image_path'):
                    st.caption(f"Ảnh hiện tại: {q_data['image_path']}")
                new_image = st.file_uploader("Thay ảnh mới (JPG/PNG):", type=["jpg", "png", "jpeg"])
                
                # Audio
                if q_data.get('audio_path'):
                    st.caption(f"Audio hiện tại: {q_data['audio_path']}")
                new_audio = st.file_uploader("Thay audio mới (MP3):", type=["mp3", "wav"])

                # NÚT CẬP NHẬT
                if st.form_submit_button("Lưu Thay Đổi", type="primary"):
                    update_data = {
                        "content": new_content,
                        "options": [x.strip() for x in new_opts_str.split(",")] if new_opts_str else [],
                        "correct_answer": new_correct
                    }
                    
                    with st.spinner("Đang cập nhật..."):
                        # Logic Upload file mới (nếu người dùng có chọn file)
                        if new_image:
                            # Upload file mới và lấy đường dẫn mới
                            new_img_path = upload_to_storage(new_image, "question_images")
                            update_data["image_path"] = new_img_path
                            # (Nâng cao: Có thể code thêm đoạn xóa file cũ trên Storage để tiết kiệm dung lượng)
                        
                        if new_audio:
                            new_aud_path = upload_to_storage(new_audio, "question_audio")
                            update_data["audio_path"] = new_aud_path

                        # Lệnh Update của Firestore
                        db.collection("questions").document(q_id).update(update_data)
                        
                        st.success("✅ Đã sửa thành công! Vui lòng bấm 'Tìm kiếm' lại để thấy thay đổi.")
                        # Xóa cache để reload lại list
                        del st.session_state['edit_list']
                        time.sleep(1)
                        st.rerun()

def teacher_page():
    """Trang chính của giáo viên"""
    # Kiểm tra session
    if not check_teacher_session():
        teacher_login_page()
        return
    
    st.title("👩‍🏫 QUẢN LÝ GIÁO VIÊN")
    
    # Nút logout
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🚪 Đăng xuất"):
            st.session_state['teacher_authenticated'] = False
            st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["➕ Tạo Câu Hỏi", "✏️ Sửa Câu Hỏi", "💯 Chấm Bài"])
    
    with tab1:
        create_question_tab()
    with tab2:
        edit_question_tab()
    with tab3:
        grading_tab()

# ========================
# 4. GIAO DIỆN HỌC SINH
# ========================

def student_page():
    """Trang học sinh với bảo mật nâng cao"""
    st.title("✍️ KHU VỰC THI HỌC SINH")
    
    if 'student_info' not in st.session_state:
        st.session_state['student_info'] = None
    
    # ĐĂNG NHẬP
    if not st.session_state['student_info']:
        st.subheader("Đăng nhập")
        
        with st.form("student_login"):
            student_code = st.text_input("Mã số học sinh:").upper().strip()
            submit = st.form_submit_button("Vào thi")
            
            if submit:
                # Validate format
                if not re.match(r'^HS\d{3,6}$', student_code):
                    st.error("❌ Mã số không hợp lệ! (Ví dụ: HS001)")
                    return
                
                # Kiểm tra trong DB
                student_ref = db.collection("students").document(student_code).get()
                if student_ref.exists:
                    st.session_state['student_info'] = student_ref.to_dict()
                    st.session_state['student_info']['id'] = student_code
                    st.session_state['student_login_time'] = time.time()
                    st.rerun()
                else:
                    st.error("❌ Mã số không tồn tại!")
        return
    
    # CHỌN ĐỀ THI
    student = st.session_state['student_info']
    st.success(f"Xin chào: **{student['name']}** - Lớp: {student.get('class', 'N/A')}")
    
    # Nút đăng xuất
    if st.button("🚪 Đăng xuất"):
        st.session_state['student_info'] = None
        st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        subject_choice = st.selectbox("Môn thi:", ["Toán", "Tiếng Việt", "Tiếng Anh"])
    with col2:
        set_choice = st.selectbox("Mã đề:", [1, 2, 3])
    
    # Kiểm tra đã nộp bài chưa
    if check_duplicate_submission(student['id'], subject_choice, set_choice):
        st.warning("⚠️ Bạn đã nộp bài cho đề thi này rồi!")
        return
    
    st.divider()
    
    # LẤY CÂU HỎI (Không lộ đáp án)
    questions_ref = db.collection("questions")\
        .where("subject", "==", subject_choice)\
        .where("set_number", "==", set_choice)\
        .limit(50)\
        .stream()
    
    questions_list = []
    for doc in questions_ref:
        q_data = doc.to_dict()
        # XÓA đáp án đúng khỏi dữ liệu gửi về client
        q_safe = {
            "id": doc.id,
            "type": q_data['type'],
            "content": q_data['content'],
            "options": q_data.get('options', []),
            "image_path": q_data.get('image_path'),
            "audio_path": q_data.get('audio_path')
        }
        questions_list.append(q_safe)
    
    if not questions_list:
        st.info("📭 Chưa có câu hỏi.")
        return
    
    # FORM LÀM BÀI
    with st.form("exam_submission"):
        user_answers = {}
        
        for idx, q in enumerate(questions_list):
            st.markdown(f"#### Câu {idx + 1}")
            
            # Audio
            if q.get('audio_path'):
                audio_url = get_public_url(q['audio_path'])
                if audio_url:
                    st.audio(audio_url)
            
            # Hình ảnh
            if q.get('image_path'):
                img_url = get_public_url(q['image_path'])
                if img_url:
                    st.image(img_url, width=400)
            
            st.write(q['content'])
            
            qid = q['id']
            if q['type'] in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                choice = st.radio("Chọn:", q.get('options', []), key=f"q_{qid}", index=None)
                user_answers[qid] = choice
            
            elif q['type'] == "Nói (Speaking)":
                audio_bytes = audio_recorder(text="", key=f"rec_{qid}")
                user_answers[qid] = audio_bytes
                if audio_bytes:
                    st.audio(audio_bytes)
            
            elif q['type'] == "Tự luận (Essay)":
                user_answers[qid] = st.text_area("Bài làm:", key=f"q_{qid}", max_chars=2000)
            
            st.markdown("---")
        
        submit_exam = st.form_submit_button("NỘP BÀI THI", type="primary")
        
        if submit_exam:
            # Kiểm tra lại duplicate
            if check_duplicate_submission(student['id'], subject_choice, set_choice):
                st.error("❌ Bạn đã nộp bài rồi!")
                return
            
            with st.spinner("Đang nộp bài..."):
                # Lấy đáp án đúng từ server để chấm
                correct_answers = {}
                for q_id in user_answers.keys():
                    q_doc = db.collection("questions").document(q_id).get()
                    if q_doc.exists:
                        correct_answers[q_id] = q_doc.to_dict()
                
                # Xử lý câu trả lời
                formatted_answers = {}
                total_score = 0
                
                for qid, user_resp in user_answers.items():
                    q_data = correct_answers.get(qid, {})
                    
                    ans_data = {
                        "type": q_data.get('type'),
                        "question_content": q_data.get('content'),
                        "max_score": 1.0,
                        "score": 0,
                        "teacher_comment": ""
                    }
                    
                    # Xử lý theo loại
                    if q_data.get('type') in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                        ans_data["student_choice"] = user_resp
                        ans_data["correct_choice"] = q_data.get("correct_answer")
                        
                        if user_resp == q_data.get("correct_answer"):
                            ans_data["score"] = 1.0
                            total_score += 1.0
                    
                    elif q_data.get('type') == "Tự luận (Essay)":
                        ans_data["student_text"] = validate_input(user_resp, 2000)
                    
                    elif q_data.get('type') == "Nói (Speaking)":
                        if user_resp:
                            path = f"recordings/{student['id']}_{subject_choice}_{set_choice}_{qid}.wav"
                            blob = bucket.blob(path)
                            blob.upload_from_string(user_resp, content_type='audio/wav')
                            ans_data["audio_path"] = path
                    
                    formatted_answers[qid] = ans_data
                
                # Lưu bài thi
                submission_data = {
                    "student_id": student['id'],
                    "student_name": student['name'],
                    "student_class": student.get('class', ''),
                    "subject": subject_choice,
                    "set_number": set_choice,
                    "submitted_at": firestore.SERVER_TIMESTAMP,
                    "status": "pending",
                    "final_score": total_score,
                    "answers": formatted_answers
                }
                
                db.collection("submissions").add(submission_data)
                
                st.balloons()
                st.success(f"✅ Nộp bài thành công! Điểm tạm: {total_score}")
                time.sleep(2)
                st.session_state['student_info'] = None
                st.rerun()

# ========================
# 5. MAIN ROUTER
# ========================
role = st.sidebar.radio("Vai trò:", ["Học sinh", "Giáo viên"])

if role == "Giáo viên":
    teacher_page()
else:
    student_page()