from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
import logging

# Import your existing scraper and the new engine
# from your_scraper import PCBuilderScraper
# from pc_builder_engine import PCBuilderEngine, BuildPurpose, BuildRequirements

logger = logging.getLogger(__name__)

# Pydantic models for API
class BuildPurposeAPI(str, Enum):
    gaming_budget = "gaming_budget"
    gaming_mid = "gaming_mid"
    gaming_high = "gaming_high"
    office = "office"
    productivity = "productivity"
    content_creation = "content_creation"
    programming = "programming"

class BuildRequest(BaseModel):
    budget: int
    purpose: BuildPurposeAPI
    prefer_brands: Optional[List[str]] = None
    avoid_brands: Optional[List[str]] = None
    specific_requirements: Optional[dict] = None

class ComponentResponse(BaseModel):
    name: str
    category: str
    price_BDT: int
    specs: dict
    performance_score: int
    retailer: str
    url: str

class BuildResponse(BaseModel):
    build: dict
    total_price: int
    budget: int
    remaining_budget: int
    avg_performance_score: float
    build_purpose: str
    compatibility_checked: bool
    bottleneck_analysis: dict
    build_explanation: dict

class ComparisonRequest(BaseModel):
    budgets: List[int]
    purpose: BuildPurposeAPI
    preferences: Optional[dict] = None

# Initialize your components (in real app, this comes from your scraper)
# scraper = PCBuilderScraper()
# engine = PCBuilderEngine(scraper.components)

app = FastAPI(title="PC Builder AI API", version="2.0.0")

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
            purpose=BuildPurpose(request.purpose.value),
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
                purpose=BuildPurpose(request.purpose.value),
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

@app.post("/validate-compatibility")
async def validate_compatibility(components: List[str]):
    """
    Check if manually selected components are compatible
    
    - **components**: List of component IDs to check compatibility
    """
    try:
        # This would use your compatibility checking logic
        compatibility_result = engine.check_compatibility(components)
        return compatibility_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-insights")
async def get_market_insights():
    """
    Get current market insights - price trends, availability, etc.
    """
    try:
        # Calculate insights from your database
        insights = {
            "price_trends": await calculate_price_trends(),
            "popular_components": await get_popular_components(),
            "stock_alerts": await get_stock_alerts(),
            "best_value_components": await get_best_value_picks(),
            "market_summary": await get_market_summary()
        }
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/build-optimizer")
async def optimize_existing_build(
    current_build: dict,
    optimization_goal: str = "performance"  # "performance", "price", "balance"
):
    """
    Optimize an existing build for better performance or value
    """
    try:
        optimized = engine.optimize_build(current_build, optimization_goal)
        return {
            "original_build": current_build,
            "optimized_build": optimized,
            "improvements": calculate_improvements(current_build, optimized),
            "optimization_goal": optimization_goal
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    
    # Add more explanations for other components
    
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
    return {
        "total_components": 1500,
        "avg_gaming_build_price": 75000,
        "price_change_week": "+2.5%",
        "recommendation": "Good time to buy CPUs, wait for GPU prices to drop"
    }

def calculate_improvements(original: dict, optimized: dict) -> dict:
    """Calculate improvements between builds"""
    return {
        "performance_gain": "+15%",
        "price_difference": "+5000 BDT",
        "value_improvement": "+8% performance per taka"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)