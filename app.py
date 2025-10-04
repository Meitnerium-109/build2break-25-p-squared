# app.py
import streamlit as st
import requests
import time

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"
CHAT_API_URL = f"{API_BASE_URL}/chat"
UPLOAD_API_URL = f"{API_BASE_URL}/upload"
DOCS_API_URL = f"{API_BASE_URL}/documents"

AGENT_AVATAR = "🤖"
USER_AVATAR = "🧑‍💻"

st.set_page_config(page_title="Aegis HR - AI Assistant", page_icon=AGENT_AVATAR)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.title("Aegis HR - AI Assistant")
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Aegis HR. How can I help?"}]
if "document_list" not in st.session_state:
    get_document_list()

# --- Functions ---

def get_document_list():
    """Fetches the list of available documents from the API."""
    try:
        response = requests.get(DOCS_API_URL, timeout=10)
        response.raise_for_status()
        st.session_state.document_list = response.json().get("documents", [])
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Failed to get docs: {e}")
        st.session_state.document_list = []

def handle_uploads():
    """Callback function to process uploaded files."""
    if st.session_state.file_uploader:
        st.info("Uploading and processing files...")
        for uploaded_file in st.session_state.file_uploader:
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(UPLOAD_API_URL, files=files, timeout=180)
                if response.status_code == 200:
                    st.success(f"✅ Processed '{uploaded_file.name}'")
                else:
                    st.error(f"❌ Error with '{uploaded_file.name}': {response.json().get('detail')}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error for '{uploaded_file.name}': {e}")
        
        # After processing, refresh the document list.
        # The file_uploader widget is automatically cleared after the callback.
        get_document_list()

# --- Sidebar ---
with st.sidebar:
    st.header("📄 Resume Management")
    
    # File Uploader with the on_change callback
    st.file_uploader(
        "Upload new resumes (PDF)", 
        type="pdf", 
        accept_multiple_files=True,
        key="file_uploader",
        on_change=handle_uploads # <-- THIS IS THE FIX
    )

    st.divider()

    st.header("Available Resumes")
    if st.button("Refresh List"):
        get_document_list()
        st.rerun()

    if st.session_state.document_list:
        for doc_name in st.session_state.document_list:
            st.markdown(f"- `{doc_name}`")
    else:
        st.info("No resumes have been uploaded yet.")

    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Aegis HR. How can I help?"}]
        st.rerun()

# --- Chat Interface ---
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=USER_AVATAR if message["role"] == "user" else AGENT_AVATAR):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about resumes, onboarding, or policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

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
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except:
                error_detail = e.response.text
            full_response = f"⚠️ API Error: {error_detail}"
            message_placeholder.error(full_response)
        except requests.exceptions.RequestException as e:
            full_response = f"🚨 Connection Error: {e}"
            message_placeholder.error(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
