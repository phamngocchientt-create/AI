import streamlit as st
from google import genai
from google.genai import types
import os

# ==========================================
# 👇 DÁN CÁI MÃ FILE BẮT ĐẦU BẰNG "files/..." VÀO ĐÂY
# Ví dụ: "files/501jm98gmcjc" (Lấy từ màn hình đen CMD lúc nãy)
MY_FILE_NAME = "files/50ljm98gmcjc"
# ==========================================

st.set_page_config(page_title="Gia sư Hóa học THCS", layout="wide")
st.title("👨‍🔬 Gia sư Hóa học THCS")

# Sidebar hiển thị trạng thái
with st.sidebar:
    st.info(f"📚 Đang sử dụng tài liệu: `{MY_FILE_NAME}`")
    st.markdown("---")
    st.write("Gia sư AI sử dụng mô hình Gemini Flash 2.0 với khả năng đọc hiểu ngữ cảnh siêu dài.")


@st.cache_resource
def setup_chat_session():
    """Thiết lập Client và đưa tài liệu vào ngữ cảnh ngay từ đầu."""

    # Lấy API Key từ Streamlit Secrets (biến môi trường)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ Chưa thiết lập GEMINI_API_KEY. Vui lòng kiểm tra Secrets.")
        return None, None

    client = genai.Client(api_key=api_key)

    # 1. Định nghĩa tính cách gia sư
    sys_instruct = (
        "Bạn là một Gia sư Hóa học THCS (Lớp 8-9) thân thiện, kiên nhẫn và sư phạm. "
        "Nhiệm vụ của bạn là trả lời câu hỏi của học sinh dựa trên tài liệu được cung cấp. "
        "Nếu tài liệu không có thông tin, hãy nói rõ và gợi ý học sinh hỏi phần khác."
    )

    # 2. Tạo phiên chat và đính kèm file vào lịch sử
    try:
        chat = client.chats.create(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.5  # Giảm sáng tạo để bám sát tài liệu
            ),
            history=[
                types.Content(
                    role="user",
                    parts=[
                        # Đưa file vào đây
                        types.Part.from_uri(
                            file_uri=f"https://generativelanguage.googleapis.com/v1beta/{MY_FILE_NAME}",
                            mime_type="text/plain"),
                        types.Part.from_text(text="Đây là giáo trình Hóa học. Hãy học thuộc nó để dạy học sinh.")
                    ]
                ),
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text="Tôi đã đọc xong giáo trình. Tôi sẵn sàng dạy Hóa học.")]
                )
            ]
        )
        return client, chat
    except Exception as e:
        st.error(f"Lỗi kết nối Gemini: {e}")
        return None, None


# Khởi tạo session
client, chat_session = setup_chat_session()

# Quản lý lịch sử chat trên giao diện
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Xin chào! Thầy là Gia sư Hóa học AI. Em cần thầy giảng bài nào trong tài liệu?"}
    ]

# Hiển thị tin nhắn cũ
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Xử lý nhập liệu mới
if prompt := st.chat_input("Nhập câu hỏi Hóa học của bạn..."):
    if not client: st.stop()

    # Hiển thị câu hỏi người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI trả lời
    with st.chat_message("assistant"):
        with st.spinner("Thầy đang xem lại tài liệu..."):
            try:
                response = chat_session.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:

                st.error(f"Có lỗi xảy ra: {e}")
