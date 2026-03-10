import os
import argparse
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configuration
STATIC_PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "pdfs")
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "crop_diagnostics"

def ingest_pdfs(file_path: str = None):
    if file_path:
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return
        # Use absolute path and basename for metadata
        file_path = os.path.abspath(file_path)
        pdf_files = [file_path]
        print(f"Single file mode: {file_path}")
    else:
        if not os.path.exists(STATIC_PDF_DIR):
            print(f"Directory {STATIC_PDF_DIR} does not exist. Creating it.")
            os.makedirs(STATIC_PDF_DIR)
            return

        pdf_files = [os.path.join(STATIC_PDF_DIR, f) for f in os.listdir(STATIC_PDF_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found to process.")
        return

    print(f"Found {len(pdf_files)} PDF files. Initializing embeddings and vector store...")
    
    # Using OpenAI embeddings by default as per existing llm.py logic
    # Make sure OPENAI_API_KEY is in .env
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Initialize SemanticChunker (Similarity-based chunking as requested)
    text_splitter = SemanticChunker(embeddings)

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

    for pdf_file_path in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_filename = os.path.basename(pdf_file_path)
        try:
            loader = PyPDFLoader(pdf_file_path)
            documents = loader.load()
            
            # Split documents using SemanticChunker
            chunks = text_splitter.split_documents(documents)
            
            # Add metadata
            for chunk in chunks:
                chunk.metadata["source"] = pdf_filename
            
            vector_store.add_documents(chunks)
            print(f"\nSuccessfully ingested {pdf_filename} ({len(chunks)} chunks)")
        except Exception as e:
            print(f"\nError processing {pdf_filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDFs into ChromaDB for diagnostics.")
    parser.add_argument("--file", help="Path to a specific PDF file to ingest.")
    parser.add_argument("--path", help="Alias for --file.")
    args = parser.parse_args()
    
    target_file = args.file or args.path
    ingest_pdfs(target_file)
