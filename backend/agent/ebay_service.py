import os
import requests
from bs4 import BeautifulSoup
import json
import time

SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY")
if not SCRAPINGBEE_API_KEY:
    raise ValueError("SCRAPINGBEE_API_KEY not found in environment variables.")

def get_ebay_car_listings(num_listings=10, max_pages=1): # Increased num_listings to 10
    listings = []
    page_num = 1
    while len(listings) < num_listings and page_num <= max_pages:
        print(f"Scraping page {page_num}...")
        # Construct eBay search URL for cars
        # Example: https://www.ebay.com/sch/i.html?_nkw=car&_sacat=0&_pgn=1
        ebay_url = f"https://www.ebay.com/sch/i.html?_nkw=car&_sacat=0&_pgn={page_num}"

        # Use ScrapingBee to get the page content
        try:
            response = requests.get(
                "https://app.scrapingbee.com/api/v1/",
                params={
                    "api_key": SCRAPINGBEE_API_KEY,
                    "url": ebay_url,
                    "wait": "5000", # Wait for 5 seconds for the page to load
                    "render_js": "True", # Render JavaScript
                }
            )
            response.raise_for_status() # Raise an exception for HTTP errors
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page_num}: {e}")
            break

        # Save raw HTML for debugging
        with open(f"ebay_page_{page_num}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"Saved raw HTML to ebay_page_{page_num}.html")

        soup = BeautifulSoup(response.content, "html.parser")

        # Find all listing items
        items = soup.find_all("li", class_="s-card")
        print(f"Found {len(items)} potential items on page {page_num}")

        for i, item in enumerate(items):
            if len(listings) >= num_listings:
                break

            title_tag = item.find("h3", class_="s-card__title")
            title = "N/A"
            if title_tag:
                # Directly target the span containing the actual product title
                product_title_span = title_tag.find("span", class_="su-styled-text primary default")
                if product_title_span:
                    title = product_title_span.text.strip()

            price_tag = item.find("span", class_="s-card__price")
            price = price_tag.text.strip() if price_tag else "N/A"

            image_tag = item.find("img", class_="s-card__image")
            image_url = image_tag["src"] if image_tag and "src" in image_tag.attrs else "N/A"

            link_tag = item.find("a", class_="s-card__link image-treatment")
            listing_url = link_tag["href"] if link_tag and "href" in link_tag.attrs else "N/A"
            
            print(f"--- Item {i+1} ---")
            print(f"Title: {title}")
            print(f"Price: {price}")
            print(f"Image URL: {image_url}")
            print(f"Listing URL: {listing_url}")

            if title != "N/A" and price != "N/A" and image_url != "N/A" and listing_url != "N/A":
                listings.append({
                    "title": title,
                    "price": price,
                    "image_url": image_url,
                    "listing_url": listing_url
                })
            else:
                print(f"Skipping item {i+1} due to missing data.")

        page_num += 1
        time.sleep(2) # Be polite and avoid hammering the server

    return listings

if __name__ == "__main__":
    print("Starting eBay car listings scraping...")
    car_listings = get_ebay_car_listings(num_listings=10, max_pages=1)
    
    output_file = "backend/data/mock_listings.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(car_listings, f, indent=4)
    
    print(f"Scraped {len(car_listings)} car listings and saved to {output_file}")
