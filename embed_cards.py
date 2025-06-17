"""
Script to embed card data from data/cards_by_pack using OpenAI's text-embedding-ada-002 model.
Outputs a JSONL file with one card per line: {"card": ..., "embedding": ...}

Usage:
    python embed_cards.py            # Embed all packs
    python embed_cards.py <pack.json>  # Embed only one pack
"""
import os
import sys
import json
from openai import OpenAI

CARDS_DIR = "data/cards_by_pack"
OUTPUT_FILE = "data/card_embeddings.jsonl"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def get_card_text(card):
    fields = [
        card.get("name", ""),
        card.get("type", ""),
        card.get("trait", ""),
        card.get("rarity", ""),
        card.get("id", ""),
        card.get("pack_id", ""),
        str(card.get("color", "")),
    ]
    return " | ".join([str(f) for f in fields if f])

def main():
    # If a pack filename is given, only embed that pack
    if len(sys.argv) == 2:
        pack_filenames = [sys.argv[1]]
    else:
        pack_filenames = [f for f in os.listdir(CARDS_DIR) if f.endswith(".json") and f != "packs.json"]
    with open(OUTPUT_FILE, "w") as out_f:
        for fname in pack_filenames:
            path = os.path.join(CARDS_DIR, fname)
            with open(path, "r") as f:
                cards = json.load(f)
            for card in cards:
                text = get_card_text(card)
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                embedding = response.data[0].embedding
                out_f.write(json.dumps({"card": card, "embedding": embedding}) + "\n")
                print(f"Embedded card: {card.get('name')}")

if __name__ == "__main__":
    main()
