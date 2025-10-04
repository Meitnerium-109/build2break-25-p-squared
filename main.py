# main.py

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# LangChain Imports
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.tools import Tool
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentExecutor

# Import all our specialist agent creators
from talent_scout import create_multi_resume_retriever, create_talent_scout_chain
from onboarder import create_onboarder_chain
from policy_bot import create_policy_retriever, create_policy_bot_chain
from orchestrator import create_orchestrator

# --- 1. Pydantic Model for API Request ---
class ChatRequest(BaseModel):
    message: str

# --- 2. FastAPI App Initialization ---
app = FastAPI(
    title="Aegis HR - Agentic HR Automation",
    description="An API for the multi-agent HR system.",
    version="1.0.0"
)

# --- 3. Global Variable for the Agent ---
orchestrator: AgentExecutor = None

# --- 4. FastAPI Startup Event ---
@app.on_event("startup")
async def startup_event():
    """
    Initializes the AI agent and all its components when the server starts.
    """
    global orchestrator
    print("--- Server is starting up, initializing AI agent... ---")
    
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    
    # Initialize the LLM and Embeddings models
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
    # CORRECTED: Use the correct model name for embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # --- This block is updated to load all resumes ---
    resumes_directory = "resumes"
    resume_retriever = create_multi_resume_retriever(resumes_directory, embeddings)
    
    # Create an empty list for tools first
    tools = []

    # Only add the TalentScout tool if resumes were successfully loaded
    if resume_retriever:
        talent_scout_chain = create_talent_scout_chain(resume_retriever, llm)
        tools.append(
            Tool(
                name="TalentScout",
                func=talent_scout_chain.invoke,
                description="Use this tool to screen resumes, compare candidates, and analyze skills based on all uploaded resume contexts. Input should be a detailed question about the candidates."
            )
        )
    else:
        print("--- TalentScout tool is disabled because no resumes were loaded. ---")

    
    onboarder_chain = create_onboarder_chain(llm)
    
    policy_retriever = create_policy_retriever("policies/company_policies.txt", embeddings)
    policy_bot_chain = create_policy_bot_chain(policy_retriever, llm)

    # Add the other tools to the list
    tools.extend([
        Tool(
            name="Onboarder",
            func=onboarder_chain.invoke,
            description="Use this tool to create an onboarding plan. The input should be a string containing the candidate's name, job title, and optionally the desired plan duration and word count. Example: 'Jane Doe, Software Engineer, 3 days, 150 words'"
        ),
        Tool(
            name="PolicyBot",
            func=policy_bot_chain.invoke,
            description="Use this tool to answer questions about company policies. Input should be a direct question about a specific policy."
        ),
    ])

    # Create the memory for the conversation
    memory = ConversationBufferWindowMemory(
        k=5, 
        memory_key="chat_history", 
        input_key="input", 
        output_key="output", 
        return_messages=True
    )

    # Create the main orchestrator agent
    orchestrator = create_orchestrator(llm, tools, memory)
    
    print("--- AI Agent initialized successfully. Server is ready. ---")


# --- 5. FastAPI Chat Endpoint ---
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Receives a message from the user, passes it to the AI agent,
    and returns the agent's response.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="AI Agent is not initialized yet. Please wait a moment.")
    
    try:
        response = orchestrator.invoke({"input": request.message})
        return {"response": response['output']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred in the agent: {e}")