"""
Database models and schemas for PC Builder
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class ComponentCategory(str, Enum):
    CPU = "CPU"
    GPU = "GPU"
    RAM = "RAM"
    MOTHERBOARD = "Motherboard"
    STORAGE = "Storage"
    PSU = "PSU"
    CASE = "Case"
    COOLING = "Cooling"

class BuildPurpose(str, Enum):
    GAMING_BUDGET = "gaming_budget"
    GAMING_MID = "gaming_mid"
    GAMING_HIGH = "gaming_high"
    OFFICE = "office"
    PRODUCTIVITY = "productivity"
    CONTENT_CREATION = "content_creation"
    PROGRAMMING = "programming"

class Component(BaseModel):
    """Component model for MongoDB documents"""
    name: str
    category: ComponentCategory
    price_BDT: int
    url: str
    stock: str = "In Stock"
    source: str
    last_updated: datetime
    specs: Optional[Dict[str, Any]] = None
    performance_score: Optional[int] = None
    retailer: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BuildRequest(BaseModel):
    """Request model for PC build recommendations"""
    budget: int = Field(..., gt=0, description="Budget in BDT")
    purpose: BuildPurpose
    prefer_brands: Optional[List[str]] = None
    avoid_brands: Optional[List[str]] = None
    specific_requirements: Optional[Dict[str, Any]] = None

class ComponentResponse(BaseModel):
    """Response model for individual components"""
    name: str
    category: str
    price_BDT: int
    specs: Optional[Dict[str, Any]]
    performance_score: Optional[int]
    retailer: str
    url: str

class BuildResponse(BaseModel):
    """Response model for complete PC builds"""
    build: Dict[str, ComponentResponse]
    total_price: int
    budget: int
    remaining_budget: int
    avg_performance_score: float
    build_purpose: str
    compatibility_checked: bool
    bottleneck_analysis: Dict[str, Any]
    build_explanation: Dict[str, str]

class ComparisonRequest(BaseModel):
    """Request model for build comparisons"""
    budgets: List[int] = Field(..., min_items=2, max_items=5)
    purpose: BuildPurpose
    preferences: Optional[Dict[str, Any]] = None

class MarketInsights(BaseModel):
    """Market insights response model"""
    price_trends: Dict[str, List[str]]
    popular_components: Dict[str, str]
    stock_alerts: List[str]
    best_value_components: Dict[str, Dict[str, str]]
    market_summary: Dict[str, Any]

# MongoDB Collection Schemas
COMPONENT_SCHEMA = {
    "name": {"type": "string", "required": True},
    "category": {"type": "string", "required": True},
    "price_BDT": {"type": "int", "required": True},
    "url": {"type": "string", "required": True},
    "stock": {"type": "string", "default": "In Stock"},
    "source": {"type": "string", "required": True},
    "last_updated": {"type": "date", "required": True},
    "specs": {"type": "object"},
    "performance_score": {"type": "int"},
    "retailer": {"type": "string"}
}

# MongoDB Indexes
COMPONENT_INDEXES = [
    [("category", 1), ("price_BDT", 1)],
    [("name", 1), ("category", 1)],
    [("stock", 1)],
    [("last_updated", -1)],
    [("performance_score", -1)]
]
