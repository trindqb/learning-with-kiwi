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
        'storageBucket': 'learning-with-kiwi.firebasestorage.app' # <--- Thay đúng tên bucket
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
def grading_tab():
    st.subheader("💯 Chấm Bài Thi")

    # --- BƯỚC 1: LỌC DANH SÁCH BÀI THI ---
    c1, c2, c3 = st.columns(3)
    with c1: filter_subject = st.selectbox("Môn thi:", ["Toán", "Tiếng Việt", "Tiếng Anh"], key="grade_sub")
    with c2: filter_set = st.selectbox("Mã đề:", [1, 2, 3], key="grade_set")
    with c3: filter_status = st.selectbox("Trạng thái:", ["Tất cả", "Chưa chấm (pending)", "Đã chấm (graded)"])

    if st.button("📂 Tải danh sách bài thi"):
        # Query Firestore
        query = db.collection("submissions")\
            .where("subject", "==", filter_subject)\
            .where("set_number", "==", filter_set)
        
        if filter_status == "Chưa chấm (pending)":
            query = query.where("status", "==", "pending")
        elif filter_status == "Đã chấm (graded)":
            query = query.where("status", "==", "graded")
            
        docs = query.stream()
        # Lưu vào session state
        st.session_state['grading_list'] = [doc.to_dict() | {"id": doc.id} for doc in docs]

    # --- BƯỚC 2: CHỌN HỌC SINH ĐỂ CHẤM ---
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
# --- 3. GIAO DIỆN GIÁO VIÊN (ADMIN) ---
def create_question_tab():
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
            tab1, tab2, tab3 = st.tabs(["➕ Tạo Câu Hỏi", "✏️ Sửa Câu Hỏi", "💯 Chấm Bài Thi"])

            with tab1:
                # (Gọi hàm tạo câu hỏi cũ)
                create_question_tab() # Bạn nên tách code cũ ra thành hàm này cho gọn
        
            with tab2:
                edit_question_tab() 
        
            with tab3:
                grading_tab() # <--- Tab mới thêm vào đây
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
