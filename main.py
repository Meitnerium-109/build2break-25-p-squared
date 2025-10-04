# main.py
import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import List

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.tools import Tool
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentExecutor

# Local Imports
from vectorstore_manager import VectorStoreManager
from talent_scout import create_talent_scout_chain
from onboarder import create_onboarder_chain
from policy_bot import create_policy_retriever, create_policy_bot_chain
from orchestrator import create_orchestrator

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file.")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
REQUEST_TIMEOUT = 120.0  # 120 seconds

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class UploadResponse(BaseModel):
    message: str
    filename: str

class DocumentListResponse(BaseModel):
    documents: List[str]

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Aegis HR - Agentic HR Automation (Hardened)",
    description="A robust API for the multi-agent HR system.",
    version="2.1.0" # Version bump
)

# --- Global Components ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3, google_api_key=API_KEY)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=API_KEY)
vector_store_manager = VectorStoreManager(embeddings=embeddings)
orchestrator: AgentExecutor = None

# --- FastAPI Startup Event ---
@app.on_event("startup")
async def startup_event():
    global orchestrator
    print("--- Server is starting up, initializing AI agent... ---")
    
    retriever = vector_store_manager.get_retriever()
    
    talent_scout_chain = create_talent_scout_chain(retriever, llm)
    onboarder_chain = create_onboarder_chain(llm)
    policy_retriever = create_policy_retriever("policies/company_policies.txt", embeddings)
    policy_bot_chain = create_policy_bot_chain(policy_retriever, llm)

    tools = [
        Tool(name="TalentScout", func=talent_scout_chain.invoke, description="For screening resumes, comparing candidates, and analyzing skills."),
        Tool(name="Onboarder", func=onboarder_chain.invoke, description="For creating onboarding plans."),
        Tool(name="PolicyBot", func=policy_bot_chain.invoke, description="For answering questions about company policies."),
    ]

    memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history", input_key="input", output_key="output", return_messages=True)
    orchestrator = create_orchestrator(llm, tools, memory)
    
    print("--- AI Agent initialized successfully. Server is ready. ---")

# --- Robust Endpoints ---

@app.get("/documents", response_model=DocumentListResponse)
async def get_documents():
    """
    NEW ENDPOINT: Returns a list of all unique documents in the vector store.
    """
    try:
        doc_list = vector_store_manager.list_documents()
        return {"documents": doc_list}
    except Exception as e:
        print(f"!!! Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document list: {str(e)}")


@app.post("/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File size exceeds limit of {MAX_FILE_SIZE / 1024 / 1024} MB.")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are accepted.")

    try:
        vector_store_manager.add_document_from_upload(file)
        return {"message": "File processed successfully.", "filename": file.filename}
    except Exception as e:
        print(f"!!! Critical error during file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="AI Agent is not ready.")
    
    try:
        response = await asyncio.wait_for(
            orchestrator.ainvoke({"input": request.message}),
            timeout=REQUEST_TIMEOUT
        )
        return {"response": response.get('output', "No output from agent.")}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out.")
    except Exception as e:
        print(f"!!! Critical error in agent chain: {e}")
        raise HTTPException(status_code=500, detail=f"Internal agent error: {str(e)}")
