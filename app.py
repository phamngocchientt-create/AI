import streamlit as st
from google import genai
from google.genai import types
import os
import io
import json

# --- CẤU HÌNH BẮT BUỘC (SỬA LẠI CHO ĐÚNG) ---

# 👇 DÁN ID THƯ MỤC GOOGLE DRIVE CỦA BẠN VÀO ĐÂY
# (Lấy từ đường link URL trên trình duyệt)
GOOGLE_DRIVE_FOLDER_ID = "1tSMd0fCm8NOsGfOnK2v0we63Ntp5anpB" 

# 👇 ĐIỀN TÊN CHÍNH XÁC CỦA MODEL BẠN DÙNG (Lấy từ lần check trước)
# (Ví dụ: "gemini-2.0-flash")
MODEL_NAME = "gemini-2.0-flash"

# --- KẾT THÚC CẤU HÌNH ---


# Hàm này dùng để kết nối với Google Drive bằng file JSON
@st.cache_resource
def get_google_drive_service():
    """Xác thực và trả về đối tượng service của Google Drive."""
    try:
        # Lấy nội dung file JSON từ Streamlit Secrets
        creds_json = st.secrets["GOOGLE_CREDS_JSON"]
        creds_dict = json.loads(creds_json)
        
        # Nhập thư viện Google (chỉ nhập khi cần)
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_info(creds_dict)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Lỗi xác thực Google Drive: {e}")
        return None

# Hàm này dùng để lấy danh sách file từ thư mục
@st.cache_data(ttl=600) # Cache trong 10 phút
def get_files_from_drive(_service):
    """Lấy danh sách file ID từ thư mục Google Drive."""
    try:
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents"
        results = _service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        files = results.get('files', [])
        
        if not files:
            st.warning("Không tìm thấy file nào trong thư mục Google Drive.")
            return []
            
        file_list = []
        for f in files:
            # Chỉ lấy file PDF và TXT, bỏ qua file Google Docs/Sheets
            if "pdf" in f["mimeType"] or "text" in f["mimeType"]:
                file_list.append({"id": f["id"], "name": f["name"]})
        return file_list
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách file Drive: {e}")
        return []

# Hàm này tạo Chatbot
@st.cache_resource
def setup_chat_session(_drive_files):
    """Khởi tạo Gemini client và phiên chat với các file từ Drive."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        sys_instruct = (
            "Bạn là Gia sư Hóa học THCS thông minh, tận tâm. Bạn có 2 quy trình chính:\n\n"
            "--- QUY TRÌNH 1: XỬ LÝ CÂU HỎI LÝ THUYẾT ---\n"
            "Tài liệu được chia 3 cấp: [KIẾN THỨC CƠ BẢN], [PHẦN GIẢI THÍCH], [PHẦN NÂNG CAO].\n"
            "1. Nếu học sinh hỏi lý thuyết bình thường: Chỉ dùng [KIẾN THỨC CƠ BẢN].\n"
            "2. Nếu học sinh hỏi 'Tại sao', 'Giải thích': Dùng [PHẦN GIẢI THÍCH].\n"
            "3. Nếu học sinh hỏi 'Nâng cao', 'Mở rộng': Dùng [PHẦN NÂNG CAO].\n"
            "-> Trả lời ngay lập tức.\n\n"
            "--- QUY TRÌNH 2: XỬ LÝ BÀI TẬP ---\n"
            "BÀI TẬP là câu hỏi tính toán hoặc vận dụng.\n"
            "1. Khi phát hiện đây là BÀI TẬP, TUYỆT ĐỐI KHÔNG GIẢI NGAY.\n"
            "2. Hãy hỏi học sinh: 'Đây là bài tập hay! Em muốn thầy giúp thế nào?'\n"
            "   🅰️. Hướng dẫn gợi ý từng bước.\n"
            "   🅱️. Xem lời giải chi tiết.\n"
            "3. Nếu học sinh chọn A: Chỉ gợi ý Bước 1. Chờ phản hồi rồi gợi ý Bước 2.\n"
            "4. Nếu học sinh chọn B: Dùng tài liệu [BÀI TẬP VÀ GIẢI CHI TIẾT] để giải mẫu."
        )

        # Tạo list_parts từ file Drive
        list_parts = []
        for f in _drive_files:
            # Dùng thẳng ID của Google Drive
            uri = f"https://generativelace.googleapis.com/v1beta/files/{f['id']}"
            list_parts.append(types.Part.from_uri(file_uri=uri, mime_type="application/pdf")) # Giả định đều là PDF/TXT
        
        list_parts.append(types.Part.from_text(text="Hãy tuân thủ 2 quy trình sư phạm trên."))

        chat = client.chats.create(
            model=MODEL_NAME, 
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.3
            ),
            history=[
                types.Content(role="user", parts=list_parts),
                types.Content(role="model", parts=[types.Part.from_text("Đã hiểu 2 quy trình. Tôi đã đọc tài liệu từ Google Drive.")])
            ]
        )
        return client, chat
    except Exception as e:
        st.error(f"❌ Lỗi thiết lập Gemini: {e}")
        return None, None

# --- CHẠY ỨNG DỤNG ---
st.set_page_config(page_title="Gia sư Hóa học (Drive)", layout="wide")
st.title("👨‍🔬 Gia sư Hóa học THCS (Nguồn: Google Drive)")

# Khởi tạo các biến
drive_service = None
client = None
chat_session = None

# Bước 1: Kết nối Drive
drive_service = get_google_drive_service()

if drive_service:
    # Bước 2: Lấy danh sách file
    drive_files = get_files_from_drive(drive_service)
    
    if drive_files:
        with st.sidebar:
            st.success(f"✅ Đã kết nối Google Drive, tìm thấy {len(drive_files)} tài liệu.")
            st.info(f"🤖 Model: {MODEL_NAME}")
            with st.expander("Danh sách tài liệu (Refresh sau 10p)"):
                for f in drive_files:
                    st.code(f["name"])

        # Bước 3: Khởi tạo Chatbot
        client, chat_session = setup_chat_session(drive_files)
    else:
        st.sidebar.error("Không tìm thấy file PDF/TXT nào trong thư mục Drive.")
else:
    st.sidebar.error("Chưa kết nối được Google Drive. Kiểm tra Secrets.")

# Giao diện Chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào em! Thầy đã sẵn sàng (đọc tài liệu từ Google Drive)."}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    if not client or not chat_session:
        st.error("Lỗi: Chatbot chưa được khởi tạo. Kiểm tra cấu hình.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thầy đang tra cứu Google Drive..."):
                try:
                    response = chat_session.send_message(prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Lỗi: {e}")

