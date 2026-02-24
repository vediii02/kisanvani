import os

# ===============================
# CONFIG & CONSTANTS
# ===============================

BASE_CHUNK_PATH = "backend/data/processed/chunks/soybean"

KEYWORD_TO_CHUNK = {
    "पीली": "soybean_04_peeli_patti.txt",
    "पीला": "soybean_04_peeli_patti.txt",
    "फूल": "soybean_05_phool_girna.txt",
    "फल": "soybean_05_phool_girna.txt",
    "पानी": "soybean_09_sinchai.txt",
    "सिंचाई": "soybean_09_sinchai.txt",
    "कीट": "soybean_07_keet_prabandhan.txt",
    "रोग": "soybean_08_rog_prabandhan.txt",
}

DEFAULT_CHUNK = "soybean_01_parichay.txt"


# ===============================
# AI PROMPT (ALWAYS ABOVE FUNCTIONS)
# ===============================

PROMPT_TEMPLATE = """
तुम एक अनुभवी कृषि सलाहकार हो।

नियम:
- केवल नीचे दी गई जानकारी का उपयोग करो
- कोई अनुमान मत लगाओ
- सरल, बोली-चाल की हिंदी में बोलो
- खाद या दवा का नाम मत बताओ
- उत्तर 4–5 वाक्यों में रखो

किसान का सवाल:
{question}

जानकारी:
{context}
"""


# ===============================
# HELPER FUNCTIONS
# ===============================

def load_chunk(chunk_file: str) -> str:
    path = os.path.join(BASE_CHUNK_PATH, chunk_file)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def find_relevant_chunk(user_query: str) -> str:
    for keyword, chunk in KEYWORD_TO_CHUNK.items():
        if keyword in user_query:
            return chunk
    return DEFAULT_CHUNK


def generate_answer(user_query: str, llm) -> str:
    chunk_file = find_relevant_chunk(user_query)
    chunk_text = load_chunk(chunk_file)

    prompt = PROMPT_TEMPLATE.format(
        question=user_query,
        context=chunk_text
    )

    response = llm.generate(prompt)
    return response.strip()
