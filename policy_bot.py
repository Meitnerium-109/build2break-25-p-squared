# policy_bot.py

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

def create_policy_retriever(file_path, embeddings):
    """
    Creates a retriever for the company policy document.
    This performs the Load, Split, and Store steps of RAG.
    """
    print(f"Processing policy document from: {file_path}")
    loader = TextLoader(file_path)
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    
    db = FAISS.from_documents(docs, embeddings)
    
    print("Policy document processed and retriever created.")
    return db.as_retriever()

def create_policy_bot_chain(retriever, llm):
    """
    Creates the main LangChain chain for the PolicyBot agent.
    The prompt is engineered to be strict and prevent hallucination.
    """
    
    template = """
    You are a helpful and formal HR Policy assistant named "PolicyBot". Your job is to answer questions about company policy using ONLY the provided context.
    If the answer to the question is not contained within the context, you MUST respond with:
    "I'm sorry, I cannot find information about that in the official policy documents."
    Do not make up answers or provide information from outside the context.

    CONTEXT:
    {context}

    QUESTION:
    {question}

    FORMAL ANSWER:
    """
    prompt = PromptTemplate.from_template(template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("PolicyBot chain created successfully.")
    return chain