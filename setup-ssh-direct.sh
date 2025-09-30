#!/bin/bash

# Direct SSH Key Addition Script
# This creates a simple approach to add SSH key to EC2

echo "🔑 Direct SSH Key Setup for EC2"
echo "================================"

INSTANCE_ID="i-05cf3774f0646b47d"
REGION="ap-south-1"
KEY_NAME="finbert-rag-key-new"

echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"

# Check if we can connect to the instance using the existing key pair
echo "🧪 Testing current SSH access..."
if ssh -i ~/.ssh/finbert-aws -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@3.7.194.20 "echo 'Already have access'" 2>/dev/null; then
    echo "✅ SSH access already working!"
    exit 0
fi

echo "❌ SSH access not working, setting up key..."

# Try to import the public key to AWS (this might help)
echo "📤 Importing public key to AWS..."
aws ec2 import-key-pair --key-name "$KEY_NAME-imported" --public-key-material fileb://~/.ssh/finbert-aws.pub --region $REGION 2>/dev/null || echo "Key might already exist"

# Alternative: Create user data to add the key (requires restart)
echo "⚠️  Alternative approach: Will restart the instance to add SSH key"
read -p "Proceed with instance restart? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Stopping instance..."
    aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION
    aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID --region $REGION
    
    # Create user data script
    SSH_PUBLIC_KEY=$(cat ~/.ssh/finbert-aws.pub)
    USER_DATA=$(base64 -w 0 << EOF
#!/bin/bash
echo "$SSH_PUBLIC_KEY" >> /home/ec2-user/.ssh/authorized_keys
chmod 600 /home/ec2-user/.ssh/authorized_keys
chown ec2-user:ec2-user /home/ec2-user/.ssh/authorized_keys
EOF
)
    
    echo "📝 Adding SSH key via user data..."
    aws ec2 modify-instance-attribute --instance-id $INSTANCE_ID --user-data "$USER_DATA" --region $REGION
    
    echo "▶️  Starting instance..."
    aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
    
    echo "⏳ Waiting for SSH service to be ready..."
    sleep 30
    
    echo "🧪 Testing SSH connection..."
    if ssh -i ~/.ssh/finbert-aws -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@3.7.194.20 "echo 'SSH setup successful!'"; then
        echo "✅ SSH key setup completed successfully!"
    else
        echo "❌ SSH setup failed"
        exit 1
    fi
else
    echo "ℹ️  Manual setup required. Please:"
    echo "   1. Go to EC2 Console"
    echo "   2. Connect to instance using Session Manager"
    echo "   3. Run: echo '$(cat ~/.ssh/finbert-aws.pub)' >> /home/ec2-user/.ssh/authorized_keys"
    echo "   4. Run: chmod 600 /home/ec2-user/.ssh/authorized_keys"
fi