import streamlit as st
from google import genai
from google.genai import types
import os

# ==========================================
# 👇 DÁN MÃ FILE CỦA BẠN VÀO ĐÂY (Giữ nguyên mã cũ của bạn)
MY_FILE_NAME = "files/xxxxxxxxxxxxx" 
# ==========================================

st.set_page_config(page_title="Gia sư Hóa học THCS", layout="wide")
st.title("👨‍🔬 Gia sư Hóa học THCS")

# Sidebar
with st.sidebar:
    st.info(f"📚 Tài liệu đang dùng: `{MY_FILE_NAME}`")
    st.success("Đang chạy mô hình: Gemini 1.5 Flash-002")

@st.cache_resource
def setup_chat_session():
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key:
        st.error("⚠️ Chưa thiết lập GEMINI_API_KEY.")
        return None, None
        
    client = genai.Client(api_key=api_key)
    
    sys_instruct = (
        "Bạn là Gia sư Hóa học THCS. Trả lời dựa trên tài liệu đính kèm. "
        "Nếu không có thông tin trong tài liệu, hãy nói rõ."
    )

    try:
        chat = client.chats.create(
            # 👇 SỬA THÀNH TÊN PHIÊN BẢN CỤ THỂ (CÓ SỐ 002)
            model="gemini-1.5-flash-002", 
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.5
            ),
            history=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=f"https://generativelanguage.googleapis.com/v1beta/{MY_FILE_NAME}",
                            mime_type="text/plain"),
                        types.Part.from_text(text="Hãy học thuộc tài liệu này để dạy học sinh.")
                    ]
                ),
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="Đã rõ. Tôi đã sẵn sàng.")]
                )
            ]
        )
        return client, chat
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None, None

client, chat_session = setup_chat_session()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào em! Thầy là Gia sư Hóa học. Em có câu hỏi gì không?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    if not client: st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thầy đang xem lại tài liệu..."):
            try:
                response = chat_session.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Lỗi: {e}")
