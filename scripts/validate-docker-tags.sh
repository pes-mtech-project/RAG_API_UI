#!/bin/bash

# 🔍 Docker Tag Validation Script
# Validates that all Docker tags in workflows follow correct naming conventions

set -e

echo "🔍 DOCKER TAG VALIDATION"
echo "========================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

WORKFLOW_DIR=".github/workflows"
ERRORS=0

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ERRORS=$((ERRORS + 1))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

validate_docker_tags() {
    local file="$1"
    echo "🔍 Checking: $file"
    
    # Check for problematic tag patterns
    local problematic_patterns=(
        "prefix={{.*}}-"        # Dynamic prefix with trailing dash
        "prefix=-"              # Prefix starting with dash  
        "{{branch}}-"           # Branch variable with dash
    )
    
    local found_issues=false
    
    for pattern in "${problematic_patterns[@]}"; do
        if grep -q "$pattern" "$file"; then
            print_error "Found problematic tag pattern '$pattern' in $file"
            grep -n "$pattern" "$file" | sed 's/^/  Line /'
            found_issues=true
        fi
    done
    
    # Check for valid tag patterns  
    local valid_patterns=(
        "type=raw,value="       # Raw value tags
        "type=ref,event="       # Reference tags
        "type=sha,prefix=.*[^-]$"  # SHA tags with non-dash ending prefix
    )
    
    local has_valid_tags=false
    for pattern in "${valid_patterns[@]}"; do
        if grep -q "$pattern" "$file"; then
            has_valid_tags=true
            break
        fi
    done
    
    if ! $found_issues && $has_valid_tags; then
        print_success "Docker tags look good in $file"
    elif ! $has_valid_tags; then
        print_warning "No Docker metadata configuration found in $file"
    fi
    
    echo ""
}

# Main validation
echo "📋 Scanning workflow files for Docker tag configurations..."
echo ""

for workflow_file in "$WORKFLOW_DIR"/*.yml; do
    if [[ -f "$workflow_file" ]]; then
        # Only check files that contain Docker metadata configuration
        if grep -q "docker/metadata-action" "$workflow_file"; then
            validate_docker_tags "$workflow_file"
        fi
    fi
done

# Summary
echo "🎯 VALIDATION SUMMARY"
echo "===================="

if [[ $ERRORS -eq 0 ]]; then
    print_success "All Docker tag configurations are valid!"
    echo ""
    echo "✅ Valid tag examples found:"
    echo "   • type=raw,value=latest"
    echo "   • type=ref,event=branch"  
    echo "   • type=sha,prefix=prod-"
    echo "   • type=sha,prefix=sha-"
    echo ""
else
    print_error "Found $ERRORS Docker tag configuration issues"
    echo ""
    echo "🔧 Common fixes:"
    echo "   • Replace 'prefix={{branch}}-' with 'prefix=sha-'"
    echo "   • Replace 'prefix=-' with 'prefix=build-'"
    echo "   • Ensure prefixes don't start with hyphens"
    echo ""
    exit 1
fi

echo "🚀 Ready for container builds!"