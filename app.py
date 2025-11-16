import streamlit as st
from google import genai
from google.genai import types
import os

# ----------------------------------------------------
# ⚠️ BƯỚC 1: DÁN DANH SÁCH MÃ FILE TẠM THỜI VÀO ĐÂY ⚠️
# DÁN LIST_FILES TỪ SCRIPT upload_drive_files.py VÀO ĐÂY
LIST_FILES = ['1I0lmDgGJdHfnzIjdLtH4ayXmb83G5dgR', '1pwCceN2dAucZEWytejVCPi6jX5xYItfY', '1XqETTjqIRJ_rUhI_DP--HaR0w3LODTgq'] 
# ----------------------------------------------------

# --- CẤU HÌNH KHÁC ---
MODEL_NAME = "gemini-2.0-flash"
# --- KẾT THÚC CẤU HÌNH ---


@st.cache_resource
def setup_chat_session():
    """Khởi tạo Gemini client và chat session bằng API Key."""
    try:
        # Lấy API Key từ Secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        sys_instruct = (
            "Bạn là Gia sư Hóa học THCS thông minh. Trả lời theo 2 quy trình: Lý thuyết (Cơ bản/Nâng cao) và Bài tập (Hướng dẫn/Giải chi tiết)."
        )

        list_parts = []
        for file_name in LIST_FILES:
            # Dùng mã file tạm thời của Gemini (được tạo bởi script)
            uri = f"https://generativelanguage.googleapis.com/v1beta/files/{file_name}" 
            # Dùng mime_type chung, vì file PDF/TXT đều được xử lý tốt
            list_parts.append(types.Part.from_uri(file_uri=uri, mime_type="application/pdf")) 
        
        list_parts.append(types.Part.from_text(text="Hãy tuân thủ 2 quy trình sư phạm trên."))

        chat = client.chats.create(
            model=MODEL_NAME, 
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.3
            ),
            history=[
                types.Content(role="user", parts=list_parts),
                types.Content(role="model", parts=[
                    types.Part.from_text(text="Đã hiểu 2 quy trình. Tôi đã đọc tài liệu.")
                ])
            ]
        )
        return chat 
    except Exception as e:
        st.error(f"❌ Lỗi thiết lập Gemini: {e}")
        
        if "API key" in str(e):
            st.error("Lỗi: Kiểm tra xem GEMINI_API_KEY đã được dán vào Streamlit Secrets chưa.")
        elif "Invalid or unsupported file uri" in str(e) or "files/" in str(e):
            st.error("Lỗi: Mã file trong LIST_FILES không hợp lệ hoặc đã hết hạn (48h). Vui lòng chạy lại script upload_drive_files.py.")
        
        return None

# --- CHẠY ỨNG DỤNG ---
st.set_page_config(page_title="Gia sư Hóa học (Ổn định)", layout="wide")
st.title("👨‍🔬 Gia sư Hóa học THCS (Nguồn: Google Drive -> Tái Upload)")

# Khởi tạo chat session
chat_session = setup_chat_session()

if chat_session:
    st.sidebar.success("✅ Đã kết nối Gemini (Dữ liệu ổn định).")
    st.sidebar.info(f"🤖 Model: {MODEL_NAME}")
    
    # Hiển thị thông báo đã tìm thấy file (dựa trên LIST_FILES)
    if len(LIST_FILES) > 0 and LIST_FILES[0] != 'DÁN_MÃ_FILE_TẠM_THỜI_VÀO_ĐÂY':
        st.sidebar.info(f"Thấy {len(LIST_FILES)} tài liệu.")
    st.sidebar.warning("⚠️ Mã file sẽ hết hạn sau 48 giờ. Vui lòng chạy lại script trên máy tính để làm mới dữ liệu.")
else:
    st.sidebar.error("Lỗi: Không thể khởi tạo Chatbot. Kiểm tra cấu hình.")

# Giao diện Chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào em! Thầy đã sẵn sàng."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    if not chat_session:
        st.error("Lỗi: Chatbot chưa được khởi tạo. Kiểm tra cấu hình.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thầy đang tra cứu..."):
                try:
                    response = chat_session.send_message(prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Lỗi: {e}")

