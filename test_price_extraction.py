"""
Quick test to verify price extraction is working correctly
"""
import requests
import time

def test_price_extraction():
    """Test if prices are being extracted correctly"""
    print("🧪 Testing Price Extraction")
    print("=" * 40)
    
    # Clear database first
    print("🗑️ Clearing database...")
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017/')
        db = client['pcbuilder_db']
        components = db['components']
        components.delete_many({})
        client.close()
        print("✅ Database cleared")
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        return
    
    # Test scraping CPUs (smaller dataset for quick test)
    print("\n📦 Scraping CPUs to test price extraction...")
    try:
        response = requests.post("http://localhost:8000/scrape-now", params={"category": "CPU"})
        if response.status_code == 200:
            result = response.json()
            print(f"✅ CPU scraping started: {result['message']}")
        else:
            print(f"❌ Failed to start CPU scraping: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error starting CPU scraping: {e}")
        return
    
    # Wait for scraping to complete
    print("⏳ Waiting 20 seconds for scraping to complete...")
    time.sleep(20)
    
    # Check the results
    print("\n📊 Checking scraped data...")
    try:
        response = requests.get("http://localhost:8000/components?category=CPU&limit=5")
        if response.status_code == 200:
            components = response.json()
            print(f"✅ Found {len(components)} CPU components")
            
            print("\n📋 Sample CPU data:")
            for i, comp in enumerate(components[:3], 1):
                print(f"\n{i}. {comp['name']}")
                print(f"   Price: ৳{comp['price_BDT']:,}")
                print(f"   Specs: {comp.get('specs', {})}")
                print(f"   Performance Score: {comp.get('performance_score', 'N/A')}")
                
                # Check if price looks reasonable (not too high/low)
                if comp['price_BDT'] < 5000:
                    print(f"   ⚠️ Price seems too low: ৳{comp['price_BDT']:,}")
                elif comp['price_BDT'] > 200000:
                    print(f"   ⚠️ Price seems too high: ৳{comp['price_BDT']:,}")
                else:
                    print(f"   ✅ Price looks reasonable")
        else:
            print(f"❌ Failed to get components: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking components: {e}")

def test_recommendation():
    """Test if recommendations work with corrected prices"""
    print(f"\n🎯 Testing Recommendations with Corrected Prices")
    print("=" * 50)
    
    test_case = {"budget": 50000, "purpose": "gaming_budget"}
    
    try:
        response = requests.post("http://localhost:8000/recommend-build", json=test_case)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Build recommendation successful!")
            print(f"  Budget: ৳{test_case['budget']:,}")
            print(f"  Total Price: ৳{result['total_price']:,}")
            print(f"  Remaining Budget: ৳{result['remaining_budget']:,}")
            print(f"  Components: {list(result['build'].keys())}")
            
            # Check individual component prices
            print(f"\n📋 Component Details:")
            for category, component in result['build'].items():
                if component and component.get('name'):
                    print(f"  {category}: {component['name']}")
                    print(f"    Price: ৳{component['price_BDT']:,}")
                    print(f"    Specs: {component.get('specs', {})}")
        else:
            print(f"❌ Build recommendation failed: {response.status_code}")
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing recommendation: {e}")

def main():
    """Main test function"""
    print("🚀 Price Extraction Test")
    print("=" * 30)
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not running. Please start it first with: python start.py")
            return
    except:
        print("❌ API is not running. Please start it first with: python start.py")
        return
    
    test_price_extraction()
    test_recommendation()
    
    print(f"\n🎉 Price extraction test completed!")

if __name__ == "__main__":
    main()
