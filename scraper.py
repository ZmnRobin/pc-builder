"""
Enhanced scraper for PC components from Bangladeshi retailers
"""
import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from config import RETAILERS, REQUEST_TIMEOUT, REQUEST_DELAY
from models import Component, ComponentCategory

logger = logging.getLogger(__name__)

class ComponentScraper:
    def __init__(self, db_client: MongoClient):
        self.db = db_client["pcbuilder_db"]
        self.components = self.db["components"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
    def extract_specs(self, component_name: str, category: str, soup: BeautifulSoup) -> Dict[str, any]:
        """Extract specifications from component page"""
        specs = {}
        
        try:
            # Look for specification tables or lists
            spec_tables = soup.find_all(['table', 'dl', 'ul'], class_=re.compile(r'spec|detail|feature'))
            
            for table in spec_tables:
                rows = table.find_all(['tr', 'li'])
                for row in rows:
                    cells = row.find_all(['td', 'dd', 'dt'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map common spec keys
                        if 'socket' in key or 'cpu socket' in key:
                            specs['socket'] = value
                        elif 'chipset' in key:
                            specs['chipset'] = value
                        elif 'memory' in key and 'type' in key:
                            specs['memory_type'] = value
                        elif 'capacity' in key or 'size' in key:
                            specs['capacity'] = value
                        elif 'speed' in key or 'frequency' in key:
                            specs['speed'] = value
                        elif 'wattage' in key or 'power' in key:
                            specs['wattage'] = int(re.findall(r'\d+', value)[0]) if re.findall(r'\d+', value) else None
                        elif 'cores' in key:
                            specs['cores'] = int(re.findall(r'\d+', value)[0]) if re.findall(r'\d+', value) else None
                        elif 'threads' in key:
                            specs['threads'] = int(re.findall(r'\d+', value)[0]) if re.findall(r'\d+', value) else None
                        elif 'base clock' in key or 'frequency' in key:
                            specs['base_clock'] = value
                        elif 'boost clock' in key:
                            specs['boost_clock'] = value
                        elif 'memory' in key and 'gb' in value.lower():
                            specs['memory_gb'] = int(re.findall(r'\d+', value)[0]) if re.findall(r'\d+', value) else None
                        elif 'interface' in key:
                            specs['interface'] = value
                        elif 'form factor' in key:
                            specs['form_factor'] = value
                            
        except Exception as e:
            logger.debug(f"Error extracting specs for {component_name}: {e}")
            
        # Extract specs from component name if not found in page
        if not specs:
            specs = self.extract_specs_from_name(component_name, category)
            
        return specs
    
    def extract_specs_from_name(self, name: str, category: str) -> Dict[str, any]:
        """Extract basic specs from component name"""
        specs = {}
        name_lower = name.lower()
        
        if category == "CPU":
            # Extract socket
            if 'am4' in name_lower:
                specs['socket'] = 'AM4'
            elif 'am5' in name_lower:
                specs['socket'] = 'AM5'
            elif 'lga1700' in name_lower:
                specs['socket'] = 'LGA1700'
            elif 'lga1200' in name_lower:
                specs['socket'] = 'LGA1200'
                
            # Extract cores
            cores_match = re.search(r'(\d+)\s*core', name_lower)
            if cores_match:
                specs['cores'] = int(cores_match.group(1))
                
            # Extract generation
            gen_match = re.search(r'(\d+)(?:th|nd|rd|st)\s*gen', name_lower)
            if gen_match:
                specs['generation'] = int(gen_match.group(1))
                
        elif category == "RAM":
            # Extract capacity
            capacity_match = re.search(r'(\d+)\s*gb', name_lower)
            if capacity_match:
                specs['capacity'] = int(capacity_match.group(1))
                
            # Extract speed
            speed_match = re.search(r'(\d+)\s*mhz', name_lower)
            if speed_match:
                specs['speed'] = int(speed_match.group(1))
                
            # Extract type
            if 'ddr4' in name_lower:
                specs['type'] = 'DDR4'
            elif 'ddr5' in name_lower:
                specs['type'] = 'DDR5'
                
        elif category == "GPU":
            # Extract memory
            memory_match = re.search(r'(\d+)\s*gb', name_lower)
            if memory_match:
                specs['memory_gb'] = int(memory_match.group(1))
                
        elif category == "Storage":
            # Extract capacity
            capacity_match = re.search(r'(\d+)\s*(?:gb|tb)', name_lower)
            if capacity_match:
                capacity = int(capacity_match.group(1))
                if 'tb' in name_lower:
                    capacity *= 1024
                specs['capacity'] = capacity
                
            # Extract type
            if 'ssd' in name_lower:
                specs['type'] = 'SSD'
            elif 'hdd' in name_lower:
                specs['type'] = 'HDD'
            elif 'nvme' in name_lower:
                specs['type'] = 'NVMe'
                
        return specs
    
    def calculate_performance_score(self, component: Dict, category: str) -> int:
        """Calculate performance score for component"""
        score = 50  # Base score
        specs = component.get('specs', {})
        
        if category == "CPU":
            # Higher cores = higher score
            cores = specs.get('cores', 4)
            score += min(cores * 5, 30)
            
            # Higher generation = higher score
            generation = specs.get('generation', 10)
            score += min((generation - 10) * 3, 20)
            
            # Brand bonus
            name_lower = component['name'].lower()
            if 'i9' in name_lower or 'ryzen 9' in name_lower:
                score += 20
            elif 'i7' in name_lower or 'ryzen 7' in name_lower:
                score += 15
            elif 'i5' in name_lower or 'ryzen 5' in name_lower:
                score += 10
                
        elif category == "GPU":
            # Memory bonus
            memory = specs.get('memory_gb', 4)
            score += min(memory * 3, 25)
            
            # Brand and model bonus
            name_lower = component['name'].lower()
            if 'rtx 4090' in name_lower:
                score += 40
            elif 'rtx 4080' in name_lower:
                score += 35
            elif 'rtx 4070' in name_lower:
                score += 30
            elif 'rtx 4060' in name_lower:
                score += 25
            elif 'rtx 3070' in name_lower:
                score += 20
            elif 'rtx 3060' in name_lower:
                score += 15
                
        elif category == "RAM":
            # Capacity bonus
            capacity = specs.get('capacity', 8)
            score += min(capacity * 2, 20)
            
            # Speed bonus
            speed = specs.get('speed', 2400)
            score += min((speed - 2400) // 100, 15)
            
            # DDR5 bonus
            if specs.get('type') == 'DDR5':
                score += 10
                
        elif category == "Storage":
            # Capacity bonus
            capacity = specs.get('capacity', 256)
            score += min(capacity // 100, 20)
            
            # Type bonus
            storage_type = specs.get('type', 'HDD')
            if storage_type == 'NVMe':
                score += 20
            elif storage_type == 'SSD':
                score += 10
                
        return min(score, 100)  # Cap at 100
    
    async def scrape_category(self, retailer: str, category: str, base_url: str) -> Tuple[int, int]:
        """Scrape all pages for a specific category"""
        scraped_count = 0
        updated_count = 0
        
        logger.info(f"Scraping {category} from {base_url}")
        
        try:
            # Get first page to detect total pages
            response = requests.get(base_url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Detect pagination
            total_pages = 1
            pagination = soup.select_one('.pagination')
            if pagination:
                page_links = pagination.find_all('a')
                for link in page_links:
                    if link.text.strip().isdigit():
                        total_pages = max(total_pages, int(link.text.strip()))
                        
            logger.info(f"Detected {total_pages} pages for {category}")
            
            # Scrape all pages
            for page in range(1, total_pages + 1):
                page_url = base_url + (f"?page={page}" if page > 1 else "")
                logger.info(f"Scraping page {page} for {category}: {page_url}")
                
                try:
                    response = requests.get(page_url, headers=self.headers, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find items container
                    main_container = soup.select_one('.main-content .p-items-wrap') or soup.select_one('.p-items-wrap')
                    items = main_container.select('.p-item') if main_container else soup.select('.p-item')
                    
                    logger.info(f"Found {len(items)} items on page {page} for {category}")
                    
                    for item in items:
                        try:
                            # Extract basic info
                            name_elem = (
                                item.select_one('.p-item-name') or 
                                item.select_one('.p-item-details h4') or
                                item.select_one('h4') or
                                item.select_one('h3')
                            )
                            
                            price_elem = (
                                item.select_one('.marks .price') or
                                item.select_one('.marks') or
                                item.select_one('.p-item-price') or
                                item.select_one('.price')
                            )
                            
                            link_elem = item.select_one('a')
                            
                            if not all([name_elem, price_elem, link_elem]):
                                continue
                                
                            name = name_elem.get_text(strip=True)
                            price_text = price_elem.get_text(strip=True)
                            
                            # Skip if price is not available
                            if 'up coming' in price_text.lower() or 'out of stock' in price_text.lower():
                                continue
                                
                            # Parse price
                            cleaned_text = price_text.replace('৳', '').replace('Tk', '').replace(',', '')
                            prices = re.findall(r'\d+', cleaned_text)
                            if not prices:
                                continue
                                
                            price = int(prices[0])
                            if price == 0:
                                continue
                                
                            # Build URL
                            link = link_elem.get('href', '')
                            if link and not link.startswith('http'):
                                base_url_site = RETAILERS[retailer]['base_url']
                                link = base_url_site + link if link.startswith('/') else base_url_site + '/' + link
                            
                            # Extract detailed specs from product page
                            specs = {}
                            try:
                                detail_response = requests.get(link, headers=self.headers, timeout=REQUEST_TIMEOUT)
                                detail_response.raise_for_status()
                                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                                specs = self.extract_specs(name, category, detail_soup)
                                time.sleep(REQUEST_DELAY)  # Be respectful
                            except Exception as e:
                                logger.debug(f"Could not fetch details for {name}: {e}")
                                specs = self.extract_specs_from_name(name, category)
                            
                            # Create component document
                            component_doc = {
                                "name": name,
                                "category": category,
                                "price_BDT": int(price * 1.15),  # Add duty
                                "url": link,
                                "stock": "In Stock",
                                "source": retailer,
                                "last_updated": datetime.now(),
                                "specs": specs,
                                "retailer": RETAILERS[retailer]['name']
                            }
                            
                            # Calculate performance score
                            component_doc["performance_score"] = self.calculate_performance_score(component_doc, category)
                            
                            # Update database
                            result = self.components.update_one(
                                {"name": name, "category": category},
                                {"$set": component_doc},
                                upsert=True
                            )
                            
                            if result.upserted_id:
                                scraped_count += 1
                                logger.info(f"Inserted {category}: {name} (৳{component_doc['price_BDT']})")
                            elif result.modified_count:
                                updated_count += 1
                                logger.info(f"Updated {category}: {name} (৳{component_doc['price_BDT']})")
                                
                        except Exception as e:
                            logger.error(f"Error parsing item on page {page} in {category}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error scraping page {page} for {category}: {e}")
                    
                time.sleep(REQUEST_DELAY)  # Be respectful to the server
                
        except Exception as e:
            logger.error(f"Error scraping {category}: {e}")
            
        return scraped_count, updated_count
    
    async def scrape_all_components(self) -> Dict[str, any]:
        """Scrape all components from all retailers"""
        total_scraped = 0
        total_updated = 0
        
        for retailer, config in RETAILERS.items():
            logger.info(f"Scraping from {config['name']}")
            
            for category, url_path in config['categories'].items():
                base_url = config['base_url'] + url_path
                scraped, updated = await self.scrape_category(retailer, category, base_url)
                total_scraped += scraped
                total_updated += updated
                
        logger.info(f"Scraping complete: {total_scraped} inserted, {total_updated} updated")
        
        return {
            "status": "Scraping complete",
            "inserted": total_scraped,
            "updated": total_updated,
            "timestamp": datetime.now().isoformat()
        }
