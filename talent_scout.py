# talent_scout.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

def create_multi_resume_retriever(resumes_dir, embeddings):
    """
    Creates a single, more powerful retriever for all resumes in a directory.
    It now fetches more documents to ensure all resumes are included.
    """
    all_docs = []
    print(f"--- Loading all resumes from: {resumes_dir} ---")
    
    if not os.path.exists(resumes_dir):
        print(f"Warning: Directory '{resumes_dir}' not found. No resumes will be loaded.")
        return None
        
    pdf_files = [f for f in os.listdir(resumes_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"Warning: No PDF resumes found in '{resumes_dir}'.")
        return None

    for pdf_file in pdf_files:
        pdf_path = os.path.join(resumes_dir, pdf_file)
        try:
            print(f"Processing resume: {pdf_file}")
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            for doc in documents:
                doc.metadata["source"] = pdf_file
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            split_docs = text_splitter.split_documents(documents)
            all_docs.extend(split_docs)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    if not all_docs:
        print("--- No resume content could be loaded. TalentScout will be disabled. ---")
        return None

    db = FAISS.from_documents(all_docs, embeddings)
    
    # --- KEY CHANGE ---
    # We are now configuring the retriever to fetch more documents (k=15).
    # This forces it to look at a wider range of information, making it
    # highly likely to include context from ALL uploaded resumes.
    retriever = db.as_retriever(search_kwargs={"k": 15})
    
    print(f"--- All {len(pdf_files)} resumes processed. Retriever is ready (Enhanced Fetching). ---")
    return retriever

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
    4.  **STRICT MARKDOWN FORMAT:** Your final output MUST use the exact Markdown format below. Use headings, bold text, and bullet points as shown. Do not use asterisks for lists; use dashes.

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