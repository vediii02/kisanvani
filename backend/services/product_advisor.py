import os
from services.product_rules import PRODUCT_RULES

BASE_PRODUCT_PATH = "backend/data/raw/products/kisan_vani_demo"


def load_product(product_file: str) -> str:
    path = os.path.join(BASE_PRODUCT_PATH, product_file)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def find_product(user_query: str) -> str | None:
    for rule in PRODUCT_RULES:
        if rule["problem_keyword"] in user_query:
            return rule["product_file"]
    return None
PRODUCT_PROMPT_TEMPLATE = """
नीचे दी गई जानकारी के आधार पर किसान को सुझाव दो।

नियम:
- उत्पाद को सुझाव की तरह बताओ, आदेश की तरह नहीं
- यह स्पष्ट करो कि यह हमारी संस्था का उत्पाद है
- जबरदस्ती न बेचो
- अंतिम निर्णय किसान का होना चाहिए
- उत्तर 2–3 वाक्यों में रखो

किसान की समस्या:
{question}

कृषि सलाह:
{agri_answer}

उत्पाद जानकारी:
{product_info}
"""
def generate_final_answer(user_query: str, agri_answer: str, llm) -> str:
    product_file = find_product(user_query)

    # Agar koi product match nahi hota
    if not product_file:
        return agri_answer

    product_info = load_product(product_file)

    prompt = PRODUCT_PROMPT_TEMPLATE.format(
        question=user_query,
        agri_answer=agri_answer,
        product_info=product_info
    )

    product_suggestion = llm.generate(prompt).strip()

    final_answer = f"{agri_answer}\n\n{product_suggestion}"
    return final_answer

