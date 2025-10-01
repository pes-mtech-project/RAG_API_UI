#!/bin/bash

# Validate Workflow Fix
# This script confirms the workflow YAML syntax and structure are correct

echo "🔧 Validating Infrastructure Workflow Fix"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

WORKFLOW_FILE=".github/workflows/infrastructure.yml"

echo -e "${BLUE}📋 Checking workflow file...${NC}"

# Check if file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo -e "${RED}❌ Workflow file not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Workflow file exists${NC}"

# Check YAML syntax
echo -e "${BLUE}🔍 Validating YAML syntax...${NC}"
if python3 -c "import yaml; yaml.safe_load(open('$WORKFLOW_FILE'))" 2>/dev/null; then
    echo -e "${GREEN}✅ YAML syntax is valid${NC}"
else
    echo -e "${RED}❌ YAML syntax errors found${NC}"
    python3 -c "import yaml; yaml.safe_load(open('$WORKFLOW_FILE'))" || true
    exit 1
fi

# Check workflow structure
echo -e "${BLUE}🔍 Checking workflow structure...${NC}"

# Check for new action parameter
if grep -q "action:" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ New 'action' parameter found${NC}"
else
    echo -e "${RED}❌ 'action' parameter not found${NC}"
    exit 1
fi

# Check for choice type
if grep -q "type: choice" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ Choice parameter type configured${NC}"
else
    echo -e "${RED}❌ Choice parameter type not found${NC}"
    exit 1
fi

# Check for create/destroy options
if grep -A2 "options:" "$WORKFLOW_FILE" | grep -q "create" && grep -A2 "options:" "$WORKFLOW_FILE" | grep -q "destroy"; then
    echo -e "${GREEN}✅ Create/destroy options configured${NC}"
else
    echo -e "${RED}❌ Create/destroy options not properly configured${NC}"
    exit 1
fi

# Check for updated condition syntax
if grep -q "inputs.action == 'create'" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ Create condition updated${NC}"
else
    echo -e "${RED}❌ Create condition not updated${NC}"
    exit 1
fi

if grep -q "inputs.action == 'destroy'" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ Destroy condition updated${NC}"
else
    echo -e "${RED}❌ Destroy condition not updated${NC}"
    exit 1
fi

# Check SSH key implementation
if grep -q "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDgmTmruJ6hX7e7YM1VJ0j2MrZGyANVCOln77jumi1JmHDta65DeJf2e" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ SSH public key is hardcoded${NC}"
else
    echo -e "${RED}❌ SSH public key not found${NC}"
    exit 1
fi

# Check that we're using echo instead of heredoc for SSH key
if grep -q 'echo "ssh-rsa.*" > temp_public_key.pub' "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ SSH key uses safe echo method${NC}"
else
    echo -e "${RED}❌ SSH key method not updated${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All workflow fixes validated successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Summary of fixes:${NC}"
echo "• ✅ YAML syntax is valid"
echo "• ✅ Changed from 'destroy: boolean' to 'action: choice'"
echo "• ✅ Added create/destroy dropdown options"
echo "• ✅ Updated conditional logic for new parameter structure"
echo "• ✅ Fixed SSH key import to avoid YAML parsing issues"
echo "• ✅ Hardcoded your specific SSH public key"
echo ""
echo -e "${YELLOW}🚀 Ready to test!${NC}"
echo ""
echo "The workflow should now:"
echo "1. ✅ Build without YAML syntax errors"
echo "2. ✅ Show a dropdown with 'create' and 'destroy' options"
echo "3. ✅ Use your existing SSH key consistently"
echo "4. ✅ Work reliably across destroy/rebuild cycles"
echo ""
echo -e "${GREEN}Go to GitHub Actions and test the fixed workflow!${NC}"