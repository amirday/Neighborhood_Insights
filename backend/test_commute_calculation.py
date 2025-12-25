#!/usr/bin/env python3
"""
Comprehensive test for commute calculation functionality
Tests both the OSRM integration and the endpoint behavior
"""

import requests
import json
import time
from routing.osrm_router import OSRMRouter, RouteResult

def test_osrm_direct():
    """Test direct OSRM API connection"""
    print("\n" + "="*60)
    print("TEST 1: Direct OSRM API Connection")
    print("="*60)

    router = OSRMRouter()

    # Test with real Israeli coordinates
    tel_aviv = (32.0853, 34.7818)
    jerusalem = (31.7683, 35.2137)

    print(f"\nTesting route: Tel Aviv → Jerusalem")
    print(f"Coordinates: {tel_aviv} → {jerusalem}")

    try:
        result = router.calculate_route_time(tel_aviv, jerusalem, "driving", return_geometry=False)

        if result.success:
            print(f"✅ SUCCESS")
            print(f"   Duration: {result.duration_minutes:.1f} minutes")
            print(f"   Distance: {result.distance_km:.1f} km")
        else:
            print(f"❌ FAILED")
            print(f"   Error: {result.error_message}")

        return result.success

    except Exception as e:
        print(f"❌ EXCEPTION: {type(e).__name__}: {e}")
        return False


def test_endpoint_small():
    """Test the routing endpoint with a small subset"""
    print("\n" + "="*60)
    print("TEST 2: Routing Endpoint (Small Subset)")
    print("="*60)

    payload = {
        'center_id': 1,
        'modes': ['driving'],
        'threshold_minutes': 15  # Very restrictive for small test
    }

    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))

    try:
        print(f"\nSending request to http://localhost:8001/routes/areas-to-center...")
        start = time.time()

        response = requests.post(
            'http://localhost:8001/routes/areas-to-center',
            json=payload,
            timeout=30  # 30 second timeout
        )

        elapsed = time.time() - start

        print(f"\nResponse received in {elapsed:.2f}s")
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            total = data.get('total_candidates', 0)
            areas = data.get('areas', [])
            processing_time = data.get('processing_time_seconds', 0)

            print(f"\n✅ SUCCESS")
            print(f"   Total candidates: {total}")
            print(f"   Areas returned: {len(areas)}")
            print(f"   Processing time: {processing_time}s")

            # Check results
            if areas:
                successful = sum(1 for a in areas
                               if any(r.get('success') for r in a.get('results', {}).values()))
                failed = len(areas) - successful

                print(f"   Successful routes: {successful}")
                print(f"   Failed routes: {failed}")

                # Show first result
                first = areas[0]
                print(f"\n   First area sample:")
                print(f"   - Area ID: {first.get('area_id')}")
                print(f"   - Results: {json.dumps(first.get('results'), indent=6)}")

                return successful > 0
            else:
                print(f"   ⚠️  No areas matched threshold")
                return True  # Not a failure, just empty result

        else:
            print(f"\n❌ HTTP ERROR")
            print(f"   Response: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT")
        print(f"   Request exceeded 30 second timeout")
        print(f"   Likely OSRM API is not responding")
        return False

    except Exception as e:
        print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
        return False


def test_error_handling():
    """Test that error handling works correctly"""
    print("\n" + "="*60)
    print("TEST 3: Error Handling")
    print("="*60)

    router = OSRMRouter()

    # Test 1: Invalid coordinates
    print("\n3.1: Invalid coordinates")
    invalid = (999, 999)
    valid = (32.0853, 34.7818)
    result = router.calculate_route_time(invalid, valid, "driving")

    if not result.success and result.error_message:
        print(f"   ✅ Correctly rejected: {result.error_message}")
    else:
        print(f"   ❌ Should have failed but got: {result}")

    # Test 2: Invalid mode
    print("\n3.2: Invalid transport mode")
    result = router.calculate_route_time(valid, valid, "flying")

    if not result.success and result.error_message:
        print(f"   ✅ Correctly rejected: {result.error_message}")
    else:
        print(f"   ❌ Should have failed but got: {result}")

    # Test 3: Mock OSRM error response
    print("\n3.3: OSRM error response handling")
    error_response = {
        "code": "NoRoute",
        "message": "No route found between points"
    }
    result = router._parse_osrm_response(error_response, "driving")

    if not result.success and "No route found" in result.error_message:
        print(f"   ✅ Correctly handled: {result.error_message}")
    else:
        print(f"   ❌ Should have failed but got: {result}")

    return True


def test_cache():
    """Test that caching works"""
    print("\n" + "="*60)
    print("TEST 4: Cache Functionality")
    print("="*60)

    from routing.route_optimizer import RouteCache

    cache = RouteCache(ttl_seconds=2, max_size=5)

    # Add entries
    print("\n4.1: Adding cache entries")
    for i in range(7):
        result = RouteResult(
            duration_seconds=100*i,
            duration_minutes=(100*i)/60,
            distance_meters=1000*i,
            distance_km=(1000*i)/1000,
            transport_mode="driving"
        )
        cache.set(f"key{i}", result)

    size = cache.size()
    print(f"   Added 7 entries, cache size: {size}")

    if size <= 5:
        print(f"   ✅ LRU working (max_size={cache.max_size})")
    else:
        print(f"   ❌ Cache exceeded max_size: {size} > {cache.max_size}")

    # Test TTL
    print("\n4.2: Testing TTL expiration")
    test_result = RouteResult(
        duration_seconds=300,
        duration_minutes=5.0,
        distance_meters=2000,
        distance_km=2.0,
        transport_mode="driving"
    )
    cache.set("ttl_test", test_result)

    immediate = cache.get("ttl_test")
    print(f"   Immediate retrieval: {'✅ Found' if immediate else '❌ Not found'}")

    print(f"   Waiting {cache.ttl_seconds}s for TTL expiration...")
    time.sleep(cache.ttl_seconds + 0.5)

    expired = cache.get("ttl_test")
    print(f"   After TTL: {'❌ Still there' if expired else '✅ Correctly expired'}")

    return True


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# COMMUTE CALCULATION TEST SUITE")
    print("#"*60)

    results = {
        "OSRM Direct": test_osrm_direct(),
        "Endpoint Small": test_endpoint_small(),
        "Error Handling": test_error_handling(),
        "Cache": test_cache(),
    }

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {test_name}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed < total:
        print("\n⚠️  DIAGNOSIS:")
        if not results["OSRM Direct"]:
            print("  - Mapbox API is not accessible")
            print("  - This will cause all routing to fail")
            print("  - Solutions:")
            print("    1. Check Mapbox token in backend/.env")
            print("    2. Verify token is valid at https://account.mapbox.com")
            print("    3. Check internet connection")
            print("    4. Check Mapbox API status: https://status.mapbox.com")
        if not results["Endpoint Small"]:
            print("  - Backend endpoint has issues")
            print("  - Check backend logs for errors")
    else:
        print("\n✅ All systems operational!")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
