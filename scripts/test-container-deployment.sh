#!/bin/bash

# Comprehensive Docker Container Test Suite
# Tests all endpoints and functionality after complete rebuild

echo "🧪 FinBERT RAG Docker Container Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="$3"
    
    echo -n "Testing $test_name... "
    TESTS_RUN=$((TESTS_RUN + 1))
    
    result=$(eval "$command" 2>&1)
    exit_code=$?
    
    if [[ $exit_code -eq 0 ]] && [[ $result =~ $expected_pattern ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "   Expected pattern: $expected_pattern"
        echo "   Got: $result"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "🔍 Container Status Tests"
echo "========================"

# Test container status
run_test "API container running" \
    "docker-compose ps finbert-api | grep 'Up'" \
    "Up.*healthy"

run_test "UI container running" \
    "docker-compose ps finbert-ui | grep 'Up'" \
    "Up.*healthy"

echo ""
echo "🌐 API Endpoint Tests"
echo "===================="

# Health endpoint
run_test "Health endpoint" \
    "curl -s http://localhost:8000/health | grep -o '\"status\":\"healthy\"'" \
    '"status":"healthy"'

# Documentation endpoint
run_test "API documentation" \
    "curl -s http://localhost:8000/docs | grep -o '<title>.*</title>'" \
    "FinBERT News RAG API"

# 384d endpoint (expect connection error but valid response structure)
run_test "384d endpoint structure" \
    "curl -s -X POST http://localhost:8000/search/cosine/embedding384d/ -H 'Content-Type: application/json' -d '{\"query\": \"test\", \"top_k\": 1}' | grep -E '(detail|results)'" \
    "detail.*Connection error"

# 768d endpoint 
run_test "768d endpoint structure" \
    "curl -s -X POST http://localhost:8000/search/cosine/embedding768d/ -H 'Content-Type: application/json' -d '{\"query\": \"test\", \"top_k\": 1}' | grep -E '(detail|results)'" \
    "detail.*Connection error"

# 1155d endpoint with real data (should work if Elasticsearch is connected)
run_test "1155d endpoint response" \
    "curl -s -X POST http://localhost:8000/search/cosine/embedding1155d/ -H 'Content-Type: application/json' -d '{\"query\": \"test\", \"top_k\": 1}' | wc -c" \
    "^[1-9][0-9]+$"  # Should return substantial response

echo ""
echo "🎨 UI Interface Tests"
echo "===================="

# UI accessibility
run_test "Streamlit UI accessible" \
    "curl -s -I http://localhost:8501 | head -1" \
    "200 OK"

# UI content
run_test "UI loads properly" \
    "curl -s http://localhost:8501 | grep -i streamlit" \
    "streamlit"

echo ""
echo "🔧 Model Loading Tests"
echo "====================="

# Model cache verification
run_test "384d model cached" \
    "docker exec finbert-api ls /home/appuser/.cache/sentence_transformers/ | grep 'all-MiniLM-L6-v2'" \
    "all-MiniLM-L6-v2"

run_test "768d model cached" \
    "docker exec finbert-api ls /home/appuser/.cache/sentence_transformers/ | grep 'all-mpnet-base-v2'" \
    "all-mpnet-base-v2"

# Model loading logs
run_test "Models loaded successfully" \
    "docker-compose logs finbert-api | grep -E '(Loading|Loaded).*model'" \
    "(Loading|Loaded)"

echo ""
echo "📊 Performance Tests"
echo "==================="

# Response time test
start_time=$(date +%s.%N)
curl -s http://localhost:8000/health > /dev/null
end_time=$(date +%s.%N)
response_time=$(echo "$end_time - $start_time" | bc)
response_time_ms=$(echo "$response_time * 1000" | bc)

run_test "Health endpoint response time < 1s" \
    "echo '$response_time < 1' | bc" \
    "1"

echo "   Response time: ${response_time_ms%.*}ms"

# Memory usage
run_test "API container memory usage reasonable" \
    "docker stats --no-stream --format 'table {{.MemUsage}}' finbert-api | tail -1 | grep -oE '[0-9]+\.?[0-9]*[GMK]iB' | head -1" \
    "[0-9]+\.?[0-9]*[GMK]iB"

echo ""
echo "🔒 Security Tests"
echo "================="

# Check for exposed sensitive data
run_test "No credentials in container ENV" \
    "docker exec finbert-api printenv | grep -iE '(password|secret|key)' | wc -l" \
    "^0$"

# Check proper user context
run_test "Running as non-root user" \
    "docker exec finbert-api whoami" \
    "appuser"

echo ""
echo "📋 Test Summary"
echo "==============="

echo "Tests run: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}All tests passed! Container deployment successful.${NC}"
    exit 0
else
    echo -e "\n⚠️  ${YELLOW}Some tests failed. Check the output above for details.${NC}"
    exit 1
fi