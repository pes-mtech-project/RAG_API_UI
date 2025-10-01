#!/bin/bash

# CloudFormation Stack Cleanup Script
# Handles stuck ECS stacks in CREATE_IN_PROGRESS state

set -e

echo "🔍 ECS CloudFormation Stack Cleanup Tool"
echo "======================================="

# Configuration
STACK_NAME="FinBertRagDevStack"
REGION="ap-south-1"

echo "📋 Checking stack: $STACK_NAME in region: $REGION"

# Get stack status
STACK_STATUS=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].StackStatus' \
  --output text 2>/dev/null || echo "STACK_NOT_FOUND")

echo "📊 Current status: $STACK_STATUS"

case $STACK_STATUS in
  "STACK_NOT_FOUND")
    echo "✅ No stack found. Ready for fresh deployment."
    ;;
  "CREATE_COMPLETE"|"UPDATE_COMPLETE")
    echo "✅ Stack is in good state. No cleanup needed."
    ;;
  "CREATE_IN_PROGRESS")
    echo "⚠️  Stack stuck in CREATE_IN_PROGRESS. Options:"
    echo "   1. Wait for completion (may take 20+ minutes)"
    echo "   2. Cancel creation (will delete partial resources)"
    read -p "🤔 Cancel stack creation? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "🗑️  Canceling stack creation..."
      aws cloudformation cancel-update-stack \
        --stack-name $STACK_NAME \
        --region $REGION 2>/dev/null || \
      aws cloudformation delete-stack \
        --stack-name $STACK_NAME \
        --region $REGION
      
      echo "⏳ Waiting for deletion to complete..."
      aws cloudformation wait stack-delete-complete \
        --stack-name $STACK_NAME \
        --region $REGION
      echo "✅ Stack deleted successfully!"
    else
      echo "⏳ Continuing to wait for stack completion..."
    fi
    ;;
  "UPDATE_IN_PROGRESS")
    echo "⚠️  Stack updating. Waiting for completion..."
    aws cloudformation wait stack-update-complete \
      --stack-name $STACK_NAME \
      --region $REGION
    echo "✅ Stack update completed!"
    ;;
  "CREATE_FAILED"|"UPDATE_FAILED"|"DELETE_FAILED")
    echo "❌ Stack in failed state. Attempting cleanup..."
    aws cloudformation delete-stack \
      --stack-name $STACK_NAME \
      --region $REGION
    
    echo "⏳ Waiting for deletion to complete..."
    aws cloudformation wait stack-delete-complete \
      --stack-name $STACK_NAME \
      --region $REGION
    echo "✅ Failed stack cleaned up!"
    ;;
  *)
    echo "🤷 Unknown stack status: $STACK_STATUS"
    echo "📚 Manual action may be required via AWS Console"
    ;;
esac

echo ""
echo "🎯 Stack cleanup complete!"
echo "💡 You can now retry the ECS deployment workflow."