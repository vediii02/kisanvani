ADVISORY_SYSTEM_MESSAGE = """You are a knowledgeable agricultural advisor for Indian farmers. 
Your responses MUST be in Hindi. Provide practical, actionable advice based strictly on the context provided.

IMPORTANT RULES:
1. Only use information from the provided context
2. Never recommend banned products
3. Structure your response in three parts:
   - Abhi kya karein (Immediate action)
   - Agle 48 ghante (Next 48 hours)
   - Aage bachav (Future prevention)
4. Be clear, simple, and actionable
5. If context is insufficient, say so clearly
"""

def create_advisory_prompt(farmer_query: str, context_docs: list) -> str:
    context_text = "\n\n".join([
        f"Document {i+1}:\n{doc.get('content', '')}\nCrop: {doc.get('crop_name', 'N/A')}\nProblem: {doc.get('problem_type', 'N/A')}"
        for i, doc in enumerate(context_docs)
    ])
    
    prompt = f"""Farmer's Question (Hindi):
{farmer_query}

Relevant Knowledge Base Context:
{context_text}

Provide a detailed advisory in Hindi following the three-part structure:
1. अभी क्या करें (Immediate action)
2. अगले 48 घंटे (Next 48 hours)
3. आगे बचाव (Future prevention)
"""
    return prompt

def build_rag_prompt(question, retrieved_chunks):
    context = "\n\n".join(f"• {chunk}" for chunk in retrieved_chunks)
    return f"""
आपको केवल नीचे दिए गए दस्तावेज़ अंशों का उपयोग करके किसान के सवाल का उत्तर देना है।
नियम:
- केवल दस्तावेज़ों की जानकारी का उपयोग करें, अनुमान या नया सुझाव न दें।
- अगर दस्तावेज़ों में उत्तर नहीं है, तो कहें: 'दस्तावेज़ों में जानकारी उपलब्ध नहीं है।'
- उत्तर सरल, स्पष्ट और किसान के लिए उपयोगी हिंदी में दें।

किसान का सवाल:
{question}

दस्तावेज़ अंश:
{context}

उत्तर:
"""