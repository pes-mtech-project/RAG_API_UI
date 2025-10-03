#!/usr/bin/env python3
"""
FinBERT API Load Testing Script
Measures API performance with configurable TPS and random queries
"""

import asyncio
import aiohttp
import json
import time
import random
import statistics
from datetime import datetime
from typing import List, Dict, Any
import argparse

# API Configuration
API_BASE_URL = "http://FinBer-FinBe-mLc1emju4Jnw-1497871200.ap-south-1.elb.amazonaws.com"
SEARCH_ENDPOINT = f"{API_BASE_URL}/search"

# Test Queries Pool
QUERIES = [
    "health", "finance", "automotive", "politics", "india", "trump", 
    "japan", "china", "modi", "biden", "economy", "stock market", 
    "inflation", "technology", "AI", "banking", "cryptocurrency",
    "healthcare", "pharmaceutical", "oil prices", "trade war",
    "elections", "congress", "parliament", "gdp growth", "recession"
]

class LoadTestResults:
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.errors: List[Dict] = []
        self.start_time = None
        self.end_time = None
        
    def add_result(self, response_time: float, success: bool, error: str = None):
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append({
                    'timestamp': datetime.now().isoformat(),
                    'error': error,
                    'response_time': response_time
                })
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self.response_times:
            return {}
            
        total_time = (self.end_time - self.start_time).total_seconds()
        actual_tps = (self.success_count + self.error_count) / total_time if total_time > 0 else 0
        
        return {
            'total_requests': len(self.response_times),
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': (self.success_count / len(self.response_times)) * 100,
            'actual_tps': round(actual_tps, 2),
            'duration_seconds': round(total_time, 2),
            'response_times': {
                'min': round(min(self.response_times), 3),
                'max': round(max(self.response_times), 3),
                'mean': round(statistics.mean(self.response_times), 3),
                'median': round(statistics.median(self.response_times), 3),
                'p95': round(statistics.quantiles(self.response_times, n=20)[18], 3) if len(self.response_times) > 20 else round(max(self.response_times), 3),
                'p99': round(statistics.quantiles(self.response_times, n=100)[98], 3) if len(self.response_times) > 100 else round(max(self.response_times), 3)
            }
        }

async def make_request(session: aiohttp.ClientSession, query: str, limit: int) -> Dict[str, Any]:
    """Make a single API request and measure response time"""
    payload = {
        "query": query,
        "limit": limit,
        "min_score": 0.6,
        "source_index": "news_finbert_embeddings"
    }
    
    start_time = time.time()
    
    try:
        async with session.post(
            SEARCH_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response_time = time.time() - start_time
            
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'response_time': response_time,
                    'status_code': response.status,
                    'result_count': len(data.get('results', [])) if isinstance(data, dict) else 0
                }
            else:
                error_text = await response.text()
                return {
                    'success': False,
                    'response_time': response_time,
                    'status_code': response.status,
                    'error': f"HTTP {response.status}: {error_text[:200]}"
                }
                
    except asyncio.TimeoutError:
        return {
            'success': False,
            'response_time': time.time() - start_time,
            'error': "Request timeout (30s)"
        }
    except Exception as e:
        return {
            'success': False,
            'response_time': time.time() - start_time,
            'error': f"Exception: {str(e)[:200]}"
        }

async def run_load_test(target_tps: float, duration_seconds: int, ramp_up_seconds: int = 10) -> LoadTestResults:
    """Run load test with specified TPS for given duration"""
    results = LoadTestResults()
    results.start_time = datetime.now()
    
    print(f"🚀 Starting load test: {target_tps} TPS for {duration_seconds} seconds")
    print(f"📊 Ramp-up period: {ramp_up_seconds} seconds")
    print(f"🎯 Target endpoint: {SEARCH_ENDPOINT}")
    print("-" * 60)
    
    # Calculate request interval
    request_interval = 1.0 / target_tps
    
    async with aiohttp.ClientSession() as session:
        # Test connectivity first
        print("🔍 Testing API connectivity...")
        test_result = await make_request(session, "test", 15)
        if not test_result['success']:
            print(f"❌ API connectivity test failed: {test_result.get('error', 'Unknown error')}")
            return results
        print(f"✅ API connectivity OK (response time: {test_result['response_time']:.3f}s)")
        print()
        
        # Start load test
        tasks = []
        test_start = time.time()
        request_count = 0
        
        while time.time() - test_start < duration_seconds:
            current_time = time.time() - test_start
            
            # Calculate current TPS based on ramp-up
            if current_time < ramp_up_seconds:
                current_tps = target_tps * (current_time / ramp_up_seconds)
                current_interval = 1.0 / max(current_tps, 0.1)  # Minimum 0.1 TPS
            else:
                current_interval = request_interval
            
            # Generate random query
            query = random.choice(QUERIES)
            limit = random.randint(15, 25)
            
            # Create task
            task = asyncio.create_task(make_request(session, query, limit))
            tasks.append((task, query, limit, time.time()))
            request_count += 1
            
            # Print progress every 10 requests
            if request_count % 10 == 0:
                elapsed = time.time() - test_start
                current_rate = request_count / elapsed if elapsed > 0 else 0
                print(f"📈 Requests sent: {request_count}, Elapsed: {elapsed:.1f}s, Rate: {current_rate:.1f} TPS")
            
            # Wait for next request
            await asyncio.sleep(current_interval)
        
        print(f"\n⏳ Waiting for {len(tasks)} pending requests to complete...")
        
        # Process completed tasks
        for task, query, limit, req_time in tasks:
            try:
                result = await task
                results.add_result(
                    result['response_time'], 
                    result['success'], 
                    result.get('error')
                )
            except Exception as e:
                results.add_result(30.0, False, f"Task exception: {str(e)}")
    
    results.end_time = datetime.now()
    return results

