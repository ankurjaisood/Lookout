import json
from config import Settings

settings = Settings()

def search_ebay_listings(query: str, category_id: str = None):
    """
    Mock function to search for listings on eBay.
    Returns a list of sample listings from a JSON file.
    """
    with open("backend/data/mock_listings.json", "r") as f:
        listings = json.load(f)
    
    if query:
        query = query.lower()
        filtered_listings = [
            listing for listing in listings
            if query in listing["title"].lower()
        ]
    else:
        filtered_listings = listings
        
    return filtered_listings
