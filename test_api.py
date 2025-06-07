import asyncio
from tcgplayer_api import tcgplayer_api

async def test_api():
    try:
        # Test the get_groups method
        print("\nTesting tcgplayer_api.get_groups()...")
        groups = await tcgplayer_api.get_groups()
        print(f"Got {len(groups)} groups")
        if groups:
            print(f"First group: {groups[0]}")
        
        # Test the get_products method with a valid group ID (Royal Blood = 23766)
        group_id = 23766
        print(f"\nTesting tcgplayer_api.get_products(group_id={group_id})...")
        products = await tcgplayer_api.get_products(group_id=group_id)
        print(f"Got {len(products)} products")
        if products:
            print(f"First product: {products[0]}")
        
        # Test the get_prices method with the same group ID
        print(f"\nTesting tcgplayer_api.get_prices(group_id={group_id})...")
        prices = await tcgplayer_api.get_prices(group_id=group_id)
        print(f"Got {len(prices)} prices")
        if prices:
            print(f"First price: {prices[0]}")
        
        # Test the get_products method WITHOUT a group ID (should return empty list with warning)
        print("\nTesting tcgplayer_api.get_products() without group_id...")
        products = await tcgplayer_api.get_products()
        print(f"Got {len(products)} products (empty list expected)")
        
    except Exception as e:
        print(f"Error in test: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
