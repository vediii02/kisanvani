# from pinecone import Pinecone, ServerlessSpec
# import os
# from dotenv import load_dotenv

# load_dotenv()

# PINECONE_API_KEY="pcsk_qZEVC_FkvQvWuQzKxcuGs1fFWGYeh1TAq4nKdVaXnhunsVM4VSgSLhixJeJMA1yri8oeW"

# # pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
# pc = Pinecone(api_key=PINECONE_API_KEY)


# PINECONE_INDEX="rag-chatbot"

# # INDEX_NAME = os.getenv("PINECONE_INDEX")
# INDEX_NAME = PINECONE_INDEX


# def create_index_if_not_exists(dim=3072):
#     existing = pc.list_indexes().names()

#     if INDEX_NAME not in existing:
#         pc.create_index(
#             name=INDEX_NAME,
#             dimension=dim,
#             metric="cosine",
#             spec=ServerlessSpec(
#                 cloud="aws",
#                 region=os.getenv("PINECONE_ENV"),
#             ),
#         )


# def get_index():
#     return pc.Index(INDEX_NAME)

from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv

load_dotenv()


pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


PINECONE_INDEX = "testing-iso"

# INDEX_NAME = os.getenv("PINECONE_INDEX")
INDEX_NAME = PINECONE_INDEX


def create_index_if_not_exists(dim=3072):
    existing = pc.list_indexes().names()

    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=dim,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",
            ),
        )


def get_index():
    return pc.Index(INDEX_NAME)

if __name__ == "__main__":
    create_index_if_not_exists(dim=3072)
    print("Done.")


