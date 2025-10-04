# app.py
import streamlit as st
import requests
import time

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"
CHAT_API_URL = f"{API_BASE_URL}/chat"
UPLOAD_API_URL = f"{API_BASE_URL}/upload"
DOCS_API_URL = f"{API_BASE_URL}/documents" # New endpoint URL

AGENT_AVATAR = "🤖"
USER_AVATAR = "🧑‍💻"

st.set_page_config(page_title="Aegis HR - AI Assistant", page_icon=AGENT_AVATAR)
st.title("Aegis HR - AI Assistant")

# --- Function to fetch the document list ---
def get_document_list():
    try:
        response = requests.get(DOCS_API_URL, timeout=10)
        response.raise_for_status()
        return response.json().get("documents", [])
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Failed to get docs: {e}")
        return []

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Aegis HR. How can I help?"}]
# Fetch initial document list when the app loads
if "document_list" not in st.session_state:
    st.session_state.document_list = get_document_list()

# --- Sidebar ---
with st.sidebar:
    st.header("📄 Resume Management")
    
    # --- File Uploader ---
    uploaded_files = st.file_uploader("Upload new resumes (PDF)", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        st.info("Uploading and processing files...")
        for uploaded_file in uploaded_files:
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(UPLOAD_API_URL, files=files, timeout=180)
                if response.status_code == 200:
                    st.success(f"✅ Processed '{uploaded_file.name}'")
                else:
                    st.error(f"❌ Error with '{uploaded_file.name}': {response.json().get('detail')}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error for '{uploaded_file.name}': {e}")
        # Refresh the document list after uploads
        st.session_state.document_list = get_document_list()
        st.rerun() # Rerun the script to display the new list immediately

    st.divider()

    # --- Persistent Document List Display ---
    st.header("Available Resumes")
    if st.button("Refresh List"):
        st.session_state.document_list = get_document_list()
        st.rerun()

    if st.session_state.document_list:
        for doc_name in st.session_state.document_list:
            st.markdown(f"- `{doc_name}`")
    else:
        st.info("No resumes have been uploaded yet.")

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