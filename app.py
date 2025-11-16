import streamlit as st
from google import genai
from google.genai import types
import os

# ==================================================
# 👇 DANH SÁCH FILE (Giữ nguyên của bạn)
LIST_FILES = ['files/501jm98gmcjc'] 
# ==================================================

st.set_page_config(page_title="Gia sư Hóa học THCS", layout="wide")
st.title("👨‍🔬 Gia sư Hóa học THCS (Bản Nâng Cao)")

with st.sidebar:
    st.info("🤖 Model: gemini-2.0-flash")
    st.success(f"✅ Đã kết nối {len(LIST_FILES)} tài liệu.")
    with st.expander("📖 Quy tắc hoạt động"):
        st.write("1. Phân tầng kiến thức (Cơ bản, Nâng cao...).")
        st.write("2. Gặp bài tập sẽ hỏi A/B (Hướng dẫn/Giải luôn).")

@st.cache_resource
def setup_chat_session():
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key: return None, None
    client = genai.Client(api_key=api_key)
    
    # --- 🧠 BỘ NÃO NÂNG CẤP (Kết hợp 2 ý tưởng) ---
    sys_instruct = (
        "Bạn là Gia sư Hóa học THCS thông minh, tận tâm. Bạn có 2 quy trình chính:\n\n"
        "--- QUY TRÌNH 1: XỬ LÝ CÂU HỎI LÝ THUYẾT ---\n"
        "Tài liệu được chia 3 cấp: [KIẾN THỨC CƠ BẢN], [PHẦN GIẢI THÍCH], [PHẦN NÂNG CAO].\n"
        "1. Nếu học sinh hỏi lý thuyết bình thường (ví dụ: 'Oxit là gì?'): Chỉ dùng [KIẾN THỨC CƠ BẢN].\n"
        "2. Nếu học sinh hỏi 'Tại sao', 'Vì sao', 'Giải thích': Dùng [PHẦN GIẢI THÍCH].\n"
        "3. Nếu học sinh hỏi 'Nâng cao', 'Mở rộng', 'Có gì đặc biệt': Dùng [PHẦN NÂNG CAO].\n"
        "-> Với 3 trường hợp này, hãy trả lời ngay lập tức.\n\n"
        "--- QUY TRÌNH 2: XỬ LÝ BÀI TẬP ---\n"
        "BÀI TẬP là câu hỏi tính toán (ví dụ: 'Tính V...') hoặc vận dụng (ví dụ: 'Nêu hiện tượng...').\n"
        "1. Khi phát hiện đây là BÀI TẬP, TUYỆT ĐỐI KHÔNG GIẢI NGAY.\n"
        "2. Hãy hỏi học sinh: 'Đây là một bài tập hay! Em muốn thầy giúp thế nào?'\n"
        "   🅰️. Hướng dẫn gợi ý từng bước (Em tự giải).\n"
        "   🅱️. Xem lời giải chi tiết (Thầy giải mẫu).\n"
        "3. Nếu học sinh chọn A (Hướng dẫn): Chỉ gợi ý Bước 1 (Ví dụ: 'Em viết PTHH ra trước nhé'). Chờ học sinh phản hồi rồi mới gợi ý Bước 2.\n"
        "4. Nếu học sinh chọn B (Giải luôn): Dùng tài liệu [BÀI TẬP VÀ GIẢI CHI TIẾT] để trình bày lời giải mẫu."
    )

    list_parts = []
    for file_name in LIST_FILES:
        uri_path = f"https://generativelanguage.googleapis.com/v1beta/{file_name}"
        list_parts.append(types.Part.from_uri(file_uri=uri_path, mime_type="text/plain"))
    
    list_parts.append(types.Part.from_text(text="Hãy tuân thủ 2 quy trình sư phạm trên."))

    try:
        chat = client.chats.create(
            # Dùng model xịn nhất của bạn
            model="gemini-2.0-flash", 
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.3 # Giảm sáng tạo để tuân thủ luật chặt chẽ
            ),
            history=[
                types.Content(role="user", parts=list_parts),
                types.Content(role="model", parts=[types.Part.from_text(text="Đã hiểu 2 quy trình. Tôi sẽ phân biệt rõ Lý thuyết và Bài tập.")])
            ]
        )
        return client, chat
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")
        return None, None

client, chat_session = setup_chat_session()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào em! Thầy là Gia sư Hóa học. Em có câu hỏi lý thuyết hay bài tập nào cần hỗ trợ không?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    if not client: st.stop()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thầy đang phân tích câu hỏi..."):
            try:
                response = chat_session.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Lỗi: {e}")
