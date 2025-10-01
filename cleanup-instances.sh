#!/bin/bash

# Instance Cleanup Script
echo "🔍 Instance Cleanup for FinBERT Infrastructure"
echo "=============================================="
echo ""

export AWS_DEFAULT_REGION=ap-south-1
ELASTIC_IP="3.7.194.20"

echo "1. 🔍 Checking running instances..."
echo "This may take a moment..."

# Get running instances
INSTANCES=$(aws ec2 describe-instances \
  --filters 'Name=instance-state-name,Values=running' \
  --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key==`Name`].Value|[0],LaunchTime]' \
  --output text 2>/dev/null)

if [ -z "$INSTANCES" ]; then
  echo "❌ No running instances found or AWS CLI timeout"
  echo ""
  echo "🔧 Manual cleanup steps:"
  echo "1. Go to AWS Console: https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#Instances:"
  echo "2. Look for running instances with names like 'finbert-rag-instance' or 'infrastructure-test'"
  echo "3. Keep the one with Elastic IP $ELASTIC_IP"
  echo "4. Terminate the duplicate instance(s)"
  exit 1
fi

echo "✅ Found running instances:"
echo "$INSTANCES"
echo ""

echo "2. 🔍 Checking which instance has the Elastic IP ($ELASTIC_IP)..."
CORRECT_INSTANCE=$(aws ec2 describe-addresses \
  --query "Addresses[?PublicIp=='$ELASTIC_IP'].InstanceId" \
  --output text 2>/dev/null)

if [ -n "$CORRECT_INSTANCE" ] && [ "$CORRECT_INSTANCE" != "None" ]; then
  echo "✅ Elastic IP is assigned to: $CORRECT_INSTANCE"
  echo ""
  
  echo "3. 🧹 Identifying instances to terminate..."
  echo "Instances that should be terminated (don't have the Elastic IP):"
  
  # Get all running instance IDs
  ALL_INSTANCES=$(aws ec2 describe-instances \
    --filters 'Name=instance-state-name,Values=running' \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text 2>/dev/null)
  
  TERMINATE_LIST=""
  for instance in $ALL_INSTANCES; do
    if [ "$instance" != "$CORRECT_INSTANCE" ]; then
      echo "- $instance (duplicate/test instance)"
      TERMINATE_LIST="$TERMINATE_LIST $instance"
    fi
  done
  
  if [ -n "$TERMINATE_LIST" ]; then
    echo ""
    echo "🔧 To clean up duplicate instances, run:"
    echo "aws ec2 terminate-instances --region ap-south-1 --instance-ids$TERMINATE_LIST"
    echo ""
    echo "⚠️  This will terminate the duplicate instances. Make sure to keep $CORRECT_INSTANCE"
  else
    echo ""
    echo "✅ No duplicate instances found. Only the correct instance is running."
  fi
  
else
  echo "❌ Elastic IP not assigned to any instance"
  echo ""
  echo "🔧 Manual steps needed:"
  echo "1. Check AWS Console to see which instances are running"
  echo "2. Identify the correct instance (latest launched)"
  echo "3. Associate Elastic IP with the correct instance"
  echo "4. Terminate the duplicate instance"
fi

echo ""
echo "4. 🔗 SSH Connection Test:"
echo "Once you have only one instance running, test SSH:"
echo "ssh -i finbert-rag-key-new.pem ec2-user@$ELASTIC_IP"
echo ""
echo "🌐 AWS Console Links:"
echo "- EC2 Instances: https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#Instances:"
echo "- Elastic IPs: https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#Addresses:"