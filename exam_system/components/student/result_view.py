"""
Giao diện xem kết quả thi (Advanced Dashboard)
"""
import streamlit as st
import pandas as pd
from config import get_db
from utils import FileUtils
from firebase_admin import firestore

class ResultView:
    @staticmethod
    def render(student_info):
        st.subheader(f"📊 Hồ Sơ Học Tập: {student_info.get('full_name')}")
        db = get_db()
        # .order_by("submitted_at", direction=firestore.Query.DESCENDING)\
        # 1. TẢI DỮ LIỆU
        submissions_ref = db.collection("submissions")\
            .where("student_id", "==", student_info['student_code'])\
            .stream()
            
        submissions = [d.to_dict() | {"id": d.id} for d in submissions_ref]
        
        if not submissions:
            st.info("👋 Bạn chưa có bài thi nào. Hãy vào mục 'Làm bài thi' để bắt đầu nhé!")
            return

        # 2. BỘ LỌC & THỐNG KÊ (DASHBOARD)
        # Chuyển đổi sang DataFrame để dễ tính toán
        df = pd.DataFrame(submissions)
        df['score_display'] = df['final_score'].fillna(0) # Xử lý bài chưa chấm
        
        # Bộ lọc Sidebar (hoặc Top bar)
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            selected_subject = st.selectbox("📚 Môn học:", ["Tất cả"] + list(df['subject'].unique()))
        with col_filter2:
            selected_status = st.selectbox("📌 Trạng thái:", ["Tất cả", "graded", "pending"], format_func=lambda x: "Đã chấm" if x == "graded" else "Chờ chấm" if x == "pending" else "Tất cả")

        # Áp dụng lọc
        filtered_df = df.copy()
        filtered_data = submissions
        
        if selected_subject != "Tất cả":
            filtered_df = filtered_df[filtered_df['subject'] == selected_subject]
            filtered_data = [s for s in filtered_data if s['subject'] == selected_subject]
            
        if selected_status != "Tất cả":
            filtered_df = filtered_df[filtered_df['status'] == selected_status]
            filtered_data = [s for s in filtered_data if s['status'] == selected_status]

        # --- METRICS SECTION ---
        st.markdown("### 📈 Tổng quan")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Tổng số bài thi", len(filtered_df))
        with m2:
            avg_score = filtered_df[filtered_df['status'] == 'graded']['final_score'].mean()
            st.metric("Điểm trung bình", f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A")
        with m3:
            completed = len(filtered_df[filtered_df['status'] == 'graded'])
            st.metric("Đã hoàn thành chấm", f"{completed}/{len(filtered_df)}")

        # --- CHART SECTION ---
        if not filtered_df.empty and selected_status != "pending":
            st.markdown("##### Biểu đồ điểm số")
            chart_data = filtered_df[filtered_df['status'] == 'graded'][['subject', 'set_number', 'final_score']]
            if not chart_data.empty:
                chart_data['Exam Label'] = chart_data['subject'] + " - Đề " + chart_data['set_number'].astype(str)
                st.bar_chart(chart_data.set_index('Exam Label')['final_score'], color="#4CAF50")

        st.divider()

        # 3. CHI TIẾT TỪNG BÀI THI
        st.markdown("### 📑 Chi tiết bài làm")
        
        for sub in filtered_data:
            ResultView._render_submission_card(sub)

    @staticmethod
    def _render_submission_card(submission):
        """Hiển thị Card chi tiết cho từng bài thi"""
        status = submission.get('status')
        score = submission.get('final_score', 0)
        subject = submission.get('subject')
        set_num = submission.get('set_number')
        
        # Tiêu đề Card: Màu sắc dựa trên trạng thái & điểm số
        status_icon = "🟢" if status == 'graded' else "⏳"
        status_text = "Đã có điểm" if status == 'graded' else "Đang chờ giáo viên chấm"
        
        header_color = "green" if score >= 5 else "red" if status == 'graded' else "gray"
        
        with st.expander(f"{status_icon} {subject} - Đề {set_num} | Điểm: :{header_color}[{score}/10]"):
            
            # Header thông tin bài thi
            c1, c2 = st.columns([2, 1])
            with c1:
                st.caption(f"Thời gian nộp: {submission.get('submitted_at')}")
                st.write(f"**Trạng thái:** {status_text}")
            with c2:
                # Hiển thị Badge điểm số to
                if status == 'graded':
                    st.markdown(
                        f"""
                        <div style="text-align: center; border: 2px solid {header_color}; border-radius: 10px; padding: 5px;">
                            <h1 style="color:{header_color}; margin:0;">{score}</h1>
                            <small>ĐIỂM TỔNG KẾT</small>
                        </div>
                        """, unsafe_allow_html=True
                    )
            
            st.markdown("---")
            
            # --- REVIEW CÂU HỎI ---
            answers = submission.get('answers', {})
            # Sắp xếp theo key câu hỏi để hiển thị đúng thứ tự
            sorted_qids = sorted(answers.keys())
            
            for qid in sorted_qids:
                ans = answers[qid]
                ResultView._render_question_detail(qid, ans, status)

    @staticmethod
    def _render_question_detail(qid, ans, status):
        """Render từng câu hỏi kèm feedback"""
        q_type = ans.get('type', 'Unknown')
        student_score = ans.get('score', 0)
        max_score = ans.get('max_score', 1)
        
        # Xác định style dựa trên điểm số
        if status == 'pending':
            border_color = "#e0e0e0" # Xám
            icon = "❔"
        elif student_score == max_score:
            border_color = "#d4edda" # Xanh nhạt
            icon = "✅"
        elif student_score > 0:
            border_color = "#fff3cd" # Vàng nhạt (đúng 1 phần)
            icon = "⚠️"
        else:
            border_color = "#f8d7da" # Đỏ nhạt
            icon = "❌"

        # Container cho câu hỏi
        with st.container():
            st.markdown(f"**{icon} Câu hỏi:** {ans.get('question_content', 'Nội dung bị ẩn')}")
            
            col_cont, col_feedback = st.columns([2, 1])
            
            with col_cont:
                # 1. Hiển thị nội dung trả lời
                if q_type in ["Trắc nghiệm (MC)", "Nghe (Listening)"]:
                    st.write(f"Bạn chọn: **{ans.get('student_choice')}**")
                    if status == 'graded':
                        st.write(f"Đáp án đúng: `{ans.get('correct_choice')}`")
                
                elif q_type == "Tự luận (Essay)":
                    st.text_area("Bài làm:", value=ans.get('student_text', ''), disabled=True, height=100)
                
                elif q_type == "Nói (Speaking)":
                    if ans.get('audio_path'):
                        url = FileUtils.get_signed_url(ans.get('audio_path'))
                        if url: 
                            st.audio(url)
                            st.caption("File ghi âm của bạn")

            with col_feedback:
                # 2. Hiển thị điểm & Lời phê (Trong khung riêng)
                st.markdown(
                    f"""
                    <div style="background-color: {border_color}; padding: 10px; border-radius: 8px; font-size: 0.9em;">
                        <strong>Điểm:</strong> {student_score}/{max_score}<br>
                        <hr style="margin: 5px 0;">
                        <strong>Giáo viên nhận xét:</strong><br>
                        <span style="font-style: italic;">{ans.get('teacher_comment', 'Chưa có nhận xét')}</span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            
            st.divider()