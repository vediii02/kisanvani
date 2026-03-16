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


def ingest_pdfs(file_path: str = None):

    if file_path:
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return

        file_path = os.path.abspath(file_path)
        pdf_files = [file_path]
        print(f"Single file mode: {file_path}")

    else:
        if not os.path.exists(STATIC_PDF_DIR):
            print(f"Directory {STATIC_PDF_DIR} does not exist. Creating it.")
            os.makedirs(STATIC_PDF_DIR)
            return

        pdf_files = [
            os.path.join(STATIC_PDF_DIR, f)
            for f in os.listdir(STATIC_PDF_DIR)
            if f.lower().endswith(".pdf")
        ]

    if not pdf_files:
        print("No PDF files found to process.")
        return

    print(f"Found {len(pdf_files)} PDF files. Initializing embeddings...")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Semantic chunking
    text_splitter = SemanticChunker(embeddings)

    for pdf_file_path in tqdm(pdf_files, desc="Processing PDFs"):

        pdf_filename = os.path.basename(pdf_file_path)

        # Create collection name from file name (sanitized for ChromaDB)
        base_name = os.path.splitext(pdf_filename)[0].lower()
        # Replace non-alphanumeric (except _ and -) with _
        clean_name = "".join([c if c.isalnum() or c in ("_", "-") else "_" for c in base_name])
        # Ensure it doesn't start/end with non-alphanumeric (Chroma rule)
        clean_name = clean_name.strip("_").strip("-")
        # Ensure it's between 3 and 63 chars
        collection_name = clean_name[:63]
        if len(collection_name) < 3:
            collection_name = f"col_{collection_name}" if collection_name else "default_collection"

        try:
            loader = PyPDFLoader(pdf_file_path)
            documents = loader.load()

            chunks = text_splitter.split_documents(documents)

            # Add metadata
            for chunk in chunks:
                chunk.metadata["source"] = pdf_filename

            # Create vector store PER PDF
            vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=CHROMA_DB_DIR
            )

            vector_store.add_documents(chunks)

            print(
                f"\nSuccessfully ingested {pdf_filename} "
                f"into collection '{collection_name}' ({len(chunks)} chunks)"
            )

        except Exception as e:
            print(f"\nError processing {pdf_filename}: {e}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Ingest PDFs into ChromaDB for diagnostics."
    )

    parser.add_argument("--file", help="Path to a specific PDF file to ingest.")
    parser.add_argument("--path", help="Alias for --file.")

    args = parser.parse_args()

    target_file = args.file or args.path

    ingest_pdfs(target_file)