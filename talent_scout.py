# talent_scout.py

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

def create_resume_retriever(pdf_path, embeddings):
    """
    Creates a retriever for a given resume PDF.
    
    This function performs the Load, Split, and Store steps of RAG.
    1. Loads the PDF.
    2. Splits the document into smaller chunks.
    3. Creates embeddings for these chunks.
    4. Stores them in a FAISS vector store.
    5. Returns a retriever object which can find relevant chunks.
    """
    print(f"Processing resume from: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    # Split the document into chunks for effective searching
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    
    # Create a FAISS vector store from the document chunks
    # This is our in-memory "database" of the resume's content
    db = FAISS.from_documents(docs, embeddings)
    
    # Return the vector store as a retriever
    # A retriever is a component that can fetch relevant documents
    print("Resume processed and retriever created.")
    return db.as_retriever()

def create_talent_scout_chain(retriever, llm):
    """
    Creates the main LangChain chain for the TalentScout agent.
    
    This function builds the Retrieve and Generate steps of RAG.
    1. Defines a prompt template to guide the LLM.
    2. Sets up a chain that:
        - Takes a user's question.
        - Uses the retriever to fetch relevant context from the resume.
        - Formats the prompt with the context and question.
        - Sends it to the LLM.
        - Parses the output.
    """
    
    template = """
    You are an expert HR assistant named TalentScout. Your task is to analyze the provided resume context and answer the question based ONLY on that context.
    Do not make up information. If the answer is not in the context, say "The information is not available in the provided resume."

    CONTEXT:
    {context}

    QUESTION:
    {question}

    ANSWER:
    """
    prompt = PromptTemplate.from_template(template)

    # This is the LangChain Expression Language (LCEL) chain
    # It defines the sequence of operations.
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("TalentScout chain created successfully.")
    return chain