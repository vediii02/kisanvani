from .retriever import retrieve_chunks
from .prompt_templates import build_rag_prompt
from core.llm import llm  # Your LLM interface

def get_rag_advisory(question):
    chunks, hits = retrieve_chunks(question)
    prompt = build_rag_prompt(question, chunks)
    answer = llm.generate(prompt).strip()
    if "दस्तावेज़ों में जानकारी उपलब्ध नहीं है" in answer or not chunks:
        answer = "दस्तावेज़ों में जानकारी उपलब्ध नहीं है।"
    return answer, chunks
