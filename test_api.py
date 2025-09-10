"""
Simple test script for PC Builder API
"""
import asyncio
import json
import requests
import time
from datetime import datetime

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

def test_api_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test an API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TEST_TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TEST_TIMEOUT)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"✅ {method} {endpoint} - Status: {response.status_code}")
        
        if response.status_code == expected_status:
            try:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
            return True
        else:
            print(f"   ❌ Expected {expected_status}, got {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False

def test_build_recommendation():
    """Test build recommendation endpoint"""
    test_cases = [
        {
            "name": "Budget Gaming Build",
            "data": {
                "budget": 50000,
                "purpose": "gaming_budget"
            }
        },
        {
            "name": "Mid-Range Gaming Build", 
            "data": {
                "budget": 80000,
                "purpose": "gaming_mid"
            }
        },
        {
            "name": "Office Build",
            "data": {
                "budget": 35000,
                "purpose": "office"
            }
        },
        {
            "name": "Content Creation Build",
            "data": {
                "budget": 120000,
                "purpose": "content_creation"
            }
        }
    ]
    
    print("\n🧪 Testing Build Recommendations...")
    success_count = 0
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['name']} ---")
        if test_api_endpoint("/recommend-build", "POST", test_case["data"]):
            success_count += 1
    
    print(f"\nBuild recommendation tests: {success_count}/{len(test_cases)} passed")
    return success_count == len(test_cases)

def test_components_endpoint():
    """Test components listing endpoint"""
    print("\n🧪 Testing Components Endpoint...")
    
    test_cases = [
        ("/components", "All components"),
        ("/components?category=CPU", "CPU components only"),
        ("/components?max_price=50000", "Components under 50k"),
        ("/components?category=GPU&max_price=100000", "GPUs under 100k")
    ]
    
    success_count = 0
    for endpoint, description in test_cases:
        print(f"\n--- Testing {description} ---")
        if test_api_endpoint(endpoint):
            success_count += 1
    
    print(f"\nComponents endpoint tests: {success_count}/{len(test_cases)} passed")
    return success_count == len(test_cases)

def test_utility_endpoints():
    """Test utility endpoints"""
    print("\n🧪 Testing Utility Endpoints...")
    
    endpoints = [
        ("/health", "Health check"),
        ("/build-templates", "Build templates"),
        ("/market-insights", "Market insights")
    ]
    
    success_count = 0
    for endpoint, description in endpoints:
        print(f"\n--- Testing {description} ---")
        if test_api_endpoint(endpoint):
            success_count += 1
    
    print(f"\nUtility endpoint tests: {success_count}/{len(endpoints)} passed")
    return success_count == len(endpoints)

def test_comparison_endpoint():
    """Test build comparison endpoint"""
    print("\n🧪 Testing Build Comparison...")
    
    comparison_data = {
        "budgets": [50000, 80000, 120000],
        "purpose": "gaming_mid"
    }
    
    return test_api_endpoint("/compare-builds", "POST", comparison_data)

def wait_for_api():
    """Wait for API to be ready"""
    print("⏳ Waiting for API to be ready...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is ready!")
                return True
        except:
            pass
        
        print(f"   Attempt {i+1}/30...")
        time.sleep(1)
    
    print("❌ API is not responding after 30 seconds")
    return False

def main():
    """Run all tests"""
    print("🚀 PC Builder API Test Suite")
    print("=" * 50)
    
    # Wait for API to be ready
    if not wait_for_api():
        print("❌ Cannot proceed - API is not available")
        return
    
    # Run tests
    tests = [
        ("Health Check", lambda: test_api_endpoint("/health")),
        ("Components", test_components_endpoint),
        ("Build Recommendations", test_build_recommendation),
        ("Build Comparison", test_comparison_endpoint),
        ("Utility Endpoints", test_utility_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the API logs for details.")

if __name__ == "__main__":
    main()
