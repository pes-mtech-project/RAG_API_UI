#!/bin/bash

# 🧪 CI/CD Workflow Validation Test
# Comprehensive test of all production-ready workflows

set -e

echo "🧪 CI/CD WORKFLOW COMPREHENSIVE TEST"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

TOTAL_TESTS=0
PASSED_TESTS=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_info "Testing: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        print_success "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        print_error "$test_name failed"
    fi
}

# Test 1: Workflow syntax validation
print_header "📋 1. WORKFLOW SYNTAX VALIDATION"
echo ""

workflows=(".github/workflows/production-release.yml" ".github/workflows/ecs-deployment.yml" ".github/workflows/development.yml" ".github/workflows/build-base-image.yml")

for workflow in "${workflows[@]}"; do
    if [[ -f "$workflow" ]]; then
        run_test "YAML syntax: $(basename $workflow)" "python3 -c 'import yaml; yaml.safe_load(open(\"$workflow\"))'"
    fi
done

echo ""

# Test 2: Docker configuration validation  
print_header "📦 2. DOCKER CONFIGURATION VALIDATION"
echo ""

run_test "Docker files exist" "[[ -f 'docker/Dockerfile.api' ]]"
run_test "Docker compose files exist" "[[ -f 'docker-compose.yml' ]]"
run_test "Docker tag validation" "./scripts/validate-docker-tags.sh"

echo ""

# Test 3: Release management validation
print_header "🚀 3. RELEASE MANAGEMENT VALIDATION"  
echo ""

run_test "Release manager script exists" "[[ -f 'scripts/release-manager.sh' && -x 'scripts/release-manager.sh' ]]"
run_test "Release manager prerequisites" "./scripts/release-manager.sh status | grep -q 'Prerequisites check passed'"

echo ""

# Test 4: Documentation validation
print_header "📚 4. DOCUMENTATION VALIDATION"
echo ""

run_test "Production deployment guide exists" "[[ -f 'PRODUCTION_DEPLOYMENT.md' ]]"
run_test "README updated with workflow info" "grep -q 'Production Release' README.md"
run_test "Workflow documentation complete" "grep -qi 'semantic versioning' README.md"

echo ""

# Test 5: Infrastructure validation
print_header "🏗️ 5. INFRASTRUCTURE VALIDATION"
echo ""

run_test "CDK infrastructure exists" "[[ -d 'infrastructure' && -f 'infrastructure/package.json' ]]"
run_test "Scripts directory exists" "[[ -d 'scripts' ]]"
run_test "API source code exists" "[[ -f 'api/main.py' && -f 'api/requirements.txt' ]]"

echo ""

# Test 6: Workflow trigger validation
print_header "🔄 6. WORKFLOW TRIGGER VALIDATION"
echo ""

run_test "Production workflow triggers on main" "grep -q 'branches: \[ main \]' .github/workflows/production-release.yml"
run_test "Development workflow excludes main" "grep -q 'branches-ignore: \[ main \]' .github/workflows/development.yml"
run_test "ECS workflow only on develop" "grep -q 'branches: \[ develop \]' .github/workflows/ecs-deployment.yml"

echo ""

# Test 7: Container registry configuration
print_header "📦 7. CONTAINER REGISTRY VALIDATION"
echo ""

run_test "GHCR registry configured" "grep -q 'ghcr.io' .github/workflows/production-release.yml"
run_test "API image name configured" "grep -q 'finbert-api' .github/workflows/production-release.yml"
run_test "Multi-tag strategy configured" "grep -q 'type=raw,value=latest' .github/workflows/production-release.yml"

echo ""

# Test 8: Security and permissions
print_header "🔒 8. SECURITY & PERMISSIONS VALIDATION"
echo ""

run_test "Workflow permissions configured" "grep -q 'permissions:' .github/workflows/production-release.yml"
run_test "Package write permission" "grep -q 'packages: write' .github/workflows/production-release.yml"
run_test "Contents write permission" "grep -q 'contents: write' .github/workflows/production-release.yml"

echo ""

# Final summary
print_header "🎯 TEST SUMMARY"
echo "==============="
echo ""

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    print_success "All tests passed! ($PASSED_TESTS/$TOTAL_TESTS)"
    echo ""
    echo "🎉 Your CI/CD workflow is production-ready!"
    echo ""
    echo "✅ Ready for main branch release:"
    echo "   1. Create PR: develop → main"
    echo "   2. Merge PR"
    echo "   3. Run: ./scripts/release-manager.sh release minor"
    echo "   4. Monitor deployment at: https://github.com/pes-mtech-project/RAG_API_UI/actions"
    echo ""
    exit 0
else
    print_error "Some tests failed! ($PASSED_TESTS/$TOTAL_TESTS passed)"
    echo ""
    echo "🔧 Please fix the failing tests before proceeding to production release."
    echo ""
    exit 1
fi