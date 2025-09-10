"""
Configuration settings for PC Builder application
"""
import os
from typing import Dict, List

# Database Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = "pcbuilder_db"

# Scraping Configuration
SCRAPING_INTERVAL_HOURS = 8
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1  # Delay between requests to be respectful

# Supported Retailers
RETAILERS = {
    "startech": {
        "name": "StarTech.com.bd",
        "base_url": "https://www.startech.com.bd",
        "categories": {
            "CPU": "/component/processor",
            "GPU": "/component/graphics-card", 
            "RAM": "/component/ram",
            "Motherboard": "/component/motherboard",
            "Storage": "/ssd",
            "PSU": "/component/power-supply",
            "Case": "/component/casing"
        }
    }
}

# Component Categories
COMPONENT_CATEGORIES = [
    "CPU", "GPU", "RAM", "Motherboard", "Storage", "PSU", "Case", "Cooling"
]

# Budget Ranges (in BDT)
BUDGET_RANGES = {
    "budget": (25000, 50000),
    "mid_range": (50000, 100000), 
    "high_end": (100000, 200000),
    "premium": (200000, 500000)
}

# Performance Scoring Weights
PERFORMANCE_WEIGHTS = {
    "CPU": {"cores": 0.3, "frequency": 0.2, "generation": 0.3, "brand": 0.2},
    "GPU": {"memory": 0.2, "cores": 0.3, "generation": 0.3, "brand": 0.2},
    "RAM": {"capacity": 0.5, "speed": 0.3, "type": 0.2},
    "Storage": {"capacity": 0.4, "type": 0.4, "speed": 0.2}
}

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_FILE = "scraper.log"
