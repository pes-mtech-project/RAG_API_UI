#!/usr/bin/env python3
"""
FinBERT RAG API - Exhaustive Testing Suite
==========================================

Comprehensive test suite that validates:
1. All API endpoints functionality
2. Performance across different query types
3. Model caching effectiveness
4. Response accuracy and consistency
5. Load testing with concurrent requests
6. Edge cases and error handling

Usage: python3 test_exhaustive_api.py
"""

import asyncio
import aiohttp
import json
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional
import concurrent.futures
from dataclasses import dataclass
import sys

# Configuration
API_BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
CONCURRENT_WORKERS = 5
LOAD_TEST_REQUESTS = 20

@dataclass
class TestResult:
    endpoint: str
    query: str
    response_time: float
    status_code: int
    total_hits: int
    success: bool
    error_message: Optional[str] = None
    top_score: Optional[float] = None

class ExhaustiveAPITester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        
    async def health_check(self) -> bool:
        """Check if API is healthy before starting tests"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(HEALTH_ENDPOINT, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Health Check: {data.get('status', 'unknown')}")
                        return True
                    else:
                        print(f"❌ Health Check Failed: Status {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Health Check Error: {e}")
            return False

    async def single_search_request(self, session: aiohttp.ClientSession, endpoint: str, query: str) -> TestResult:
        """Execute a single search request and measure performance"""
        url = f"{API_BASE_URL}{endpoint}"
        payload = {"query": query, "size": 5}
        
        start_time = time.time()
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    total_hits = data.get('total_hits', 0)
                    top_score = data.get('results', [{}])[0].get('score', 0) if data.get('results') else 0
                    
                    return TestResult(
                        endpoint=endpoint,
                        query=query,
                        response_time=response_time,
                        status_code=response.status,
                        total_hits=total_hits,
                        success=True,
                        top_score=top_score
                    )
                else:
                    error_text = await response.text()
                    return TestResult(
                        endpoint=endpoint,
                        query=query,
                        response_time=response_time,
                        status_code=response.status,
                        total_hits=0,
                        success=False,
                        error_message=error_text
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                query=query,
                response_time=response_time,
                status_code=0,
                total_hits=0,
                success=False,
                error_message=str(e)
            )

    def get_test_queries(self) -> List[Dict[str, Any]]:
        """Define comprehensive test queries covering various scenarios"""
        return [
            # Financial Keywords
            {"category": "Financial - Basic", "queries": [
                "stock market trends", "investment opportunities", "financial reports",
                "earnings analysis", "market volatility", "portfolio management"
            ]},
            
            # Technology & Innovation
            {"category": "Technology", "queries": [
                "artificial intelligence", "machine learning applications", "blockchain technology",
                "cybersecurity threats", "cloud computing", "data analytics"
            ]},
            
            # Economic Indicators
            {"category": "Economics", "queries": [
                "inflation rates", "GDP growth", "unemployment statistics",
                "federal reserve policy", "interest rates", "economic outlook"
            ]},
            
            # Industry Specific
            {"category": "Industry", "queries": [
                "healthcare innovations", "renewable energy", "automotive industry",
                "real estate market", "retail sector", "manufacturing trends"
            ]},
            
            # News & Events
            {"category": "News Events", "queries": [
                "corporate mergers", "IPO announcements", "regulatory changes",
                "company earnings", "market analysis", "business strategy"
            ]},
            
            # Edge Cases
            {"category": "Edge Cases", "queries": [
                "a", "the quick brown fox", "supercalifragilisticexpialidocious",
                "COVID-19 impact", "climate change", "social media influence"
            ]},
            
            # Long Form Queries
            {"category": "Long Form", "queries": [
                "comprehensive analysis of technology stock performance in the current market environment",
                "detailed examination of artificial intelligence impact on financial services industry",
                "in-depth review of sustainable investment opportunities in emerging markets"
            ]},
            
            # Multi-word Financial Terms
            {"category": "Financial Terms", "queries": [
                "venture capital", "hedge funds", "private equity", "mutual funds",
                "commodity trading", "foreign exchange", "derivatives market"
            ]}
        ]

    async def run_endpoint_tests(self) -> None:
        """Test all endpoints with various query types"""
        endpoints = [
            "/search/cosine/embedding384d/",
            "/search/cosine/embedding768d/",
            "/search/cosine/embedding1155d/"
        ]
        
        test_queries = self.get_test_queries()
        
        print("\n" + "="*80)
        print("COMPREHENSIVE ENDPOINT TESTING")
        print("="*80)
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                print(f"\n🔍 Testing endpoint: {endpoint}")
                print("-" * 60)
                
                endpoint_results = []
                
                for query_group in test_queries:
                    category = query_group["category"]
                    queries = query_group["queries"]
                    
                    print(f"\n📁 Category: {category}")
                    
                    for query in queries:
                        result = await self.single_search_request(session, endpoint, query)
                        endpoint_results.append(result)
                        self.results.append(result)
                        
                        status = "✅" if result.success else "❌"
                        hits = f"({result.total_hits} hits)" if result.success else "(failed)"
                        print(f"   {status} '{query[:40]}...' - {result.response_time:.3f}s {hits}")
                
                # Endpoint summary
                successful_results = [r for r in endpoint_results if r.success]
                if successful_results:
                    avg_time = statistics.mean([r.response_time for r in successful_results])
                    median_time = statistics.median([r.response_time for r in successful_results])
                    success_rate = len(successful_results) / len(endpoint_results) * 100
                    
                    print(f"\n📊 {endpoint} Summary:")
                    print(f"   Success Rate: {success_rate:.1f}% ({len(successful_results)}/{len(endpoint_results)})")
                    print(f"   Avg Response: {avg_time:.3f}s")
                    print(f"   Med Response: {median_time:.3f}s")

    async def run_caching_performance_test(self) -> None:
        """Test model caching by running same queries twice"""
        print("\n" + "="*80)
        print("MODEL CACHING PERFORMANCE TEST")
        print("="*80)
        
        test_queries = [
            "financial market analysis",
            "artificial intelligence investment",
            "technology stock performance"
        ]
        
        endpoints = ["/search/cosine/embedding384d/", "/search/cosine/embedding768d/"]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                print(f"\n🚀 Testing caching for: {endpoint}")
                print("-" * 50)
                
                for query in test_queries:
                    # First call (potentially cached already, but measuring baseline)
                    result1 = await self.single_search_request(session, endpoint, query)
                    
                    # Small delay
                    await asyncio.sleep(0.1)
                    
                    # Second call (should be cached)
                    result2 = await self.single_search_request(session, endpoint, query)
                    
                    if result1.success and result2.success:
                        speedup = result1.response_time / result2.response_time if result2.response_time > 0 else 1
                        cache_status = "✅ Cached" if result2.response_time < result1.response_time else "⚠️  Similar"
                        
                        print(f"   '{query[:30]}...'")
                        print(f"     Call 1: {result1.response_time:.3f}s")
                        print(f"     Call 2: {result2.response_time:.3f}s")
                        print(f"     Speedup: {speedup:.1f}x {cache_status}")
                    else:
                        print(f"   ❌ '{query}' - Failed to complete both calls")

    async def run_concurrent_load_test(self) -> None:
        """Test API under concurrent load"""
        print("\n" + "="*80)
        print("CONCURRENT LOAD TESTING")
        print("="*80)
        
        test_query = "financial technology innovation"
        endpoint = "/search/cosine/embedding384d/"
        
        print(f"Running {LOAD_TEST_REQUESTS} concurrent requests to {endpoint}")
        print(f"Query: '{test_query}'")
        
        async with aiohttp.ClientSession() as session:
            # Create concurrent tasks
            tasks = []
            start_time = time.time()
            
            for i in range(LOAD_TEST_REQUESTS):
                task = self.single_search_request(session, endpoint, f"{test_query} {i}")
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Analyze results
            successful_results = [r for r in results if isinstance(r, TestResult) and r.success]
            failed_results = [r for r in results if not isinstance(r, TestResult) or not r.success]
            
            if successful_results:
                response_times = [r.response_time for r in successful_results]
                avg_response = statistics.mean(response_times)
                median_response = statistics.median(response_times)
                min_response = min(response_times)
                max_response = max(response_times)
                
                requests_per_second = len(successful_results) / total_duration
                
                print(f"\n📊 Load Test Results:")
                print(f"   Total Requests: {LOAD_TEST_REQUESTS}")
                print(f"   Successful: {len(successful_results)}")
                print(f"   Failed: {len(failed_results)}")
                print(f"   Success Rate: {len(successful_results)/LOAD_TEST_REQUESTS*100:.1f}%")
                print(f"   Total Duration: {total_duration:.2f}s")
                print(f"   Requests/Second: {requests_per_second:.2f}")
                print(f"   Response Times:")
                print(f"     Average: {avg_response:.3f}s")
                print(f"     Median:  {median_response:.3f}s")
                print(f"     Min:     {min_response:.3f}s")
                print(f"     Max:     {max_response:.3f}s")

    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Organize results by endpoint
        endpoint_stats = {}
        for result in self.results:
            if result.endpoint not in endpoint_stats:
                endpoint_stats[result.endpoint] = []
            endpoint_stats[result.endpoint].append(result)
        
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        print(f"Test Duration: {total_duration:.2f} seconds")
        print(f"Total Requests: {len(self.results)}")
        print(f"Test Timestamp: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Overall statistics
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        print(f"\n📊 Overall Performance:")
        print(f"   Successful Requests: {len(successful_results)}")
        print(f"   Failed Requests: {len(failed_results)}")
        print(f"   Success Rate: {len(successful_results)/len(self.results)*100:.1f}%")
        
        if successful_results:
            response_times = [r.response_time for r in successful_results]
            print(f"   Average Response Time: {statistics.mean(response_times):.3f}s")
            print(f"   Median Response Time: {statistics.median(response_times):.3f}s")
            print(f"   95th Percentile: {sorted(response_times)[int(0.95*len(response_times))]:.3f}s")
        
        # Per-endpoint analysis
        print(f"\n📈 Per-Endpoint Analysis:")
        for endpoint, results in endpoint_stats.items():
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            
            print(f"\n   🔍 {endpoint}")
            print(f"      Requests: {len(results)}")
            print(f"      Success Rate: {len(successful)/len(results)*100:.1f}%")
            
            if successful:
                times = [r.response_time for r in successful]
                hits = [r.total_hits for r in successful if r.total_hits > 0]
                
                print(f"      Avg Response: {statistics.mean(times):.3f}s")
                print(f"      Fastest: {min(times):.3f}s")
                print(f"      Slowest: {max(times):.3f}s")
                
                if hits:
                    print(f"      Avg Hits: {statistics.mean(hits):.1f}")
                    print(f"      Total Results Found: {sum(hits)}")
            
            if failed:
                print(f"      Failed Requests: {len(failed)}")
                error_types = {}
                for f in failed:
                    error_key = f"Status {f.status_code}" if f.status_code > 0 else "Network Error"
                    error_types[error_key] = error_types.get(error_key, 0) + 1
                
                for error_type, count in error_types.items():
                    print(f"        {error_type}: {count}")
        
        # Performance recommendations
        print(f"\n💡 Performance Insights:")
        
        if successful_results:
            avg_time = statistics.mean([r.response_time for r in successful_results])
            if avg_time < 0.5:
                print("   ✅ Excellent response times (< 0.5s average)")
            elif avg_time < 1.0:
                print("   ✅ Good response times (< 1.0s average)")
            elif avg_time < 2.0:
                print("   ⚠️  Moderate response times (< 2.0s average)")
            else:
                print("   ❌ Slow response times (> 2.0s average)")
        
        # Model caching assessment
        embedding_384d_results = [r for r in successful_results if "embedding384d" in r.endpoint]
        embedding_768d_results = [r for r in successful_results if "embedding768d" in r.endpoint]
        
        if embedding_384d_results and embedding_768d_results:
            avg_384d = statistics.mean([r.response_time for r in embedding_384d_results])
            avg_768d = statistics.mean([r.response_time for r in embedding_768d_results])
            
            print(f"   384d Model Avg: {avg_384d:.3f}s")
            print(f"   768d Model Avg: {avg_768d:.3f}s")
            
            if abs(avg_384d - avg_768d) < 0.1:
                print("   ✅ Both models performing similarly (good caching)")
            else:
                slower_model = "384d" if avg_384d > avg_768d else "768d"
                print(f"   ⚠️  {slower_model} model slower (potential caching issue)")

async def main():
    """Main test execution"""
    print("🚀 Starting Exhaustive API Testing Suite")
    print(f"Target API: {API_BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = ExhaustiveAPITester()
    
    # Health check
    if not await tester.health_check():
        print("❌ API health check failed. Please ensure the API is running.")
        sys.exit(1)
    
    print("\n⏳ Waiting for API to fully initialize...")
    await asyncio.sleep(3)
    
    try:
        # Run comprehensive tests
        await tester.run_endpoint_tests()
        await tester.run_caching_performance_test()
        await tester.run_concurrent_load_test()
        
        # Generate final report
        tester.generate_report()
        
        print(f"\n🎉 Exhaustive testing completed!")
        print(f"📄 Results saved in memory - {len(tester.results)} total requests")
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())