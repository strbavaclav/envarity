import math

from envarity.llm_client import get_client, get_embedding_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = get_client()
    response = client.embeddings.create(model=get_embedding_model(), input=texts)
    return [item.embedding for item in response.data]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


def find_similar(
    query: str, documents: list[str], embeddings: list[list[float]], top_k: int = 3
) -> list[tuple[str, float]]:
    query_embedding = embed_texts([query])[0]
    scored = [
        (doc, cosine_similarity(query_embedding, emb))
        for doc, emb in zip(documents, embeddings)
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
