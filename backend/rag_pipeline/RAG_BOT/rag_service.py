
# from rag_pipeline.RAG_BOT.openai_client import (
#     get_embedding,
#     generate_answer,
# )
# from rag_pipeline.RAG_BOT.pinecone_db import get_index

# # ---------------------------
# # HISTORY STORAGE
# # ---------------------------

# messages = []


# # ---------------------------
# # QUERY REWRITER
# # ---------------------------

# def rewrite_query_with_history(user_query: str):

#     history_text = ""

#     for msg in messages:
#         history_text += f"{msg['role']}: {msg['content']}\n"

#     prompt = f"""
# You are a query rewriter for a retrieval system.

# Given the conversation history and the latest user message,
# rewrite the user message into a standalone search query.

# If the user is asking about the conversation itself
# return exactly: __HISTORY_QUERY__.

# Conversation History:
# {history_text}

# Latest User Message:
# {user_query}

# Standalone Query:
# """ 
#     return generate_answer(prompt).strip()


# # ---------------------------
# # HISTORY QUESTION HANDLER
# # ---------------------------

# def handle_history_question():

#     questions = [
#         msg["content"]
#         for msg in messages
#         if msg["role"] == "user"
#     ]

#     if not questions:
#         return "You haven't asked anything yet."

#     result = "You asked:\n\n"
#     for q in questions:
#         result += f"- {q}\n"

#     return result


# # ---------------------------
# # RETRIEVAL
# # ---------------------------

# def retrieve_context(question):

#     index = get_index()
   
#     q_embedding = get_embedding(question)

#     result = index.query(
#         vector=q_embedding,
#         top_k=5,
#         include_metadata=True,
#     )

#     return "\n\n".join(
#         m["metadata"]["text"]
#         for m in result["matches"]
#     )


# def build_prompt(context, question):

#     return f"""
# You are a helpful assistant.

# Answer ONLY from the context.

# Context:
# {context}

# Question:
# {question}
# """

# # ---------------------------
# # MAIN ENTRY FUNCTION
# # ---------------------------

# def run_rag_chat(user_input: str) -> str:
#     messages.append({"role": "user", "content": user_input})

#     # rewritten_query = rewrite_query_with_history(user_input)

#     # if "__HISTORY_QUERY__" in rewritten_query:
#     #     answer = handle_history_question()
#     # else:
#         # context = retrieve_context(rewritten_query)
#     context = retrieve_context(user_input)
#     final_prompt = build_prompt(context, user_input)
#     answer = generate_answer(final_prompt)

#     messages.append({"role": "assistant", "content": answer})

#     return answer

# if __name__ == "__main__":

#     print("\n📥 INGEST DOCUMENTS FIRST")

#     # folder = input("Enter folder path containing docs: ")

#     # ingest_files_from_folder(folder)

#     run_rag_chat("provide the summary of data you have")



from rag_pipeline.RAG_BOT.openai_client import (
    get_embedding,
    generate_answer,
    rewrite_query,   # separate neutral rewriter
)
from rag_pipeline.RAG_BOT.pinecone_db import get_index

# from openai_client import (
#     get_embedding,
#     generate_answer,
#     rewrite_query,   # separate neutral rewriter
# )
# from pinecone_db import get_index

# ---------------------------
# SESSION STORAGE (In-memory)
# ---------------------------

chat_sessions = {}


# ---------------------------
# QUERY REWRITER
# ---------------------------

def rewrite_query_with_history(user_query: str, history: list):

    history_text = ""

    for msg in history[-5:]:
        history_text += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
You are a search query rewriter.

Your task:
Convert the latest user question into a fully standalone search query.

Rules:
- Do NOT answer the question.
- Do NOT invent unrelated information.
- If the latest question is incomplete but clearly continues the same topic 
  from recent conversation, infer the missing part from context.
- Clarify references like "its", "that product", etc.
- If already standalone, return it unchanged.

Conversation History:
{history_text}

Latest Question:
{user_query}

Standalone Search Query:
"""


    rewritten = rewrite_query(prompt)

    return rewritten.strip()


# ---------------------------
# RETRIEVAL (Namespace Isolation)
# ---------------------------

def retrieve_context(question: str, company_id: str):
    index = get_index()
    q_embedding = get_embedding(question)

    result = index.query(
        vector=q_embedding,
        top_k=5,
        include_metadata=True,
        namespace=company_id,   # 🔐 strict isolation
    )


    # print("----------retrieval_context-----------", result)

    if not result["matches"]:
        print("No relevant context found for the query.")
        return ""

    return "\n\n".join(
        m["metadata"]["text"]
        for m in result["matches"]
    )



# ---------------------------
# PROMPT BUILDER
# ---------------------------

def build_prompt(context: str, question: str):
    return f"""
आप केवल नीचे दिए गए संदर्भ (context) के आधार पर उत्तर दें।

संदर्भ:
{context}

प्रश्न:
{question}
"""

# ---------------------------
# MAIN CHAT FUNCTION
# ---------------------------

def run_rag_chat(
    user_input: str,
    company_id: str,
    company_name: str,
    session_id: str
) -> str:

    # Initialize session if not exists
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    session_history = chat_sessions[session_id]

    print("-----------session history-----------" , session_history)


    # 🔥 Rewrite query BEFORE adding current message
    rewritten_query = rewrite_query_with_history(
        user_input,
        session_history
    )

    print("-----------------Rewritten Query------------------:", rewritten_query)

    # Retrieve context using namespace isolation
    context = retrieve_context(rewritten_query, company_id)
    # print("-------------------context retrieved:---------------------", context)

    # If no relevant data found → fallback
    if not context:
        # print("-------------------No context found, using fallback response.-------------------")
        fallback = "आपकी सहायता के लिए हमारे कृषि सहायक जल्द ही आपको कॉल करेंगे। आपके समय और विश्वास के लिए धन्यवाद।"

        # Store conversation
        session_history.append({"role": "user", "content": user_input})
        session_history.append({"role": "assistant", "content": fallback})

        return fallback

    # Build final answer prompt
    final_prompt = build_prompt(context, user_input)

    # print("-------------------Final Prompt for Generation-------------------", final_prompt)

    # Generate company-restricted response
    answer = generate_answer(final_prompt, company_name)

    # Store conversation
    session_history.append({"role": "user", "content": user_input})
    session_history.append({"role": "assistant", "content": answer})

    return answer


# ---------------------------
# CLI TEST MODE (Optional)
# ---------------------------

if __name__ == "__main__":

    company_id=101
    company_id=str(company_id)
    company_name="AI"
    session_id="session_7"


    print("Chatbot started. Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        response = run_rag_chat(
            user_input,
            company_id,
            company_name,
            session_id
        )

        print("Bot:", response)

