#!/bin/bash

# API Testing Script for FinBERT News RAG System
# Run this after successful deployment

API_BASE="http://3.7.194.20:8000"
STREAMLIT_URL="http://3.7.194.20:8501"

echo "🧪 Testing FinBERT News RAG API Deployment"
echo "=========================================="

# Test 1: Health Check
echo "1. Testing API Health..."
curl -s "$API_BASE/health" | jq '.' || echo "❌ Health check failed"

# Test 2: Basic Query
echo -e "\n2. Testing basic financial query..."
curl -s -X POST "$API_BASE/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the impact of inflation on stock markets?"}' | jq '.' || echo "❌ Basic query failed"

# Test 3: Complex Financial Query  
echo -e "\n3. Testing complex financial analysis..."
curl -s -X POST "$API_BASE/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How do interest rate changes affect banking sector performance?"}' | jq '.' || echo "❌ Complex query failed"

# Test 4: Market-specific Query
echo -e "\n4. Testing market-specific query..."
curl -s -X POST "$API_BASE/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tesla stock price prediction based on recent news"}' | jq '.' || echo "❌ Market query failed"

# Test 5: Response Time Test
echo -e "\n5. Testing response time..."
start_time=$(date +%s.%N)
curl -s -X POST "$API_BASE/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Federal Reserve policy impact on cryptocurrency"}' > /dev/null
end_time=$(date +%s.%N)
response_time=$(echo "$end_time - $start_time" | bc)
echo "⏱️  Response time: ${response_time}s"

# Test 6: Streamlit UI Check
echo -e "\n6. Testing Streamlit UI availability..."
if curl -s --head "$STREAMLIT_URL" | head -n 1 | grep "200 OK" > /dev/null; then
    echo "✅ Streamlit UI is accessible at $STREAMLIT_URL"
else
    echo "❌ Streamlit UI not accessible"
fi

# Test 7: Load Test (Light)
echo -e "\n7. Running light load test..."
for i in {1..5}; do
    echo "Request $i/5..."
    curl -s -X POST "$API_BASE/query" \
      -H "Content-Type: application/json" \
      -d '{"query": "Market volatility analysis"}' > /dev/null &
done
wait
echo "✅ Light load test completed"

echo -e "\n🎉 API Testing Complete!"
echo "Access your application:"
echo "  📊 Streamlit UI: $STREAMLIT_URL" 
echo "  🔌 API Docs: $API_BASE/docs"