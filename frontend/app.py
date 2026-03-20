import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="AI Edu Hub",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://localhost:8000/api/v1"

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes shine {
        0% { left: -100%; }
        50% { left: 100%; }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main {
        padding-top: 2rem;
        background: linear-gradient(-45deg, #f8fafb, #f2f8fc, #faf8f3, #f5f9f8);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(71, 115, 179, 0.7) 0%, rgba(80, 150, 180, 0.7) 50%, rgba(100, 150, 120, 0.7) 100%);
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, rgba(71, 115, 179, 0.7) 0%, rgba(80, 150, 180, 0.7) 50%, rgba(100, 150, 120, 0.7) 100%);
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: white !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-left: 4px solid rgba(71, 115, 179, 0.5);
        transition: all 0.3s cubic-bezier(0.23, 1, 0.320, 1);
    }
    
    .card:hover {
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
        border-left-color: rgba(71, 115, 179, 0.8);
    }
    
    .stButton > button {
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.35s cubic-bezier(0.23, 1, 0.320, 1);
        width: 100%;
        background: linear-gradient(90deg, rgba(71, 115, 179, 0.6) 0%, rgba(80, 150, 180, 0.6) 100%);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: shine 3s infinite;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 6px 20px rgba(71, 115, 179, 0.25);
        background: linear-gradient(90deg, rgba(71, 115, 179, 0.8) 0%, rgba(80, 150, 180, 0.8) 100%);
    }
    
    .stFileUploader {
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    h1 {
        color: rgba(71, 115, 179, 0.8);
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 10px;
        animation: slideIn 0.6s ease;
    }
    
    h2 {
        color: rgba(80, 150, 180, 0.7);
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        animation: slideIn 0.7s ease;
    }
    
    h3 {
        color: rgba(71, 115, 179, 0.7);
        font-weight: 600 !important;
    }
    
    .caption-text {
        color: #666;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    
    .stAlert {
        border-radius: 10px;
        padding: 15px !important;
        margin-bottom: 10px;
        animation: slideIn 0.4s ease;
        backdrop-filter: blur(5px);
    }
    
    .chat-message {
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        line-height: 1.6;
        animation: slideIn 0.4s ease;
        transition: all 0.3s ease;
    }
    
    .chat-message:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transform: translateX(5px);
    }
    
    .streamlit-expanderHeader {
        background-color: rgba(242, 248, 252, 0.6);
        border-radius: 10px;
        font-weight: 600;
        color: rgba(71, 115, 179, 0.7);
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: rgba(242, 248, 252, 1);
        color: rgba(71, 115, 179, 0.9);
    }
    
    .stTextInput > div > div > input,
    .stChatInput > div > div > input {
        background: rgba(255, 255, 255, 0.5);
        border: 1px solid rgba(71, 115, 179, 0.2) !important;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:hover,
    .stChatInput > div > div > input:hover {
        background: rgba(255, 255, 255, 0.8);
        border-color: rgba(71, 115, 179, 0.4) !important;
        box-shadow: 0 2px 8px rgba(71, 115, 179, 0.15);
    }
    
    .stTextInput > div > div > input:focus,
    .stChatInput > div > div > input:focus {
        background: rgba(255, 255, 255, 0.95);
        border-color: rgba(71, 115, 179, 0.6) !important;
        box-shadow: 0 4px 12px rgba(71, 115, 179, 0.25) !important;
    }
    
    hr {
        border-color: rgba(71, 115, 179, 0.1);
        opacity: 0.5;
    }
    
    * {
        transition: background-color 0.3s ease, color 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# --- KHỞI TẠO BỘ NHỚ SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

# --- SIDEBAR: QUẢN LÝ TÀI LIỆU ĐA PHƯƠNG TIỆN ---
with st.sidebar:
    st.markdown("## 🎓 Kho Dữ Liệu")
    
    # Section 1: Upload documents
    st.markdown("### 📄 Tải lên Tài Liệu")
    st.markdown("*Hỗ trợ PDF, PPTX*", help="Tải các tài liệu học tập của bạn lên đây")
    
    uploaded_file = st.file_uploader(
        "Chọn file bài giảng",
        type=["pdf", "pptx"],
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("⚙️ Xử lý", key="process_doc", use_container_width=True):
            if uploaded_file is not None:
                progress_bar = st.progress(0)
                try:
                    progress_bar.progress(25)
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    
                    progress_bar.progress(50)
                    res = requests.post(f"{API_URL}/upload", files=files)
                    progress_bar.progress(75)
                    
                    if res.status_code == 200:
                        progress_bar.progress(100)
                        st.success(f"✅ Đã nạp: {uploaded_file.name}", icon="✅")
                    else:
                        st.error(f"❌ Lỗi: {res.json().get('detail')}", icon="❌")
                except Exception as e:
                    st.error("❌ Lỗi kết nối Backend!", icon="❌")
            else:
                st.warning("⚠️ Vui lòng chọn file", icon="⚠️")
    
    st.divider()
    
    # Section 2: YouTube
    st.markdown("### 📺 Video YouTube")
    st.markdown("*Bôi trích nội dung từ video*", help="Dán link video để AI phân tích")
    youtube_url = st.text_input(
        "YouTube link",
        placeholder="https://youtube.com/...",
        label_visibility="collapsed"
    )
    
    if st.button("▶️ Xử lý Video", key="process_video", use_container_width=True):
        if youtube_url:
            progress_bar = st.progress(0)
            try:
                progress_bar.progress(30)
                res = requests.post(f"{API_URL}/upload-youtube", json={"url": youtube_url})
                progress_bar.progress(60)
                
                if res.status_code == 200:
                    progress_bar.progress(100)
                    st.success("✅ Đã xử lý xong video!", icon="✅")
                else:
                    st.error(f"❌ Lỗi: {res.json().get('detail')}", icon="❌")
            except Exception as e:
                st.error("❌ Lỗi kết nối Backend!", icon="❌")
        else:
            st.warning("⚠️ Nhập link YouTube", icon="⚠️")
    
    st.divider()
    
    # Section 3: Memory management
    if st.button("🗑️ Xóa Bộ Nhớ", use_container_width=True):
        st.session_state.messages = []
        st.session_state.quiz_data = None
        st.rerun()
    
    st.markdown("---")
    st.caption("AI Edu Hub v1.0 | Powered by RAG + Qdrant")


# --- MAIN AREA ---
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("# 📚 AI Edu Hub")
    st.markdown("### Trợ lý Học tập Thông minh")
with col2:
    st.metric("💬", len(st.session_state.get("messages", [])))

st.markdown("---")

# TẠO 2 TAB CHÍNH
tab_chat, tab_quiz = st.tabs(["💬 Trợ lý Học tập", "📝 Ôn tập Trắc nghiệm"])

# ==========================================
# TAB 1: GIAO DIỆN CHAT (GIỮ NGUYÊN LOGIC CŨ)
# ==========================================
with tab_chat:
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(71, 115, 179, 0.4) 0%, rgba(80, 150, 180, 0.4) 50%, rgba(100, 150, 120, 0.4) 100%);
                backdrop-filter: blur(10px);
                padding: 20px; border-radius: 15px; color: #333; margin-bottom: 30px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                transition: all 0.3s ease;
                animation: slideIn 0.6s ease;">
        <p style="margin: 0; font-size: 0.95rem;">
            🤖 <b>Hệ thống RAG với trí nhớ dài hạn</b><br>
            Tích hợp Reranker & Đa phương tiện | Phiên bản Enterprise
        </p>
    </div>
    """, unsafe_allow_html=True)

    chat_container = st.container(border=False)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])

    if prompt := st.chat_input("🔍 Nhập câu hỏi... (VD: Gradient Descent là gì?)"):
        payload = {
            "query": prompt,
            "history": st.session_state.messages.copy() 
        }
        
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(prompt)
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            try:
                with st.spinner("🔄 AI đang suy nghĩ..."):
                    response = requests.post(f"{API_URL}/chat", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    message_placeholder.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
                    if sources:
                        st.divider()
                        with st.expander("📚 **Nguồn tham khảo** (Click để xem chi tiết)", expanded=False):
                            for idx, source in enumerate(sources, 1):
                                payload_data = source.get("payload", {})
                                text_snippet = payload_data.get("text", "")[:250]
                                filename = payload_data.get("filename", "Không rõ")
                                score = source.get("score", 0.0)
                                
                                # SỬA LẠI ĐỊNH DẠNG ĐIỂM RERANKER (Thành số thập phân .2f)
                                st.markdown(f"""
                                **📄 Nguồn {idx}**
                                - **File:** `{filename}`
                                - **Điểm logic (Reranker):** `{score:.2f}`
                                
                                > {text_snippet}...
                                """)
                else:
                    error_msg = response.json().get('detail', 'Lỗi không xác định')
                    message_placeholder.error(f"❌ Lỗi: {error_msg}")
                    
            except requests.exceptions.ConnectionError:
                message_placeholder.error("❌ Không thể kết nối Backend.")
            except Exception as e:
                message_placeholder.error(f"❌ Lỗi: {str(e)}")

# ==========================================
# TAB 2: GIAO DIỆN TẠO TRẮC NGHIỆM TỰ ĐỘNG
# ==========================================
with tab_quiz:
    st.markdown("### 📝 Sinh Bài Tập Trắc Nghiệm Tự Động")
    st.write("Nhập một chủ đề bất kỳ có trong tài liệu của bạn, AI sẽ tự động đọc, trích xuất kiến thức và tạo ra một bộ đề thi trắc nghiệm để bạn ôn tập!")
    
    col_q1, col_q2 = st.columns([3, 1])
    with col_q1:
        quiz_topic = st.text_input("📚 Chủ đề ôn tập:", placeholder="VD: Thuật toán KNN, Machine Learning...")
    with col_q2:
        quiz_num = st.number_input("🔢 Số câu hỏi:", min_value=1, max_value=15, value=5)

    if st.button("🚀 Soạn đề thi ngay!", use_container_width=True):
        if not quiz_topic:
            st.warning("⚠️ Vui lòng nhập chủ đề bạn muốn ôn tập!")
        else:
            with st.spinner("🧠 AI đang phân tích tài liệu và soạn câu hỏi... (Có thể mất 10-20 giây)"):
                try:
                    res = requests.post(f"{API_URL}/generate-quiz", json={"topic": quiz_topic, "num_questions": quiz_num})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.quiz_data = data.get("quiz", [])
                        # Đặt lại trạng thái bài làm
                        st.session_state.quiz_submitted = False
                        st.session_state.user_answers = {}
                        st.rerun() # Tải lại giao diện để hiện câu hỏi
                    else:
                        st.error(f"❌ AI không tìm thấy tài liệu phù hợp: {res.json().get('detail')}")
                except Exception as e:
                    st.error("❌ Không thể kết nối đến máy chủ AI.")

    # --- KHU VỰC LÀM BÀI TRẮC NGHIỆM ---
    if st.session_state.quiz_data:
        st.divider()
        st.markdown(f"#### 🎯 Đề thi: {quiz_topic}")
        
        # Duyệt qua từng câu hỏi JSON
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Câu {i+1}: {q.get('question', '')}**")
            
            # Hiển thị Radio Button cho các đáp án
            options = q.get('options', [])
            selected_option = st.radio(
                label=f"Đáp án câu {i+1}",
                options=options,
                key=f"quiz_radio_{i}",
                label_visibility="collapsed",
                index=None, # Mặc định không chọn gì
                disabled=st.session_state.quiz_submitted # Khóa nút nếu đã nộp bài
            )
            
            # Lưu lựa chọn của người dùng vào session state
            st.session_state.user_answers[i] = selected_option

            # NẾU ĐÃ NỘP BÀI -> HIỂN THỊ KẾT QUẢ ĐÚNG/SAI BÊN DƯỚI CÂU HỎI
            if st.session_state.quiz_submitted:
                correct_answer = q.get('answer', '')
                explanation = q.get('explanation', '')
                
                if selected_option:
                    # Chấm điểm (Chỉ cần chuỗi đáp án chứa text của đáp án đúng)
                    if correct_answer in selected_option or selected_option in correct_answer:
                        st.success(f"✅ **Chính xác!**\n\n💡 *Giải thích:* {explanation}")
                    else:
                        st.error(f"❌ **Sai rồi!** Đáp án đúng là: **{correct_answer}**\n\n💡 *Giải thích:* {explanation}")
                else:
                    st.warning(f"⚠️ Bạn chưa trả lời câu này! Đáp án đúng là: **{correct_answer}**\n\n💡 *Giải thích:* {explanation}")
            
            st.write("") # Dòng trống phân cách

        st.divider()
        
        # NÚT NỘP BÀI
        if not st.session_state.quiz_submitted:
            if st.button("✅ Nộp Bài & Xem Điểm", type="primary", use_container_width=True):
                st.session_state.quiz_submitted = True
                st.rerun() # Tải lại giao diện để kích hoạt trạng thái chấm điểm


# --- FOOTER ---
st.divider()
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.85rem; padding: 20px 0;">
    <p>✨ <b>AI Edu Hub</b> - Nền tảng học tập thông minh<br>
    © 2024 | Sử dụng RAG + Vector Database</p>
</div>
""", unsafe_allow_html=True)