def print_results(results: LoadTestResults, target_tps: float):
    """Print detailed test results"""
    stats = results.get_statistics()
    
    if not stats:
        print("❌ No results to display")
        return
    
    print("\n" + "=" * 60)
    print("📊 LOAD TEST RESULTS")
    print("=" * 60)
    
    # Overall Statistics
    print(f"🎯 Target TPS: {target_tps}")
    print(f"⚡ Actual TPS: {stats['actual_tps']}")
    print(f"⏱️  Duration: {stats['duration_seconds']} seconds")
    print(f"📨 Total Requests: {stats['total_requests']}")
    print(f"✅ Successful: {stats['success_count']} ({stats['success_rate']:.1f}%)")
    print(f"❌ Failed: {stats['error_count']}")
    print()
    
    # Response Time Statistics
    if stats['response_times']:
        print("🕐 RESPONSE TIME ANALYSIS")
        print("-" * 30)
        rt = stats['response_times']
        print(f"Minimum:  {rt['min']:>8.3f}s")
        print(f"Maximum:  {rt['max']:>8.3f}s") 
        print(f"Mean:     {rt['mean']:>8.3f}s")
        print(f"Median:   {rt['median']:>8.3f}s")
        print(f"95th %:   {rt['p95']:>8.3f}s")
        print(f"99th %:   {rt['p99']:>8.3f}s")
        print()
    
    # Performance Analysis
    print("🎯 PERFORMANCE ANALYSIS")
    print("-" * 30)
    if stats['actual_tps'] >= target_tps * 0.9:
        print("✅ Target TPS achieved successfully!")
    elif stats['actual_tps'] >= target_tps * 0.7:
        print("⚠️  Target TPS partially achieved")
    else:
        print("❌ Target TPS not achieved - system likely overloaded")
    
    if rt['mean'] < 1.0:
        print("✅ Excellent response times (< 1s average)")
    elif rt['mean'] < 3.0:
        print("⚠️  Acceptable response times (< 3s average)")
    else:
        print("❌ Poor response times (> 3s average)")
    
    if stats['success_rate'] > 99:
        print("✅ Excellent reliability (> 99% success)")
    elif stats['success_rate'] > 95:
        print("⚠️  Good reliability (> 95% success)")
    else:
        print("❌ Poor reliability (< 95% success)")
    
    # Error Analysis
    if results.errors:
        print(f"\n❌ ERRORS ({len(results.errors)} total)")
        print("-" * 30)
        error_types = {}
        for error in results.errors:
            error_key = error['error'][:50] + "..." if len(error['error']) > 50 else error['error']
            error_types[error_key] = error_types.get(error_key, 0) + 1
        
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"{count:>3}x {error_type}")

async def main():
    parser = argparse.ArgumentParser(description='FinBERT API Load Testing')
    parser.add_argument('--tps', type=float, default=10.0, help='Target TPS (default: 10)')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds (default: 60)')
    parser.add_argument('--ramp-up', type=int, default=10, help='Ramp-up period in seconds (default: 10)')
    
    args = parser.parse_args()
    
    print("🔥 FinBERT API Load Testing Tool")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run the load test
    results = await run_load_test(args.tps, args.duration, args.ramp_up)
    
    # Print results
    print_results(results, args.tps)
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"load_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            'test_config': {
                'target_tps': args.tps,
                'duration': args.duration,
                'ramp_up': args.ramp_up
            },
            'results': results.get_statistics(),
            'errors': results.errors
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())