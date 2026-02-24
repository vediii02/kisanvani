from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'):
        self.model = SentenceTransformer(model_name)
    
    def encode(self, text: str):
        return self.model.encode(text)