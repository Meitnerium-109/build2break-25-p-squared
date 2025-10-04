# app.py
import streamlit as st
import requests
import time
import os

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/chat"
AGENT_AVATAR = "🤖"
USER_AVATAR = "🧑‍💻"
RESUME_DIR = "resumes"

st.set_page_config(page_title="Aegis HR - AI Assistant", page_icon=AGENT_AVATAR)
st.title("Aegis HR - AI Assistant")

# --- Sidebar for File Upload ---
with st.sidebar:
    st.header("📄 Resume Screening")
    # Change: Allow multiple files to be uploaded
    uploaded_files = st.file_uploader("Upload resumes (PDF)", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        # Ensure the resume directory exists
        if not os.path.exists(RESUME_DIR):
            os.makedirs(RESUME_DIR)

        # Save each uploaded file
        for uploaded_file in uploaded_files:
            file_path = os.path.join(RESUME_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        st.success(f"{len(uploaded_files)} resume(s) uploaded successfully!")
        st.info("The AI agent will restart to load the new resumes. You can then ask questions like 'Compare the candidates based on the uploaded resumes.'")


# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you today?"}]

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=USER_AVATAR if message["role"] == "user" else AGENT_AVATAR):
        st.markdown(message["content"])

# --- Handle User Input ---
if prompt := st.chat_input("Ask about the uploaded resume, onboarding, or policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AGENT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        try:
            response = requests.post(API_URL, json={"message": prompt}, timeout=180) # Increased timeout for RAG
            response.raise_for_status()
            ai_response = response.json().get("response", "Sorry, I encountered an error.")
            for chunk in ai_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except requests.exceptions.RequestException as e:
            full_response = f"Sorry, I couldn't connect to the AI agent. Please ensure the server is running. Error: {e}"
            message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})