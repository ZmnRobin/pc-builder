"""
Main FastAPI application for PC Builder recommendation system
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import MONGODB_URL, DATABASE_NAME, SCRAPING_INTERVAL_HOURS, LOG_LEVEL, LOG_FORMAT, LOG_FILE
from models import (
    BuildRequest, BuildResponse, ComparisonRequest, ComponentResponse, 
    MarketInsights, BuildPurpose, ComponentCategory
)
from engine import PCBuilderEngine, BuildRequirements, BuildPurpose as EngineBuildPurpose
from scraper import ComponentScraper
from database import initialize_database

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
db_client = None
engine = None
scraper = None
scheduler = AsyncIOScheduler()

async def initialize_app():
    """Initialize application components"""
    global db_client, engine, scraper
    
    try:
        # Initialize database with proper indexes
        db_client = initialize_database()
        logger.info("Database initialized")
        
        # Initialize engine and scraper
        db = db_client[DATABASE_NAME]
        components = db["components"]
        engine = PCBuilderEngine(components)
        scraper = ComponentScraper(db_client)
        
        logger.info("Application initialization complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

async def scrape_components_task():
    """Background task for scraping components"""
    try:
        logger.info("Starting scheduled component scraping")
        result = await scraper.scrape_all_components()
        logger.info(f"Scraping completed: {result}")
    except Exception as e:
        logger.error(f"Error in scheduled scraping: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting PC Builder API")
    
    # Initialize application
    await initialize_app()
    
    # Start scheduler
    scheduler.add_job(scrape_components_task, 'interval', hours=SCRAPING_INTERVAL_HOURS)
    scheduler.start()
    logger.info("Scheduler started")
    
    yield
    
    # Cleanup
    logger.info("Shutting down PC Builder API")
    scheduler.shutdown()
    if db_client:
        db_client.close()

# Create FastAPI app
app = FastAPI(
    title="PC Builder AI API",
    description="AI-powered PC build recommendation system for Bangladesh market",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files removed - API only

@app.get("/", response_class=HTMLResponse)
async def root():
    """API root endpoint"""
    return HTMLResponse(content="""
    <html>
        <head>
            <title>PC Builder AI API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                .links { margin-top: 20px; }
                .links a { display: inline-block; margin-right: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                .links a:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🖥️ PC Builder AI API</h1>
                <p>Welcome to the PC Builder AI API for Bangladesh market!</p>
                <p>This API provides intelligent PC build recommendations based on real-time component prices from local retailers.</p>
                
                <div class="links">
                    <a href="/docs">📖 API Documentation</a>
                    <a href="/redoc">📋 ReDoc</a>
                    <a href="/health">🏥 Health Check</a>
                    <a href="/build-templates">📋 Build Templates</a>
                </div>
                
                <h3>Quick Start:</h3>
                <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
curl -X POST "http://localhost:8000/recommend-build" \\
  -H "Content-Type: application/json" \\
  -d '{"budget": 80000, "purpose": "gaming_mid"}'
                </pre>
            </div>
        </body>
    </html>
    """)

@app.post("/recommend-build", response_model=BuildResponse)
async def recommend_build(request: BuildRequest):
    """
    Get PC build recommendation based on budget and purpose
    
    - **budget**: Your budget in BDT
    - **purpose**: What you'll use the PC for (gaming, office, etc.)
    - **prefer_brands**: Brands you prefer (optional)
    - **avoid_brands**: Brands to avoid (optional)
    """
    try:
        # Convert API request to engine format
        requirements = BuildRequirements(
            purpose=EngineBuildPurpose(request.purpose.value),
            budget=request.budget,
            preferences=request.specific_requirements or {},
            must_have_brands=request.prefer_brands,
            avoid_brands=request.avoid_brands
        )
        
        # Get recommendation
        result = engine.recommend_build(requirements)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Add explanation for the build choices
        result["build_explanation"] = generate_build_explanation(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in recommend_build: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-builds")
async def compare_builds(request: ComparisonRequest):
    """
    Compare builds at different budget points
    
    Returns comparison of builds at different budgets to help you decide
    """
    try:
        builds = []
        
        for budget in request.budgets:
            requirements = BuildRequirements(
                purpose=EngineBuildPurpose(request.purpose.value),
                budget=budget,
                preferences=request.preferences or {}
            )
            
            result = engine.recommend_build(requirements)
            if "error" not in result:
                builds.append(result)
        
        comparison = engine.compare_builds(builds)
        
        # Add insights
        comparison["insights"] = generate_comparison_insights(comparison)
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error in compare_builds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/components")
async def get_components(
    category: Optional[str] = None, 
    max_price: Optional[int] = None,
    limit: int = 50
):
    """
    Get components from database
    
    - **category**: Filter by component category
    - **max_price**: Filter by maximum price
    - **limit**: Maximum number of results
    """
    try:
        query = {"stock": "In Stock"}
        
        if category:
            query["category"] = category.upper()
        if max_price:
            query["price_BDT"] = {"$lte": max_price}
        
        db = db_client[DATABASE_NAME]
        components = db["components"]
        
        results = list(components.find(query).sort("performance_score", -1).limit(limit))
        
        return [
            {
                "name": r["name"],
                "category": r["category"],
                "price_BDT": r["price_BDT"],
                "url": r["url"],
                "stock": r["stock"],
                "performance_score": r.get("performance_score", 50),
                "retailer": r.get("retailer", "Unknown"),
                "specs": r.get("specs", {})
            } 
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Error querying components: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape-now")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Manually trigger component scraping"""
    try:
        logger.info("Manual scrape triggered via /scrape-now")
        background_tasks.add_task(scrape_components_task)
        return {"message": "Scraping started in background", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/build-templates")
async def get_build_templates():
    """
    Get pre-made build templates for common use cases
    """
    templates = {
        "budget_gaming": {
            "name": "Budget Gaming PC",
            "description": "Good 1080p gaming performance for tight budgets",
            "budget_range": [35000, 50000],
            "purpose": "gaming_budget",
            "expected_performance": "1080p Medium-High settings, 60+ FPS"
        },
        "mid_gaming": {
            "name": "Mid-Range Gaming PC", 
            "description": "Excellent 1080p, good 1440p gaming",
            "budget_range": [60000, 90000],
            "purpose": "gaming_mid",
            "expected_performance": "1080p Ultra, 1440p High settings, 60+ FPS"
        },
        "high_gaming": {
            "name": "High-End Gaming PC",
            "description": "4K gaming and future-proof performance",
            "budget_range": [120000, 200000],
            "purpose": "gaming_high", 
            "expected_performance": "1440p Ultra, 4K High settings, 60+ FPS"
        },
        "office": {
            "name": "Office PC",
            "description": "Reliable performance for office work",
            "budget_range": [25000, 40000],
            "purpose": "office",
            "expected_performance": "Smooth office applications, web browsing"
        },
        "content_creation": {
            "name": "Content Creation PC",
            "description": "Video editing, 3D rendering, streaming",
            "budget_range": [80000, 150000],
            "purpose": "content_creation",
            "expected_performance": "4K video editing, 3D rendering, live streaming"
        }
    }
    
    return templates

@app.get("/market-insights", response_model=MarketInsights)
async def get_market_insights():
    """
    Get current market insights - price trends, availability, etc.
    """
    try:
        insights = {
            "price_trends": await calculate_price_trends(),
            "popular_components": await get_popular_components(),
            "stock_alerts": await get_stock_alerts(),
            "best_value_components": await get_best_value_picks(),
            "market_summary": await get_market_summary()
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting market insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_client.server_info()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "components_count": db_client[DATABASE_NAME]["components"].count_documents({})
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Helper functions
def generate_build_explanation(build_result: dict) -> dict:
    """Generate human-readable explanation for build choices"""
    explanations = {}
    build = build_result.get("build", {})
    
    if "GPU" in build:
        gpu = build["GPU"]
        explanations["GPU"] = f"Selected {gpu['name']} for its excellent price-to-performance ratio in your budget range. This GPU will handle modern games at high settings."
    
    if "CPU" in build:
        cpu = build["CPU"]
        explanations["CPU"] = f"Chose {cpu['name']} to pair well with your GPU and avoid bottlenecks. This CPU provides strong performance for gaming and productivity."
    
    if "RAM" in build:
        ram = build["RAM"]
        explanations["RAM"] = f"Selected {ram['name']} for optimal capacity and speed for your use case."
    
    if "Storage" in build:
        storage = build["Storage"]
        explanations["Storage"] = f"Chose {storage['name']} for fast boot times and application loading."
    
    if "PSU" in build:
        psu = build["PSU"]
        explanations["PSU"] = f"Selected {psu['name']} to provide stable power delivery for your components."
    
    return explanations

async def calculate_price_trends():
    """Calculate price trends from price history"""
    # Implementation would analyze your price_history collection
    return {
        "trending_up": ["GPU prices increasing due to demand"],
        "trending_down": ["SSD prices dropping significantly"],
        "stable": ["CPU prices remain stable"]
    }

async def get_popular_components():
    """Get most popular components by category"""
    # This would analyze your database for most queried/recommended items
    return {
        "CPU": "AMD Ryzen 5 5600X",
        "GPU": "RTX 3060",
        "RAM": "16GB DDR4 3200MHz"
    }

async def get_stock_alerts():
    """Get components with limited stock"""
    # Query your database for low stock items
    return ["RTX 4070 - Limited stock at StarTech"]

async def get_best_value_picks():
    """Get best value components in each category"""
    return {
        "CPU": {"name": "Ryzen 5 5600X", "reason": "Best price-performance for gaming"},
        "GPU": {"name": "RTX 3060", "reason": "Sweet spot for 1080p gaming"}
    }

async def get_market_summary():
    """Get overall market summary"""
    try:
        db = db_client[DATABASE_NAME]
        components = db["components"]
        
        total_components = components.count_documents({})
        in_stock = components.count_documents({"stock": "In Stock"})
        
        return {
            "total_components": total_components,
            "in_stock_components": in_stock,
            "price_change_week": "+2.5%",
            "recommendation": "Good time to buy CPUs, wait for GPU prices to drop"
        }
    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        return {
            "total_components": 0,
            "in_stock_components": 0,
            "price_change_week": "N/A",
            "recommendation": "Unable to fetch market data"
        }

def generate_comparison_insights(comparison: dict) -> dict:
    """Generate insights from build comparison"""
    insights = {
        "recommendations": [],
        "value_analysis": {},
        "performance_analysis": {}
    }
    
    if comparison.get("best_value"):
        best_value = comparison["best_value"]
        insights["recommendations"].append(
            f"Best value build: {best_value['build_purpose']} at ৳{best_value['total_price']:,}"
        )
    
    if comparison.get("best_performance"):
        best_perf = comparison["best_performance"]
        insights["recommendations"].append(
            f"Highest performance build: {best_perf['build_purpose']} with {best_perf['avg_performance_score']} performance score"
        )
    
    return insights

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting PC Builder API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
