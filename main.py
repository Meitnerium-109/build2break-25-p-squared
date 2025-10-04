# main.py

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.tools import Tool
from langchain.memory import ConversationBufferWindowMemory

# Import all our specialist agent creators
from talent_scout import create_resume_retriever, create_talent_scout_chain
from onboarder import create_onboarder_chain
from policy_bot import create_policy_retriever, create_policy_bot_chain
from orchestrator import create_orchestrator

def main():
    # --- 1. Setup ---
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # --- 2. Create Specialist Chains ---
    # TalentScout
    resume_retriever = create_resume_retriever("resumes/sample_resume.pdf", embeddings)
    talent_scout_chain = create_talent_scout_chain(resume_retriever, llm)
    
    # Onboarder
    onboarder_chain = create_onboarder_chain(llm)
    
    # PolicyBot
    policy_retriever = create_policy_retriever("policies/company_policies.txt", embeddings)
    policy_bot_chain = create_policy_bot_chain(policy_retriever, llm)

    # --- 3. Define Tools for the Orchestrator ---
    tools = [
        Tool(
            name="TalentScout",
            func=talent_scout_chain.invoke,
            description="Use this tool to screen resumes and analyze candidates. Input should be a detailed question about the candidate's fit for a role."
        ),
        Tool(
            name="Onboarder",
            func=onboarder_chain.invoke,
            description="Use this tool to create an onboarding plan for a new hire. The input should be a single string containing the candidate's full name and their job title."
        ),
        Tool(
            name="PolicyBot",
            func=policy_bot_chain.invoke,
            description="Use this tool to answer questions about company policies. Input should be a direct question about a specific policy."
        ),
    ]

    # --- 4. Create Memory ---
    # k=5 means it will remember the last 5 human/AI message pairs.
    memory = ConversationBufferWindowMemory(
        k=5, 
        memory_key="chat_history", 
        input_key="input", 
        output_key="output", 
        return_messages=True
    )

    # --- 5. Create and Run the Orchestrator ---
    orchestrator = create_orchestrator(llm, tools, memory)
    
    print("\n--- HR Orchestrator is ready. Ask your questions. Type 'exit' to quit. ---")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            
            response = orchestrator.invoke({"input": user_input})
            print(f"Agent: {response['output']}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()