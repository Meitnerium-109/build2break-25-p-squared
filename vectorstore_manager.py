# vectorstore_manager.py
import os
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Local Imports
from security import create_guardrails_agent, sanitize_text_chunk # Import sanitize_text_chunk

# --- Configuration ---
PERSIST_DIRECTORY = "chroma_db"
CHROMA_COLLECTION_NAME = "hr_documents"

class VectorStoreManager:
    """
    Manages the persistent vector store for the application.
    Handles initialization, adding documents, and providing a retriever.
    """
    def __init__(self, embeddings, llm=None):  # Added llm as an argument
        self.embeddings = embeddings
        self.llm = llm # Store the llm instance
        
        # Initialize the persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        
        # Initialize the LangChain Chroma vector store
        self.vector_store = Chroma(
            client=self.client,
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
        )
        
        # Initialize the guardrails agent here to avoid re-initialization
        self.guardrails_agent = None
        if self.llm:
            self.guardrails_agent = create_guardrails_agent(self.llm) # Use self.llm
        
        print(f"--- VectorStoreManager initialized. Using '{PERSIST_DIRECTORY}' for storage. ---")
        print(f"Current document count: {self.vector_store._collection.count()}")

    def add_document_from_upload(self, uploaded_file):
        """
        Processes an uploaded file, splits it into chunks, and adds it to the vector store.
        The file is saved temporarily for processing and then deleted.
        """
        temp_dir = "temp_uploads"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        temp_filepath = os.path.join(temp_dir, uploaded_file.filename)

        try:
            # Save the uploaded file temporarily
            with open(temp_filepath, "wb") as buffer:
                buffer.write(uploaded_file.file.read())

            # Load the PDF
            print(f"--- Processing document: {uploaded_file.filename} ---")
            loader = PyPDFLoader(temp_filepath)
            documents = loader.load()
            
            # Add source metadata to each document chunk
            for doc in documents:
                doc.metadata["source"] = uploaded_file.filename
            
            # Split the document into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.split_documents(documents)

            # Sanitize each document chunk before adding it to the vector store
            if self.guardrails_agent:
                sanitized_docs = []
                for doc in docs:
                    # Ensure doc has page_content attribute
                    if hasattr(doc, 'page_content'):
                        doc.page_content = sanitize_text_chunk(doc.page_content, self.guardrails_agent)
                    else:
                        print(f"Warning: Document chunk missing 'page_content'. Skipping sanitization.")
                    sanitized_docs.append(doc)
                docs = sanitized_docs

            # Add the documents to the persistent vector store
            self.vector_store.add_documents(docs)
            
            print(f"--- Document '{uploaded_file.filename}' added successfully. ---")
            print(f"New document count: {self.vector_store._collection.count()}")
            
        except Exception as e:
            print(f"!!! Error processing document {uploaded_file.filename}: {e}")
            raise
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

    def get_retriever(self, k_value=15):
        """
        Returns a retriever from the vector store.
        """
        return self.vector_store.as_retriever(search_kwargs={"k": k_value})

    def list_documents(self) -> list[str]:
        """
        NEW METHOD: Lists the unique source documents currently in the vector store.
        """
        # The .get() method without IDs fetches all entries in the collection
        collection_data = self.vector_store._collection.get()
        metadatas = collection_data.get('metadatas', [])
        
        if not metadatas:
            return []
        
        # Extract unique source filenames from the metadata
        source_files = {meta['source'] for meta in metadatas if 'source' in meta}
        return sorted(list(source_files))
