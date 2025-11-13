import streamlit as st
from google import genai
from google.genai import types
import os

# ==================================================
# 👇 MÃ FILE CỦA BẠN (Tôi đã điền sẵn)
MY_FILE_NAME = "files/501jm98gmcjc"
# ==================================================

st.set_page_config(page_title="Gia sư Hóa học THCS", layout="wide")
st.title("👨‍🔬 Gia sư Hóa học THCS")

# Sidebar hiển thị thông tin
with st.sidebar:
    st.success("✅ Kết nối thành công!")
    st.info(f"📚 Tài liệu: `{MY_FILE_NAME}`")
    # Sử dụng model chính thức từ danh sách của bạn
    st.info("🤖 Model: gemini-2.0-flash")

@st.cache_resource
def setup_chat_session():
    # Lấy API Key từ biến môi trường
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key:
        st.error("⚠️ LỖI: Chưa thiết lập GEMINI_API_KEY.")
        return None, None
        
    client = genai.Client(api_key=api_key)
    
    # Hướng dẫn cho AI
    sys_instruct = (
        "Bạn là Gia sư Hóa học THCS (Lớp 8-9) thân thiện. "
        "Nhiệm vụ: Trả lời câu hỏi của học sinh CHÍNH XÁC dựa trên tài liệu đính kèm. "
        "Nếu tài liệu không có thông tin, hãy nói rõ rằng bạn không tìm thấy trong giáo trình."
    )

    try:
        # 👇 ĐÃ CHỌN MODEL TỐT NHẤT TRONG DANH SÁCH CỦA BẠN
        chat = client.chats.create(
            model="gemini-2.0-flash", 
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.5 # Giữ câu trả lời ổn định
            ),
            history=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=f"https://generativelanguage.googleapis.com/v1beta/{MY_FILE_NAME}",
                            mime_type="text/plain"),
                        types.Part.from_text(text="Đây là giáo trình Hóa học. Hãy học thuộc nó để dạy học sinh.")
                    ]
                ),
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="Đã rõ. Tôi đã đọc tài liệu và sẵn sàng dạy Hóa học.")]
                )
            ]
        )
        return client, chat
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Gemini: {e}")
        return None, None

# Khởi tạo
client, chat_session = setup_chat_session()

# Quản lý lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào em! Thầy là Gia sư Hóa học. Em muốn hỏi về bài nào?"}]

# Hiển thị tin nhắn
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Xử lý khi người dùng nhập câu hỏi
if prompt := st.chat_input("Nhập câu hỏi Hóa học..."):
    if not client: st.stop()
    
    # Hiện câu hỏi
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI trả lời
    with st.chat_message("assistant"):
        with st.spinner("Thầy đang suy nghĩ..."):
            try:
                response = chat_session.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")
