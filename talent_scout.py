# talent_scout.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# NOTE: This file is now correct and does not import from itself.

def create_talent_scout_chain(retriever, llm):
    """
    Creates the main LangChain chain for the TalentScout agent.
    This version has a completely overhauled, stricter prompt for better formatting and completeness.
    """
    
    template = """
    You are an expert HR analyst, TalentScout. Your only job is to analyze and rank candidates based on the resume context provided.

    **CONTEXT FROM RESUMES:**
    {context}

    **USER'S QUESTION:**
    {question}

    **CRITICAL RULES FOR YOUR RESPONSE:**
    1.  **INCLUDE EVERYONE:** You MUST analyze every candidate found in the context. Do not omit any candidate.
    2.  **EXTRACT NAME:** You MUST find the full name of each candidate. If a name is not in the resume, you MUST state "Name Not Found".
    3.  **RANK AND JUSTIFY:** Provide a numbered priority list. For each candidate, you MUST briefly justify your ranking.
    4.  **STRICT MARKDOWN FORMAT:** Your final output MUST use the exact Markdown format below. Use headings, bold text, and dashes for bullet points.

    ### Candidate Ranking

    Based on your request, here is the priority order of the candidates:

    ---
    **1. Candidate Name**
    - **Source:** `[source_filename.pdf]`
    - **Justification:** [Explain why this candidate is ranked first based on their skills and experience.]
    - **Summary:** [Provide a brief summary of the candidate's profile.]

    ---
    **2. Candidate Name**
    - **Source:** `[source_filename.pdf]`
    - **Justification:** [Explain why this candidate is ranked second.]
    - **Summary:** [Provide a brief summary of the candidate's profile.]

    ---
    **3. Candidate Name (or Name Not Found)**
    - **Source:** `[source_filename.pdf]`
    - **Justification:** [Explain why this candidate is ranked third.]
    - **Summary:** [Provide a brief summary of the candidate's profile.]
    
    (Continue for all other candidates)
    """
    prompt = PromptTemplate.from_template(template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("TalentScout chain created successfully (Final Overhauled Version).")
    return chain