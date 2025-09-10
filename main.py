from fastapi import FastAPI
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import asyncio
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

# MongoDB connection
try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    logger.info("Connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

db = client["pcbuilder_db"]
components = db["components"]

async def scrape_components():
    urls = [
        ("CPU", "https://www.startech.com.bd/component/processor"),
        # ("GPU", "https://www.startech.com.bd/component/graphics-card"),
        # ("RAM", "https://www.startech.com.bd/component/ram"),
        # ("Motherboard", "https://www.startech.com.bd/component/motherboard"),
        # ("Storage", "https://www.startech.com.bd/ssd"),
        # ("PSU", "https://www.startech.com.bd/component/power-supply"),
        # ("Case", "https://www.startech.com.bd/component/casing")
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    scraped_count = 0
    updated_count = 0
    
    for category, base_url in urls:
        logger.info(f"Scraping {category} from {base_url}")
        
        # Fetch first page to detect total pages
        try:
            response = requests.get(base_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Detect pagination
            total_pages = 1
            pagination = soup.select_one('.pagination')  # Common class for pagination
            if pagination:
                page_links = pagination.find_all('a')
                for link in page_links:
                    if link.text.strip().isdigit():
                        total_pages = max(total_pages, int(link.text.strip()))
            logger.info(f"Detected {total_pages} pages for {category}")
        except Exception as e:
            logger.error(f"Error detecting pagination for {category}: {e}")
            continue  # Skip if first page fails
        
        # Loop over all pages
        for page in range(1, total_pages + 1):
            page_url = base_url + (f"?page={page}" if page > 1 else "")
            logger.info(f"Scraping page {page} for {category}: {page_url}")
            
            try:
                response = requests.get(page_url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for the main container (added space in selector for descendant)
                main_container = soup.select_one('.main-content .p-items-wrap')
                if not main_container:
                    # Fallback
                    main_container = soup.select_one('.p-items-wrap')
                
                if not main_container:
                    logger.warning(f"Could not find main container for {category} on page {page}")
                    items = soup.select('.p-item')
                else:
                    items = main_container.select('.p-item')
                
                logger.info(f"Found {len(items)} items on page {page} for {category}")
                
                if len(items) == 0:
                    logger.warning(f"No items found on page {page} for {category}. Available classes: {[elem.get('class') for elem in soup.find_all(class_=True)[:10]]}")
                
                for item in items:
                    try:
                        # Name selectors
                        name_elem = (
                            item.select_one('.p-item-name') or 
                            item.select_one('.p-item-details h4') or
                            item.select_one('.p-item-details .p-item-name') or
                            item.select_one('h4') or
                            item.select_one('h3') or
                            item.select_one('.product-name')
                        )
                        
                        # Price selectors
                        price_elem = (
                            item.select_one('.marks .price') or
                            item.select_one('.marks') or
                            item.select_one('.p-item-price') or
                            item.select_one('.price') or
                            item.select_one('[class*="price"]')
                        )
                        
                        # Link selectors
                        link_elem = (
                            item.select_one('a') or
                            item.select_one('.p-item-img a') or
                            item.select_one('.p-item-details a')
                        )
                        
                        if not name_elem:
                            logger.debug(f"No name found for item on page {page} in {category}. Available elements: {[elem.name for elem in item.find_all()[:5]]}")
                            continue
                            
                        if not price_elem:
                            logger.debug(f"No price found for item on page {page} in {category}")
                            continue
                            
                        if not link_elem:
                            logger.debug(f"No link found for item on page {page} in {category}")
                            continue
                        
                        name = name_elem.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True)
                        
                        # Improved price cleaning: find all numbers, take the first (current price)
                        cleaned_text = price_text.replace('৳', '').replace('Tk', '').replace(',', '')
                        prices = re.findall(r'\d+', cleaned_text)
                        if prices:
                            price = int(prices[0])
                        else:
                            logger.warning(f"Could not parse price '{price_text}' for {name} on page {page}")
                            continue
                        
                        if price == 0:
                            logger.warning(f"Invalid price for {name} on page {page}: {price_text}")
                            continue
                        
                        link = link_elem.get('href', '')
                        if link and not link.startswith('http'):
                            base_url_site = 'https://www.startech.com.bd'
                            link = base_url_site + link if link.startswith('/') else base_url_site + '/' + link
                        
                        # Check stock status (improved to check specific elements if possible)
                        stock_elem = item.select_one('[class*="stock"]')  # Optional: if site has a stock class
                        stock_text = stock_elem.get_text(strip=True).lower() if stock_elem else item.get_text(strip=True).lower()
                        if 'out of stock' in stock_text or 'stock out' in stock_text:
                            stock = "Out of Stock"
                        elif 'in stock' in stock_text:
                            stock = "In Stock"
                        else:
                            stock = "In Stock"  # Default
                        
                        # Update database
                        result = components.update_one(
                            {"name": name, "category": category},
                            {"$set": {
                                "category": category,
                                "price_BDT": int(price * 1.15),  # Add ~15% duty
                                "url": link,
                                "stock": stock,
                                "last_updated": datetime.now().isoformat(),
                                "source": "startech.com.bd"
                            }},
                            upsert=True
                        )
                        
                        if result.upserted_id:
                            logger.info(f"Inserted {category}: {name} (Price: ৳{int(price * 1.15)}) from page {page}")
                            scraped_count += 1
                        elif result.modified_count:
                            logger.info(f"Updated {category}: {name} (Price: ৳{int(price * 1.15)}) from page {page}")
                            updated_count += 1
                        else:
                            logger.debug(f"No change for {category}: {name} on page {page}")
                            
                    except Exception as e:
                        logger.error(f"Error parsing item on page {page} in {category}: {e}")
                        logger.debug(f"Item HTML: {str(item)[:500]}...")
                        
            except Exception as e:
                logger.error(f"Error scraping page {page} for {category} at {page_url}: {e}")
    
    logger.info(f"Scraping complete: {scraped_count} inserted, {updated_count} updated")
    return {
        "status": "Scraping complete", 
        "inserted": scraped_count, 
        "updated": updated_count, 
        "timestamp": datetime.now().isoformat()
    }

# Scheduler setup
scheduler = AsyncIOScheduler()

# FastAPI lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting scheduler")
    scheduler.add_job(scrape_components, 'interval', hours=8)  # Every 8 hours
    scheduler.start()
    yield
    logger.info("Shutting down scheduler")
    scheduler.shutdown()
app = FastAPI(lifespan=lifespan)


# API Endpoints
@app.get("/scrape-now")
async def trigger_scrape():
    logger.info("Manual scrape triggered via /scrape-now")
    result = await scrape_components()
    print(result)
    return result

@app.get("/components")
async def get_components(category: str = None, max_price: int = None):
    query = {"stock": "In Stock"}
    if category:
        query["category"] = category.upper()
    if max_price:
        query["price_BDT"] = {"$lte": max_price}
    try:
        results = list(components.find(query).limit(100))
        logger.info(f"Queried components: {len(results)} found for category={category}, max_price={max_price}")
        return [{"name": r["name"], "category": r["category"], "price_BDT": r["price_BDT"], "url": r["url"], "stock": r["stock"]} for r in results]
    except Exception as e:
        logger.error(f"Error querying components: {e}")
        return {"error": str(e)}
    
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000)