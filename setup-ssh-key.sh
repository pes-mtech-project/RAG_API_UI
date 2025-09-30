#!/bin/bash

# SSH Key Setup Script for EC2 Instance
# This script adds your SSH public key to the EC2 instance

echo "🔑 SSH Key Setup for EC2 Instance"
echo "================================"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get instance details
INSTANCE_ID="i-05cf3774f0646b47d"  # Your actual instance ID
REGION="ap-south-1"

echo "📋 Instance ID: $INSTANCE_ID"
echo "🌍 Region: $REGION"

# Check if SSH key exists
if [ ! -f ~/.ssh/finbert-aws.pub ]; then
    echo "❌ SSH public key not found at ~/.ssh/finbert-aws.pub"
    echo "Please ensure you have the SSH key pair ready."
    exit 1
fi

# Read the public key
SSH_PUBLIC_KEY=$(cat ~/.ssh/finbert-aws.pub)
echo "🔍 Found SSH public key: ${SSH_PUBLIC_KEY:0:50}..."

# Create user data script
USER_DATA=$(cat << EOF
#!/bin/bash
echo "$SSH_PUBLIC_KEY" >> /home/ec2-user/.ssh/authorized_keys
chmod 600 /home/ec2-user/.ssh/authorized_keys
chown ec2-user:ec2-user /home/ec2-user/.ssh/authorized_keys
echo "SSH key added successfully" > /tmp/ssh-key-setup.log
EOF
)

echo "🔄 Stopping EC2 instance..."
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID --region $REGION

echo "📝 Adding SSH key via user data..."
aws ec2 modify-instance-attribute --instance-id $INSTANCE_ID --user-data "$USER_DATA" --region $REGION

echo "▶️  Starting EC2 instance..."
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

echo "✅ SSH key setup completed!"
echo "🧪 Testing SSH connection..."

# Get instance IP
INSTANCE_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "🌐 Instance IP: $INSTANCE_IP"

echo "🔗 You can now connect using:"
echo "   ssh -i ~/.ssh/finbert-aws ec2-user@$INSTANCE_IP"
echo ""
echo "⏳ Note: Wait a few minutes for the instance to fully boot before testing SSH."