from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

_ = model.encode("This is a warm-up sentence.")

def generate_embedding(text: str):
    return model.encode(text).tolist()
