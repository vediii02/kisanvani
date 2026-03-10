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

def ingest_pdfs():
    if not os.path.exists(STATIC_PDF_DIR):
        print(f"Directory {STATIC_PDF_DIR} does not exist. Creating it.")
        os.makedirs(STATIC_PDF_DIR)
        return

    pdf_files = [f for f in os.listdir(STATIC_PDF_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in {STATIC_PDF_DIR}")
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

    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        file_path = os.path.join(STATIC_PDF_DIR, pdf_file)
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            # Split documents using SemanticChunker
            chunks = text_splitter.split_documents(documents)
            
            # Add metadata
            for chunk in chunks:
                chunk.metadata["source"] = pdf_file
            
            vector_store.add_documents(chunks)
            print(f"\nSuccessfully ingested {pdf_file} ({len(chunks)} chunks)")
        except Exception as e:
            print(f"\nError processing {pdf_file}: {e}")

if __name__ == "__main__":
    ingest_pdfs()
