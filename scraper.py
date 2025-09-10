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
        
    def extract_specs_from_short_description(self, soup: BeautifulSoup, category: str) -> Dict[str, any]:
        """Extract specifications from short-description section"""
        specs = {}
        
        try:
            # Look for short-description section
            short_desc = soup.select_one('.short-description')
            if not short_desc:
                return specs
                
            # Find all list items in short-description
            list_items = short_desc.find_all('li')
            
            for item in list_items:
                text = item.get_text(strip=True).lower()
                
                # CPU specifications
                if category == "CPU":
                    if 'speed:' in text or 'frequency:' in text:
                        # Extract speed info like "3.5GHz up to 4.4GHz"
                        speed_match = re.search(r'(\d+\.?\d*)\s*ghz', text)
                        if speed_match:
                            specs['base_clock'] = speed_match.group(1) + 'GHz'
                    
                    if 'cores' in text and 'threads' in text:
                        # Extract cores and threads like "Cores-6 & Threads-12"
                        cores_match = re.search(r'cores[:\s-]*(\d+)', text)
                        threads_match = re.search(r'threads[:\s-]*(\d+)', text)
                        if cores_match:
                            specs['cores'] = int(cores_match.group(1))
                        if threads_match:
                            specs['threads'] = int(threads_match.group(1))
                    
                    if 'ddr' in text:
                        # Extract DDR type like "DDR4 Up to 3200MHz"
                        ddr_match = re.search(r'ddr(\d+)', text)
                        if ddr_match:
                            specs['memory_type'] = f"DDR{ddr_match.group(1)}"
                    
                    if 'cache:' in text:
                        # Extract cache info
                        cache_match = re.search(r'l3[:\s-]*(\d+)mb', text)
                        if cache_match:
                            specs['cache_l3'] = int(cache_match.group(1))
                
                # Motherboard specifications
                elif category == "Motherboard":
                    if 'amd' in text and ('ryzen' in text or 'am4' in text):
                        specs['socket'] = 'AM4'
                        if 'a520' in text:
                            specs['chipset'] = 'A520'
                        elif 'b450' in text:
                            specs['chipset'] = 'B450'
                        elif 'b550' in text:
                            specs['chipset'] = 'B550'
                        elif 'x570' in text:
                            specs['chipset'] = 'X570'
                    
                    if 'intel' in text and ('lga' in text or 'socket' in text):
                        if 'lga1700' in text:
                            specs['socket'] = 'LGA1700'
                        elif 'lga1200' in text:
                            specs['socket'] = 'LGA1200'
                        elif 'h610' in text:
                            specs['chipset'] = 'H610'
                        elif 'b660' in text:
                            specs['chipset'] = 'B660'
                        elif 'z690' in text:
                            specs['chipset'] = 'Z690'
                    
                    if 'ram' in text and 'mhz' in text:
                        # Extract RAM speed like "Supports up to 4600(OC) MHz RAM"
                        ram_match = re.search(r'(\d+)(?:\(oc\))?\s*mhz', text)
                        if ram_match:
                            specs['max_ram_speed'] = int(ram_match.group(1))
                    
                    if 'micro-atx' in text or 'matx' in text:
                        specs['form_factor'] = 'Micro-ATX'
                    elif 'mini-itx' in text:
                        specs['form_factor'] = 'Mini-ITX'
                    elif 'atx' in text:
                        specs['form_factor'] = 'ATX'
                
                # RAM specifications
                elif category == "RAM":
                    if 'capacity:' in text or 'memory capacity:' in text:
                        # Extract capacity like "Memory Capacity: 16GB"
                        capacity_match = re.search(r'(\d+)\s*gb', text)
                        if capacity_match:
                            specs['capacity'] = int(capacity_match.group(1))
                    
                    if 'type:' in text or 'memory type:' in text:
                        # Extract type like "Memory Type: DDR4"
                        type_match = re.search(r'ddr(\d+)', text)
                        if type_match:
                            specs['type'] = f"DDR{type_match.group(1)}"
                    
                    if 'frequency:' in text or 'mhz' in text:
                        # Extract frequency like "Memory Frequency: 3600MHz"
                        freq_match = re.search(r'(\d+)\s*mhz', text)
                        if freq_match:
                            specs['speed'] = int(freq_match.group(1))
                    
                    if 'latency:' in text or 'cl' in text:
                        # Extract latency like "Latency: CL18"
                        latency_match = re.search(r'cl(\d+)', text)
                        if latency_match:
                            specs['latency'] = f"CL{latency_match.group(1)}"
                
                # GPU specifications
                elif category == "GPU":
                    if 'memory:' in text or 'video memory:' in text:
                        # Extract memory like "Video Memory: 8GB GDDR6"
                        memory_match = re.search(r'(\d+)\s*gb', text)
                        if memory_match:
                            specs['memory_gb'] = int(memory_match.group(1))
                    
                    if 'core clock:' in text:
                        # Extract core clock like "Core Clock: 2587 MHz"
                        clock_match = re.search(r'(\d+)\s*mhz', text)
                        if clock_match:
                            specs['core_clock'] = int(clock_match.group(1))
                    
                    if 'cuda cores:' in text:
                        # Extract CUDA cores like "CUDA Cores: 2560"
                        cuda_match = re.search(r'(\d+)', text)
                        if cuda_match:
                            specs['cuda_cores'] = int(cuda_match.group(1))
                
                # Storage specifications
                elif category == "Storage":
                    if 'capacity:' in text:
                        # Extract capacity like "Capacity: 512GB"
                        capacity_match = re.search(r'(\d+)\s*gb', text)
                        if capacity_match:
                            specs['capacity'] = int(capacity_match.group(1))
                    
                    if 'interface:' in text:
                        # Extract interface like "Interface: PCI-Express 4.0 x4"
                        if 'pci-express' in text or 'nvme' in text:
                            specs['interface'] = 'PCIe NVMe'
                        elif 'sata' in text:
                            specs['interface'] = 'SATA'
                    
                    if 'form factor:' in text:
                        # Extract form factor like "Form Factor: M.2 2280"
                        if 'm.2' in text:
                            specs['form_factor'] = 'M.2'
                        elif '2.5' in text:
                            specs['form_factor'] = '2.5"'
                
                # PSU specifications
                elif category == "PSU":
                    if 'wattage' in text or 'w' in text:
                        # Extract wattage like "550W"
                        wattage_match = re.search(r'(\d+)\s*w', text)
                        if wattage_match:
                            specs['wattage'] = int(wattage_match.group(1))
                    
                    if '80 plus' in text:
                        # Extract efficiency rating like "80 PLUS White Certified"
                        efficiency_match = re.search(r'80\s*plus\s+(\w+)', text)
                        if efficiency_match:
                            specs['efficiency'] = efficiency_match.group(1).title()
                
                # Case specifications
                elif category == "Case":
                    if 'motherboard support:' in text:
                        # Extract motherboard support like "Motherboard Support: M-ATX, Mini-ITX"
                        if 'atx' in text:
                            specs['motherboard_support'] = 'ATX'
                        elif 'micro-atx' in text or 'm-atx' in text:
                            specs['motherboard_support'] = 'Micro-ATX'
                        elif 'mini-itx' in text:
                            specs['motherboard_support'] = 'Mini-ITX'
                            
        except Exception as e:
            logger.debug(f"Error extracting specs from short description: {e}")
            
        return specs

    def extract_specs(self, component_name: str, category: str, soup: BeautifulSoup) -> Dict[str, any]:
        """Extract specifications from component page"""
        specs = {}
        
        try:
            # First try to extract from short-description section
            specs = self.extract_specs_from_short_description(soup, category)
            
            # If no specs found, try to extract from component name
            if not specs:
                specs = self.extract_specs_from_name(component_name, category)
            
            # Also try to extract from detailed specification tables if available
            spec_tables = soup.find_all(['table', 'dl'], class_=re.compile(r'spec|detail|feature'))
            
            for table in spec_tables:
                rows = table.find_all(['tr', 'li'])
                for row in rows:
                    cells = row.find_all(['td', 'dd', 'dt'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Map common spec keys (fallback)
                        if 'socket' in key and 'socket' not in specs:
                            specs['socket'] = value
                        elif 'chipset' in key and 'chipset' not in specs:
                            specs['chipset'] = value
                        elif 'memory' in key and 'type' in key and 'memory_type' not in specs:
                            specs['memory_type'] = value
                        elif 'capacity' in key and 'capacity' not in specs:
                            specs['capacity'] = value
                        elif 'speed' in key and 'speed' not in specs:
                            specs['speed'] = value
                        elif 'wattage' in key and 'wattage' not in specs:
                            specs['wattage'] = int(re.findall(r'\d+', value)[0]) if re.findall(r'\d+', value) else None
                            
        except Exception as e:
            logger.debug(f"Error extracting specs for {component_name}: {e}")
            
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
                            
                            # Extract price from correct location - price-new is the actual price
                            price_elem = (
                                item.select_one('.p-item-price .price-new') or
                                item.select_one('.price-new') or
                                item.select_one('.p-item-price span') or
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
                                
                            # Parse price - handle different formats
                            # Remove currency symbols and commas
                            cleaned_text = price_text.replace('৳', '').replace('Tk', '').replace(',', '').strip()
                            
                            # Extract the first number found (should be the price)
                            price_match = re.search(r'(\d+)', cleaned_text)
                            if not price_match:
                                logger.debug(f"Could not parse price '{price_text}' for {name}")
                                continue
                                
                            price = int(price_match.group(1))
                            if price == 0:
                                logger.debug(f"Invalid price for {name}: {price_text}")
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
    
    async def scrape_category_only(self, category: str) -> Dict[str, any]:
        """Scrape only a specific category"""
        logger.info(f"Scraping only {category} category")
        
        total_scraped = 0
        total_updated = 0
        
        for retailer, config in RETAILERS.items():
            if category in config['categories']:
                logger.info(f"Scraping {category} from {config['name']}")
                base_url = config['base_url'] + config['categories'][category]
                scraped, updated = await self.scrape_category(retailer, category, base_url)
                total_scraped += scraped
                total_updated += updated
                break  # Only scrape from first retailer for now
        
        logger.info(f"{category} scraping complete: {total_scraped} inserted, {total_updated} updated")
        
        return {
            "status": f"{category} scraping complete",
            "category": category,
            "inserted": total_scraped,
            "updated": total_updated,
            "timestamp": datetime.now().isoformat()
        }

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
