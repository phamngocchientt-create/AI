import streamlit as st
from google import genai
from google.genai import types
import os
import io

# --- CẤU HÌNH BẮT BUỘC (SỬA LẠI CHO ĐÚNG) ---
# 👇 DÁN ID THƯ MỤC GOOGLE DRIVE CỦA BẠN VÀO ĐÂY
GOOGLE_DRIVE_FOLDER_ID = "1tSMd0fCm8NOsGfOnK2v0we63Ntp5anpB" 

# 👇 ĐIỀN TÊN CHÍNH XÁC CỦA MODEL BẠN DÙNG
MODEL_NAME = "gemini-2.0-flash"
# --- KẾT THÚC CẤU HÌNH ---


@st.cache_resource
def get_google_drive_service():
    """Xác thực Drive bằng cách đọc từng mảnh Secrets."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"], 
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"]
        }
        
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        service = build('drive', 'v3', credentials=creds)
        st.sidebar.success("✅ Đã kết nối Google Drive!")
        return service
        
    except KeyError as e:
        st.error(f"Lỗi Secrets: Thiếu key '{e.args[0]}'. Hãy kiểm tra file Secrets.")
        return None
    except Exception as e:
        st.error(f"Lỗi xác thực Google Drive: {e}")
        return None

@st.cache_data(ttl=600) # Cache trong 10 phút
def get_files_from_drive(_service):
    """Lấy danh sách file ID VÀ mimeType từ thư mục Google Drive."""
    try:
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents"
        results = _service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        files = results.get('files', [])
        
        if not files:
            st.warning("Không tìm thấy file nào trong thư mục Google Drive.")
            return []
            
        file_list = []
        for f in files:
            if "pdf" in f["mimeType"] or "text" in f["mimeType"]:
                file_list.append({"id": f["id"], "name": f["name"], "mimeType": f["mimeType"]})
        return file_list
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách file Drive: {e}")
        return []

@st.cache_resource
def setup_chat_session(_drive_files):
    """Khởi tạo Gemini client và phiên chat với các file từ Drive."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        sys_instruct = (
            "Bạn là Gia sư Hóa học THCS thông minh. Bạn có 2 quy trình chính:\n\n"
            "--- QUY TRÌNH 1: XỬ LÝ LÝ THUYẾT ---\n"
            "Tài liệu chia 3 cấp: [KIẾN THỨC CƠ BẢN], [GIẢI THÍCH], [NÂNG CAO].\n"
            "1. Hỏi lý thuyết -> Dùng [KIẾN THỨC CƠ BẢN].\n"
            "2. Hỏi 'Tại sao' -> Dùng [GIẢI THÍCH].\n"
            "3. Hỏi 'Nâng cao' -> Dùng [NÂNG CAO].\n"
            "--- QUY TRÌNH 2: XỬ LÝ BÀI TẬP ---\n"
            "1. Khi gặp BÀI TẬP (tính toán, vận dụng) -> KHÔNG GIẢI NGAY.\n"
            "2. Hỏi học sinh: 'Đây là bài tập hay! Em muốn thầy giúp thế nào?'\n"
            "   🅰️. Hướng dẫn từng bước.\n"
            "   🅱️. Xem lời giải chi tiết.\n"
            "3. Nếu chọn A: Gợi ý Bước 1, chờ phản hồi rồi gợi ý Bước 2.\n"
            "4. Nếu chọn B: Dùng [BÀI TẬP VÀ GIẢI CHI TI TIẾT] để giải mẫu."
        )

        list_parts = []
        for f in _drive_files:
            # ⚠️ SỬA LỖI TAI HẠI: "generativelace" -> "generativelanguage" ⚠️
            uri = f"https://generativelanguage.googleapis.com/v1beta/files/{f['id']}"
            list_parts.append(types.Part.from_uri(file_uri=uri, mime_type=f['mimeType'])) 
        
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
                    types.Part.from_text(text="Đã hiểu 2 quy trình. Tôi đã đọc tài liệu từ Google Drive.")
                ])
            ]
        )
        return client, chat
    except Exception as e:
        st.error(f"❌ Lỗi thiết lập Gemini: {e}")
        return None, None

# --- CHẠY ỨNG DỤNG ---
st.set_page_config(page_title="Gia sư Hóa học (Drive)", layout="wide")
st.title("👨‍🔬 Gia sư Hóa học THCS (Nguồn: Google Drive)")

drive_service = get_google_drive_service()

if drive_service:
    drive_files = get_files_from_drive(drive_service)
    
    if drive_files:
        with st.sidebar:
            st.info(f"🤖 Model: {MODEL_NAME}")
            with st.expander(f"Thấy {len(drive_files)} tài liệu (Refresh sau 10p)"):
                for f in drive_files:
                    st.code(f"{f['name']} ({f['mimeType']})")
        client, chat_session = setup_chat_session(drive_files)
    else:
        st.sidebar.error("Không tìm thấy file PDF/TXT nào trong thư mục Drive.")
else:
    st.sidebar.error("Chưa kết nối được Google Drive. Kiểm tra Secrets.")

# Giao diện Chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào em! Thầy đã sẵn sàng."}]
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    if 'chat_session' not in locals() or not chat_session:
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

