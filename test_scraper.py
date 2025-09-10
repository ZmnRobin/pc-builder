"""
Test script to verify the improved scraper works correctly
"""
import asyncio
import requests
import time

def test_scraper_endpoints():
    """Test the scraper endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Scraper Endpoints")
    print("=" * 40)
    
    # Test scraping specific categories
    categories = ["CPU", "Motherboard", "RAM"]
    
    for category in categories:
        print(f"\n--- Testing {category} Scraping ---")
        try:
            response = requests.post(f"{base_url}/scrape-now", params={"category": category})
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {category} scraping started: {result['message']}")
            else:
                print(f"❌ Failed to start {category} scraping: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing {category} scraping: {e}")
        
        # Wait a bit between requests
        time.sleep(2)
    
    # Test scraping all components
    print(f"\n--- Testing All Components Scraping ---")
    try:
        response = requests.post(f"{base_url}/scrape-now")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ All components scraping started: {result['message']}")
        else:
            print(f"❌ Failed to start all components scraping: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing all components scraping: {e}")

def check_database_after_scraping():
    """Check database contents after scraping"""
    print(f"\n--- Checking Database Contents ---")
    
    try:
        # Check components with specs
        response = requests.get("http://localhost:8000/components?limit=5")
        if response.status_code == 200:
            components = response.json()
            print(f"✅ Found {len(components)} components")
            
            for comp in components[:3]:  # Show first 3
                print(f"\nComponent: {comp['name']}")
                print(f"  Category: {comp['category']}")
                print(f"  Price: ৳{comp['price_BDT']:,}")
                print(f"  Specs: {comp.get('specs', {})}")
                print(f"  Performance Score: {comp.get('performance_score', 'N/A')}")
        else:
            print(f"❌ Failed to get components: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def test_recommendation_with_new_data():
    """Test if recommendations work with the new scraped data"""
    print(f"\n--- Testing Recommendations with New Data ---")
    
    test_cases = [
        {"budget": 50000, "purpose": "gaming_budget"},
        {"budget": 80000, "purpose": "gaming_mid"}
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['purpose']} with ৳{test_case['budget']:,}")
        try:
            response = requests.post("http://localhost:8000/recommend-build", json=test_case)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Build recommendation successful!")
                print(f"  Total Price: ৳{result['total_price']:,}")
                print(f"  Components: {list(result['build'].keys())}")
                
                # Check if motherboard was found
                if 'Motherboard' in result['build']:
                    mb = result['build']['Motherboard']
                    print(f"  Motherboard: {mb['name']}")
                    print(f"  MB Specs: {mb.get('specs', {})}")
                else:
                    print(f"  ⚠️ No motherboard found in build")
                    
            else:
                print(f"❌ Build recommendation failed: {response.status_code}")
                print(f"  Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing recommendation: {e}")

def main():
    """Main test function"""
    print("🚀 PC Builder Scraper Test Suite")
    print("=" * 50)
    
    # Wait for API to be ready
    print("⏳ Waiting for API to be ready...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is ready!")
                break
        except:
            pass
        print(f"   Attempt {i+1}/10...")
        time.sleep(2)
    else:
        print("❌ API is not responding. Please start the API first.")
        return
    
    # Run tests
    test_scraper_endpoints()
    
    print(f"\n⏳ Waiting 30 seconds for scraping to complete...")
    time.sleep(30)
    
    check_database_after_scraping()
    test_recommendation_with_new_data()
    
    print(f"\n🎉 Test suite completed!")

if __name__ == "__main__":
    main()
