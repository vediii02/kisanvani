import streamlit as st
import os
import tempfile
import time

from loader import load_file
from chunker import chunk_text
from openai_client import get_embedding, generate_answer

from pinecone_db import create_index_if_not_exists, get_index

st.set_page_config(page_title="RAG Chatbot", layout="wide")

st.title("📄 RAG Chatbot — Pinecone + Gemini")

# ---------------- Sidebar -----------------

st.sidebar.header("Upload & Ingest")

uploaded_files = st.sidebar.file_uploader(
    "Upload documents",
    type=["pdf", "xlsx", "xls", "json"],
    accept_multiple_files=True,
)
def rewrite_query_with_history(user_query):

    history_text = ""

    for msg in st.session_state.messages:
        history_text += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
You are a query rewriter for a retrieval system.

Given the conversation history and the latest user message,
rewrite the user message into a standalone search query.

If the user is asking about the conversation itself
return exactly: __HISTORY_QUERY__.

Conversation History:
{history_text}

Latest User Message:
{user_query}

Standalone Query:
"""

    rewritten = generate_answer(prompt).strip()

    return rewritten

def handle_history_question():

    questions = [
        msg["content"]
        for msg in st.session_state.messages
        if msg["role"] == "user"
    ]

    if not questions:
        return "You haven't asked anything yet."

    result = "You asked:\n\n"
    for q in questions:
        result += f"- {q}\n"

    return result



# -------------- INGEST -------------------

def ingest_files(files):
    
    create_index_if_not_exists()
    index = get_index()

    for file in files:
        print("files=-------------",files)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
            print(tmp_path,"tmp_path----------")

        st.sidebar.write(f"Processing {file.name}...")
        print(file.name,"file-----------")
        filename=file.name
        text = load_file(tmp_path,filename)
        chunks = chunk_text(text)
        print("chunks---------",chunks)

        for chunk in chunks:

            emb = get_embedding(chunk)

            index.upsert(
                [
                    {
                        "id": f"{file.name}-{hash(chunk)}",
                        "values": emb,
                        "metadata": {
                            "source": file.name,
                            "text": chunk,
                        },
                    }
                ]
            )   

            time.sleep(1.1)

        os.remove(tmp_path)

ingest_btn = st.sidebar.button("📤 Ingest to Pinecone")

if ingest_btn:

    if not uploaded_files:
        st.sidebar.error("Upload files first.")
    else:
        with st.sidebar.spinner("Ingesting documents..."):
            ingest_files(uploaded_files)

        st.sidebar.success("✅ Ingestion complete!")

# -------------- CHAT ---------------------

st.header("💬 Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def retrieve_context(question):

    index = get_index()
    q_embedding = get_embedding(question)

    result = index.query(
        vector=q_embedding,
        top_k=5,
        include_metadata=True,
    )

    return "\n\n".join(
        m["metadata"]["text"] for m in result["matches"]
    )


def build_prompt(context, question):

    return f"""
You are a helpful assistant.

Answer ONLY from the context.

Context:
{context}

Question:
{question}
"""


# Input box
prompt = st.chat_input("Ask your documents...")

if prompt:

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):

        rewritten_query = rewrite_query_with_history(prompt)

        print("Rewritten Query:", rewritten_query)

        # ---- history-based question ----
        if "__HISTORY_QUERY__" in rewritten_query:
            
            answer = handle_history_question()

        else:

            context = retrieve_context(rewritten_query)

            final_prompt = build_prompt(context, prompt)

            answer = generate_answer(final_prompt)


    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    with st.chat_message("assistant"):
        st.markdown(answer)
