# import os
# from dotenv import load_dotenv
# from openai import OpenAI

# load_dotenv()

# client = OpenAI(api_key="OPENAI_API_KEY")

# # ---------- MODELS -------------

# EMBED_MODEL = "text-embedding-3-large"
# CHAT_MODEL = "gpt-4.1-mini"   # fast + cheap, good for RAG


# # ---------- EMBEDDING -----------

# def get_embedding(text: str):

#     resp = client.embeddings.create(
#         model=EMBED_MODEL,
#         input=text,
#     )

#     return resp.data[0].embedding


# # ---------- GENERATION ----------

# def generate_answer(prompt: str):
#     system_msg = """
# आप केवल हिंदी में उत्तर देंगे।
# अगर जानकारी संदर्भ (context) में मौजूद नहीं है तो कहें:
# "आपकी सहायता के लिए हमारे कृषि सहायक जल्द ही आपको कॉल करेंगे। आपके समय और विश्वास के लिए धन्यवाद।"
# अंग्रेज़ी का प्रयोग न करें।
# """

#     response = client.chat.completions.create(
#         model=CHAT_MODEL,
#         messages=[
#             {"role": "system", "content": system_msg},
#             {"role": "user", "content": prompt},
#         ],
#         temperature=0.2,
#     )
#     return response.choices[0].message.content.strip()

import os
# from dotenv import load_dotenv
from openai import OpenAI

# load_dotenv()
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key="OPENAI_API_KEY")
# ---------- MODELS -------------

EMBED_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4o-mini"   # fast + cheap, good for RAG



def rewrite_query(prompt: str):
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a search query rewriter. Only rewrite the query. Do not answer it."
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content.strip()



# ---------- EMBEDDING -----------

def get_embedding(text: str):

    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=text,
    )

    return resp.data[0].embedding


# ---------- GENERATION ----------
def generate_answer(prompt: str, company_name: str):
    system_msg = f""" 
आप {company_name} के क्षेत्र में जानकारी देने वाला सहायक हैं।
सख्त नियम:
1. आप **हमेशा हिंदी में ही जवाब देंगे** — चाहे उपयोगकर्ता ने अंग्रेजी में पूछा हो या हिंदी में।
2. जवाब सरल, स्पष्ट और विनम्र हिंदी में होना चाहिए।
3. आप **केवल** नीचे दिए गए संदर्भ से ही जवाब बनाएँ।
4. संदर्भ से बाहर कोई भी नई जानकारी, सलाह या कंपनी का प्रचार न करें।
5. "कृषि सहायक" या "कॉल" वाली बात **कभी न करें** जब तक कि संदर्भ शून्य न हो।
6. अगर संदर्भ खाली है या बिल्कुल असंबंधित है, तभी कहें:
   "आपकी सहायता के लिए हमारे सहायक से संपर्क किया जाएगा।"

उत्तर हमेशा संदर्भ पर आधारित और उपयोगी होना चाहिए।"""    
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()