"""Giao diện chấm bài"""
import streamlit as st
import time
from config import get_db
from utils import FileUtils

class GradingInterface:
    @staticmethod
    def render():
        st.subheader("💯 Chấm Bài")
        db = get_db()
        
        # Bộ lọc
        col1, col2, col3 = st.columns(3)
        with col1: filter_subject = st.selectbox("Môn:", ["Toán", "Tiếng Việt", "Tiếng Anh"], key="grade_sub")
        with col2: filter_set = st.selectbox("Mã đề:", [1, 2, 3], key="grade_set")
        with col3: filter_status = st.selectbox("Trạng thái:", ["Tất cả", "pending", "graded"], key="grade_status")
        
        if st.button("🔄 Tải bài nộp"):
            query = db.collection("submissions")\
                .where("subject", "==", filter_subject)\
                .where("set_number", "==", filter_set)\
                .limit(100)
            
            if filter_status != "Tất cả":
                query = query.where("status", "==", filter_status)
            
            docs = query.stream()
            st.session_state['grading_list'] = [d.to_dict() | {"id": d.id} for d in docs]
            
        if st.session_state.get('grading_list'):
            subs = st.session_state['grading_list']
            
            if not subs:
                st.info("Không tìm thấy bài thi nào.")
            else:
                options_map = {f"{s['student_name']} ({s['student_id']}) - {s['status']}": i for i, s in enumerate(subs)}
                selected_label = st.selectbox("Chọn bài thi cần chấm:", list(options_map.keys()))
                selected_sub = subs[options_map[selected_label]]
                sub_id = selected_sub['id']
                answers = selected_sub.get('answers', {})
                
                st.divider()
                st.markdown(f"### 📝 Đang chấm: {selected_sub['student_name']}")
                st.caption(f"Thời gian nộp: {selected_sub.get('submitted_at', 'N/A')}")
                
                with st.form(f"grading_form_{sub_id}"):
                    total_new_score = 0.0
                    sorted_qids = sorted(answers.keys())
                    
                    for qid in sorted_qids:
                        ans = answers[qid]
                        q_type = ans.get('type', 'Unknown')
                        
                        st.markdown(f"**Câu hỏi ({q_type}):** {ans.get('question_content', 'Không có nội dung')}")
                        
                        # TRẮC NGHIỆM
                        if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                            col_a, col_b = st.columns(2)
                            with col_a: st.write(f"HS chọn: **{ans.get('student_choice')}**")
                            with col_b: st.write(f"Đáp án đúng: `{ans.get('correct_choice')}`")
                            
                            new_score = st.number_input(f"Điểm câu {qid}:", value=float(ans.get('score', 0)), step=0.25, key=f"score_{qid}")
                            ans['score'] = new_score
                        
                        # TỰ LUẬN
                        elif q_type == "Tự luận (Essay)":
                            st.text_area("Bài làm của HS:", value=ans.get('student_text', ''), disabled=True, key=f"view_{qid}")
                            
                            c_score, c_comment = st.columns([1, 3])
                            with c_score:
                                new_score = st.number_input(f"Chấm điểm (Max {ans.get('max_score', 1)}):", value=float(ans.get('score', 0)), step=0.25, key=f"score_{qid}")
                            with c_comment:
                                comment = st.text_input("Lời phê:", value=ans.get('teacher_comment', ''), key=f"cmt_{qid}")
                            
                            ans['score'] = new_score
                            ans['teacher_comment'] = comment
                        
                        # NÓI (SPEAKING)
                        elif q_type == "Nói (Speaking)":
                            audio_path = ans.get('audio_path')
                            if audio_path:
                                audio_url = FileUtils.get_signed_url(audio_path)
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
                    
                    st.subheader(f"📊 Tổng điểm: {total_new_score}")
                    
                    if st.form_submit_button("Lưu Kết Quả Chấm", type="primary"):
                        with st.spinner("Đang lưu điểm số..."):
                            db.collection("submissions").document(sub_id).update({
                                "answers": answers,
                                "final_score": total_new_score,
                                "status": "graded"
                            })
                            st.success(f"Đã chấm xong cho {selected_sub['student_name']}! Điểm: {total_new_score}")
                            selected_sub['status'] = 'graded'
                            selected_sub['final_score'] = total_new_score
                            time.sleep(1)
                            st.rerun()
