from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class BuildPurpose(Enum):
    GAMING_BUDGET = "gaming_budget"
    GAMING_MID = "gaming_mid" 
    GAMING_HIGH = "gaming_high"
    OFFICE = "office"
    PRODUCTIVITY = "productivity"
    CONTENT_CREATION = "content_creation"
    PROGRAMMING = "programming"

@dataclass
class BuildRequirements:
    purpose: BuildPurpose
    budget: int
    preferences: Dict[str, any] = None
    must_have_brands: List[str] = None
    avoid_brands: List[str] = None

class PCBuilderEngine:
    def __init__(self, components_collection):
        self.components = components_collection
        
        # Budget allocation rules based on purpose
        self.budget_allocation = {
            BuildPurpose.GAMING_BUDGET: {
                "GPU": 0.35,      # 35% of budget
                "CPU": 0.20,      # 20% of budget
                "RAM": 0.12,      # 12% of budget
                "Motherboard": 0.10,
                "Storage": 0.08,
                "PSU": 0.08,
                "Case": 0.05,
                "Cooling": 0.02
            },
            BuildPurpose.GAMING_MID: {
                "GPU": 0.40,
                "CPU": 0.22,
                "RAM": 0.12,
                "Motherboard": 0.08,
                "Storage": 0.08,
                "PSU": 0.06,
                "Case": 0.03,
                "Cooling": 0.01
            },
            BuildPurpose.GAMING_HIGH: {
                "GPU": 0.45,
                "CPU": 0.25,
                "RAM": 0.10,
                "Motherboard": 0.08,
                "Storage": 0.06,
                "PSU": 0.04,
                "Case": 0.02,
                "Cooling": 0.00
            },
            BuildPurpose.OFFICE: {
                "CPU": 0.30,
                "RAM": 0.20,
                "Storage": 0.20,
                "Motherboard": 0.15,
                "GPU": 0.05,  # Integrated graphics mostly
                "PSU": 0.05,
                "Case": 0.05
            },
            BuildPurpose.PRODUCTIVITY: {
                "CPU": 0.35,
                "RAM": 0.25,
                "Storage": 0.15,
                "Motherboard": 0.10,
                "GPU": 0.08,
                "PSU": 0.05,
                "Case": 0.02
            },
            BuildPurpose.CONTENT_CREATION: {
                "CPU": 0.30,
                "GPU": 0.25,
                "RAM": 0.20,
                "Storage": 0.10,
                "Motherboard": 0.08,
                "PSU": 0.05,
                "Case": 0.02
            }
        }
        
        # Compatibility rules
        self.compatibility_rules = {
            "cpu_socket_mapping": {
                # AMD
                "AM4": ["B450", "B550", "X470", "X570", "A520"],
                "AM5": ["B650", "X670", "B650E", "X670E"],
                # Intel
                "LGA1700": ["B660", "H670", "Z690", "B760", "H770", "Z790"],
                "LGA1200": ["B460", "H470", "Z490", "B560", "H570", "Z590"]
            },
            "ram_generation": {
                "DDR4": ["AM4", "LGA1200", "LGA1700"],  # Some LGA1700 support both
                "DDR5": ["AM5", "LGA1700"]
            },
            "psu_requirements": {
                # Minimum PSU wattage for different GPU tiers
                "RTX_4090": 850,
                "RTX_4080": 750,
                "RTX_4070_TI": 700,
                "RTX_4070": 650,
                "RTX_4060_TI": 550,
                "RTX_4060": 500,
                "RTX_3070": 650,
                "RTX_3060": 550,
                "GTX_1660": 450,
                "INTEGRATED": 400
            }
        }
        
        # Performance tiers for components
        self.performance_tiers = {
            "CPU": {
                "HIGH": ["i9", "i7", "ryzen 9", "ryzen 7"],
                "MID": ["i5", "ryzen 5"],
                "LOW": ["i3", "ryzen 3", "pentium", "celeron"]
            },
            "GPU": {
                "HIGH": ["4090", "4080", "4070 ti", "3080", "3070 ti"],
                "MID": ["4070", "4060 ti", "3070", "3060 ti", "6700"],
                "LOW": ["4060", "3060", "1660", "1650"]
            }
        }

    def get_compatible_motherboards(self, cpu_socket: str) -> List[str]:
        """Get compatible motherboard chipsets for CPU socket"""
        return self.compatibility_rules["cpu_socket_mapping"].get(cpu_socket, [])

    def calculate_psu_requirement(self, gpu_name: str, cpu_tier: str) -> int:
        """Calculate minimum PSU wattage needed"""
        base_wattage = 300  # System base consumption
        
        # GPU power consumption
        gpu_name_lower = gpu_name.lower()
        gpu_wattage = 200  # Default
        
        for gpu_tier, wattage in self.compatibility_rules["psu_requirements"].items():
            if any(tier_name in gpu_name_lower for tier_name in gpu_tier.lower().split('_')):
                gpu_wattage = wattage - base_wattage
                break
        
        # CPU power consumption (rough estimates)
        cpu_wattage = 150 if cpu_tier == "HIGH" else 100 if cpu_tier == "MID" else 65
        
        # Add 20% headroom
        total_wattage = int((base_wattage + gpu_wattage + cpu_wattage) * 1.2)
        return max(total_wattage, 450)  # Minimum 450W

    def find_best_component(self, category: str, budget: int, requirements: Dict = None) -> Dict:
        """Find the best component within budget for category"""
        query = {
            "category": category.upper(),
            "stock": "In Stock",
            "price_BDT": {"$lte": budget}
        }
        
        # Add requirement filters
        if requirements:
            if "socket" in requirements and category == "Motherboard":
                # Find motherboards compatible with CPU socket
                compatible_chipsets = self.get_compatible_motherboards(requirements["socket"])
                if compatible_chipsets:
                    query["specs.chipset"] = {"$in": compatible_chipsets}
            
            if "min_wattage" in requirements and category == "PSU":
                query["specs.wattage"] = {"$gte": requirements["min_wattage"]}
            
            if "ram_type" in requirements and category == "RAM":
                query["specs.type"] = requirements["ram_type"]
        
        # Sort by performance score and price ratio
        components = list(self.components.find(query).sort([
            ("performance_score", -1),  # Higher performance first
            ("price_BDT", 1)           # Lower price first
        ]).limit(10))
        
        if not components:
            return None
        
        # Calculate value score (performance per dollar)
        for comp in components:
            perf_score = comp.get("performance_score", 50)
            price_score = 100 - (comp["price_BDT"] / budget * 50)  # Price efficiency
            comp["value_score"] = (perf_score * 0.7) + (price_score * 0.3)
        
        # Return best value component
        best_component = max(components, key=lambda x: x.get("value_score", 0))
        return best_component

    def build_gaming_pc(self, requirements: BuildRequirements) -> Dict:
        """Build a gaming-focused PC"""
        budget = requirements.budget
        allocation = self.budget_allocation[requirements.purpose]
        
        build = {}
        remaining_budget = budget
        build_requirements = {}
        
        # Step 1: Choose GPU (most important for gaming)
        gpu_budget = int(budget * allocation["GPU"])
        gpu = self.find_best_component("GPU", gpu_budget)
        
        if not gpu:
            return {"error": "No suitable GPU found within budget"}
        
        build["GPU"] = gpu
        remaining_budget -= gpu["price_BDT"]
        
        # Determine PSU requirement based on GPU
        gpu_tier = self.get_component_tier(gpu["name"], "GPU")
        min_psu_wattage = self.calculate_psu_requirement(gpu["name"], "MID")
        build_requirements["min_wattage"] = min_psu_wattage
        
        # Step 2: Choose CPU (balance with GPU)
        cpu_budget = int(budget * allocation["CPU"])
        # Adjust CPU budget based on GPU tier to avoid bottlenecks
        if gpu_tier == "HIGH":
            cpu_budget = int(cpu_budget * 1.2)  # Get better CPU for high-end GPU
        
        cpu = self.find_best_component("CPU", min(cpu_budget, remaining_budget))
        if not cpu:
            return {"error": "No suitable CPU found within budget"}
        
        build["CPU"] = cpu
        remaining_budget -= cpu["price_BDT"]
        
        # Extract CPU socket for motherboard compatibility
        cpu_socket = cpu.get("specs", {}).get("socket")
        if cpu_socket:
            build_requirements["socket"] = cpu_socket
        
        # Step 3: Choose Motherboard (compatible with CPU)
        mb_budget = int(budget * allocation["Motherboard"])
        motherboard = self.find_best_component("Motherboard", 
                                             min(mb_budget, remaining_budget), 
                                             build_requirements)
        if not motherboard:
            return {"error": "No compatible motherboard found"}
        
        build["Motherboard"] = motherboard
        remaining_budget -= motherboard["price_BDT"]
        
        # Step 4: Choose RAM (DDR4 or DDR5 based on platform)
        ram_budget = int(budget * allocation["RAM"])
        ram_type = self.get_ram_type_for_socket(cpu_socket)
        build_requirements["ram_type"] = ram_type
        
        ram = self.find_best_component("RAM", 
                                     min(ram_budget, remaining_budget),
                                     build_requirements)
        if not ram:
            return {"error": "No suitable RAM found"}
        
        build["RAM"] = ram
        remaining_budget -= ram["price_BDT"]
        
        # Step 5: Choose Storage
        storage_budget = int(budget * allocation["Storage"])
        storage = self.find_best_component("Storage", 
                                         min(storage_budget, remaining_budget))
        if storage:
            build["Storage"] = storage
            remaining_budget -= storage["price_BDT"]
        
        # Step 6: Choose PSU
        psu_budget = int(budget * allocation["PSU"])
        psu = self.find_best_component("PSU", 
                                     min(psu_budget, remaining_budget),
                                     {"min_wattage": min_psu_wattage})
        if psu:
            build["PSU"] = psu
            remaining_budget -= psu["price_BDT"]
        
        # Step 7: Choose Case
        case_budget = remaining_budget
        case = self.find_best_component("Case", case_budget)
        if case:
            build["Case"] = case
            remaining_budget -= case["price_BDT"]
        
        # Calculate totals and performance
        total_price = sum(comp["price_BDT"] for comp in build.values() if isinstance(comp, dict))
        avg_performance = sum(comp.get("performance_score", 50) for comp in build.values() if isinstance(comp, dict)) / len(build)
        
        return {
            "build": build,
            "total_price": total_price,
            "budget": budget,
            "remaining_budget": remaining_budget,
            "avg_performance_score": round(avg_performance, 1),
            "build_purpose": requirements.purpose.value,
            "compatibility_checked": True,
            "bottleneck_analysis": self.analyze_bottlenecks(build)
        }

    def build_office_pc(self, requirements: BuildRequirements) -> Dict:
        """Build an office/productivity PC"""
        # Similar logic but prioritize CPU, RAM, and integrated graphics
        # Implementation would follow similar pattern but with different priorities
        pass

    def get_component_tier(self, component_name: str, category: str) -> str:
        """Determine component performance tier"""
        name_lower = component_name.lower()
        tiers = self.performance_tiers.get(category, {})
        
        for tier, keywords in tiers.items():
            if any(keyword in name_lower for keyword in keywords):
                return tier
        return "MID"  # Default

    def get_ram_type_for_socket(self, socket: str) -> str:
        """Determine RAM type based on CPU socket"""
        if socket in ["AM5", "LGA1700"]:
            return "DDR5"  # Prefer DDR5 for newer platforms
        return "DDR4"

    def analyze_bottlenecks(self, build: Dict) -> Dict:
        """Analyze potential bottlenecks in the build"""
        analysis = {"warnings": [], "recommendations": []}
        
        if "CPU" in build and "GPU" in build:
            cpu_tier = self.get_component_tier(build["CPU"]["name"], "CPU")
            gpu_tier = self.get_component_tier(build["GPU"]["name"], "GPU")
            
            # Check for CPU bottleneck
            if cpu_tier == "LOW" and gpu_tier == "HIGH":
                analysis["warnings"].append("CPU may bottleneck GPU performance")
                analysis["recommendations"].append("Consider upgrading CPU")
            
            # Check for GPU bottleneck
            if gpu_tier == "LOW" and cpu_tier == "HIGH":
                analysis["warnings"].append("GPU may limit gaming performance")
                analysis["recommendations"].append("Consider upgrading GPU")
        
        return analysis

    def recommend_build(self, requirements: BuildRequirements) -> Dict:
        """Main function to recommend PC build"""
        logger.info(f"Building PC for purpose: {requirements.purpose.value}, budget: {requirements.budget}")
        
        # Route to appropriate builder based on purpose
        if requirements.purpose in [BuildPurpose.GAMING_BUDGET, BuildPurpose.GAMING_MID, BuildPurpose.GAMING_HIGH]:
            return self.build_gaming_pc(requirements)
        elif requirements.purpose in [BuildPurpose.OFFICE, BuildPurpose.PRODUCTIVITY]:
            return self.build_office_pc(requirements)
        else:
            return {"error": f"Build purpose {requirements.purpose.value} not yet implemented"}

    def compare_builds(self, builds: List[Dict]) -> Dict:
        """Compare multiple builds"""
        comparison = {
            "builds": builds,
            "best_value": None,
            "best_performance": None,
            "cheapest": None
        }
        
        if not builds:
            return comparison
        
        # Find best in each category
        comparison["cheapest"] = min(builds, key=lambda x: x.get("total_price", float('inf')))
        comparison["best_performance"] = max(builds, key=lambda x: x.get("avg_performance_score", 0))
        
        # Calculate value score (performance per price)
        for build in builds:
            perf = build.get("avg_performance_score", 50)
            price = build.get("total_price", 1)
            build["value_score"] = (perf / price) * 10000  # Scale for readability
        
        comparison["best_value"] = max(builds, key=lambda x: x.get("value_score", 0))
        
        return comparison

# Example usage function
def example_usage():
    """Example of how to use the PC builder engine"""
    # This would be called from your FastAPI endpoints
    
    # Assuming you have components collection from MongoDB
    # components_collection = db["components"]
    # engine = PCBuilderEngine(components_collection)
    
    # Build a gaming PC
    # requirements = BuildRequirements(
    #     purpose=BuildPurpose.GAMING_MID,
    #     budget=80000,  # 80,000 BDT
    #     preferences={"prefer_nvidia": True}
    # )
    
    # result = engine.recommend_build(requirements)
    # return result
    pass