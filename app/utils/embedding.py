from typing import List, Tuple, Any
import numpy as np
import json as _json
from openai import OpenAI
from app.models.card import CardInfo

def get_cardinfo_text(cardinfo: CardInfo) -> str:
    name = cardinfo.name or ""
    type_ = cardinfo.type or ""
    trait = cardinfo.trait or ""
    rarity = cardinfo.rarity or ""
    card_number = cardinfo.card_number or ""
    colors = str(cardinfo.colors or "")
    cost = str(cardinfo.cost or "")
    fields = [
        cost, cost, cost, cost,
        card_number, card_number, card_number, card_number,
        name, name, name, name, name,
        type_, type_,
        trait,
        rarity,
        card_number,
        colors,
    ]
    return " | ".join([str(f) for f in fields if f])

def cosine_similarity(a: List[float], b: List[float]) -> float:
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def embedding_pre_filter(
    card_info: CardInfo,
    client: OpenAI,
    embeddings_file: str = "data/card_embeddings.jsonl",
    top_k: int = 50
) -> Tuple[List[Any], float]:
    import time
    embedding_start_time = time.time()
    text = get_cardinfo_text(card_info)
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    cardinfo_embedding = response.data[0].embedding
    with open(embeddings_file, "r") as f:
        all_embeddings = [_json.loads(line) for line in f]
    scored: List[Tuple[float, Any]] = []
    for entry in all_embeddings:
        sim = cosine_similarity(cardinfo_embedding, entry["embedding"])
        scored.append((sim, entry["card"]))
    scored.sort(reverse=True, key=lambda x: x[0])
    top_k_cards: List[Any] = [card for _, card in scored[:top_k]]
    embedding_duration: float = time.time() - embedding_start_time
    return top_k_cards, embedding_duration
