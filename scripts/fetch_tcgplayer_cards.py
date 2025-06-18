import os
import json
import asyncio
from app.services import tcgplayer_api

NEW_DATA_DIR = 'data/tcgplayer_cards_by_pack'

def ensure_data_dir():
    os.makedirs(NEW_DATA_DIR, exist_ok=True)

async def fetch_and_store():
    ensure_data_dir()
    groups = await tcgplayer_api.get_groups()
    for group in groups:
        group_id = group['groupId']
        print(f"Fetching TCGPlayer products and prices for group {group_id} ({group.get('abbreviation', group.get('name'))})...")
        products = await tcgplayer_api.get_products(group_id)
        prices = await tcgplayer_api.get_prices(group_id)
        data = {
            'group': group,
            'products': products,
            'prices': prices
        }
        out_path = os.path.join(NEW_DATA_DIR, f'cards_{group_id}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {out_path}")

def main():
    asyncio.run(fetch_and_store())

if __name__ == '__main__':
    main()
