import streamlit as st
import requests
import time

# -------------------- CONFIG --------------------
API_BASE_URL = "http://127.0.0.1:8000"
CHAT_API_URL = f"{API_BASE_URL}/chat"
UPLOAD_API_URL = f"{API_BASE_URL}/upload"
DOCS_API_URL = f"{API_BASE_URL}/documents"

AGENT_AVATAR = "🤖"
USER_AVATAR = "🧑‍💻"

st.set_page_config(
    page_title="Aegis HR - AI Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- CUSTOM CSS --------------------
st.markdown("""
<style>
/* Global Style */
body {
    background: radial-gradient(circle at top, #0d0d0d 0%, #000000 100%);
    color: #e5e5e5;
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit’s built-in file size limit text */
div[data-testid="stFileUploader"] label p {
    display: none !important;
}

/* Chat Container */
[data-testid="stChatMessage"] {
    background: rgba(25, 25, 25, 0.5);
    border-radius: 16px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0px 0px 20px rgba(255, 215, 0, 0.05);
    animation: fadeIn 0.6s ease;
}

/* Fade In Animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Assistant Message (Left Aligned) */
.assistant-container {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    margin-bottom: 1rem;
}
.assistant-bubble {
    background: linear-gradient(135deg, #101010, #1a1a1a);
    border-left: 3px solid gold;
    border-radius: 16px;
    padding: 0.8rem 1.2rem;
    box-shadow: inset 0 0 10px rgba(255, 215, 0, 0.05);
    max-width: 80%;
}
.assistant-avatar {
    font-size: 1.4rem;
    margin-top: 0.2rem;
}

/* User Message (Right Aligned) */
.user-container {
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
    gap: 0.6rem;
    margin-bottom: 1rem;
}
.user-bubble {
    background: linear-gradient(135deg, #1b1b1b, #111);
    border-right: 3px solid #c5a100;
    border-radius: 16px;
    padding: 0.8rem 1.2rem;
    text-align: right;
    color: #fffbe6;
    max-width: 80%;
    box-shadow: inset 0 0 10px rgba(255, 215, 0, 0.05);
}
.user-avatar {
    font-size: 1.4rem;
    margin-top: 0.2rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0b0b0b 0%, #111 100%);
    color: #eaeaea;
    box-shadow: 2px 0 10px rgba(255, 215, 0, 0.05);
}

h1, h2, h3, h4 {
    color: #f5f5f5 !important;
    font-weight: 600;
}

/* Buttons */
div.stButton > button {
    background: linear-gradient(135deg, #222, #000);
    color: gold;
    border: 1px solid rgba(255, 215, 0, 0.4);
    border-radius: 10px;
    font-weight: 500;
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #444, #111);
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    color: #fffbe6;
}

/* Upload Widget */
div[data-testid="stFileUploader"] {
    background: rgba(15,15,15,0.7);
    padding: 0.5rem;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
}

/* Glowing Gradient Accent */
.glow {
    background: linear-gradient(90deg, gold, #fffbe6, gold);
    background-size: 200% 200%;
    animation: shimmer 4s infinite;
    height: 2px;
    border-radius: 2px;
    margin: 1rem 0;
}
@keyframes shimmer {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* Input Box */
div.stChatInputContainer {
    background: rgba(20,20,20,0.8);
    border-top: 1px solid rgba(255,215,0,0.2);
    box-shadow: 0 -4px 10px rgba(0,0,0,0.3);
}

/* Typing Animation */
.typing {
    display: inline-block;
    border-right: 2px solid gold;
    animation: blink 0.8s infinite;
}
@keyframes blink {
    50% { border-color: transparent; }
}
</style>
""", unsafe_allow_html=True)


# -------------------- FUNCTIONS --------------------
def get_document_list():
    try:
        response = requests.get(DOCS_API_URL, timeout=10)
        response.raise_for_status()
        st.session_state.document_list = response.json().get("documents", [])
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"⚠️ Failed to get docs: {e}")
        st.session_state.document_list = []


def handle_uploads():
    if st.session_state.file_uploader:
        st.info("📤 Uploading and processing files...")
        for uploaded_file in st.session_state.file_uploader:
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(UPLOAD_API_URL, files=files, timeout=180)
                if response.status_code == 200:
                    st.success(f"✅ Processed '{uploaded_file.name}' successfully!")
                else:
                    st.error(f"❌ Error with '{uploaded_file.name}': {response.json().get('detail')}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error for '{uploaded_file.name}': {e}")
        get_document_list()


# -------------------- INITIALIZE --------------------
if "messages" not in st.session_state:
    st.title("💼 Aegis HR — Executive AI Assistant")
    st.markdown("<div class='glow'></div>", unsafe_allow_html=True)
    st.session_state.messages = [{"role": "assistant", "content": "Hello, I'm Aegis HR. How can I assist you today?"}]
if "document_list" not in st.session_state:
    get_document_list()


# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.header("📁 Resume Management")
    st.file_uploader(
        "Upload Resumes (PDF)",
        type="pdf",
        accept_multiple_files=True,
        key="file_uploader",
        on_change=handle_uploads
    )
    st.markdown("<div class='glow'></div>", unsafe_allow_html=True)

    st.subheader("Available Resumes")
    if st.button("🔄 Refresh List"):
        get_document_list()
        st.rerun()
    if st.session_state.document_list:
        for doc_name in st.session_state.document_list:
            st.markdown(f"- `{doc_name}`")
    else:
        st.info("No resumes uploaded yet.")

    st.markdown("<div class='glow'></div>", unsafe_allow_html=True)

    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = [{"role": "assistant", "content": "Hello, I'm Aegis HR. How can I assist you today?"}]
        st.rerun()


# -------------------- CHAT DISPLAY --------------------
for message in st.session_state.messages:
    if message["role"] == "assistant":
        st.markdown(
            f"""
            <div class="assistant-container">
                <div class="assistant-avatar">{AGENT_AVATAR}</div>
                <div class="assistant-bubble">{message["content"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="user-container">
                <div class="user-bubble">{message["content"]}</div>
                <div class="user-avatar">{USER_AVATAR}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -------------------- CHAT LOGIC --------------------
if prompt := st.chat_input("Ask about resumes, onboarding, or policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    st.markdown(
        f"""
        <div class="user-container">
            <div class="user-bubble">{prompt}</div>
            <div class="user-avatar">{USER_AVATAR}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.chat_message("assistant", avatar=AGENT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        try:
            response = requests.post(CHAT_API_URL, json={"message": prompt}, timeout=180)
            response.raise_for_status()
            ai_response = response.json().get("response", "Sorry, I received an empty response.")
            for chunk in ai_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(f"<div class='typing'>{full_response}</div>", unsafe_allow_html=True)
            message_placeholder.markdown(full_response)
        except requests.exceptions.RequestException as e:
            full_response = f"🚨 Connection Error: {e}"
            message_placeholder.error(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
