#!/bin/bash

echo "🔑 SSH Key Setup for EC2 Instance"
echo "================================="

INSTANCE_ID="i-05cf3774f0646b47d"
REGION="ap-south-1"

# Get public key
if [ ! -f ~/.ssh/finbert-aws.pub ]; then
    echo "❌ SSH public key not found"
    exit 1
fi

SSH_PUBLIC_KEY=$(cat ~/.ssh/finbert-aws.pub)
echo "📋 Public key found: ${SSH_PUBLIC_KEY:0:50}..."

echo "🔄 This will restart your EC2 instance to add the SSH key"
read -p "Continue? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Stopping instance..."
    aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION
    aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID --region $REGION
    
    # Create user data to add SSH key
    cat > /tmp/add_ssh_key.sh << EOF
#!/bin/bash
echo "$SSH_PUBLIC_KEY" >> /home/ec2-user/.ssh/authorized_keys
chmod 600 /home/ec2-user/.ssh/authorized_keys
chown ec2-user:ec2-user /home/ec2-user/.ssh/authorized_keys
EOF
    
    echo "📝 Adding SSH key..."
    aws ec2 modify-instance-attribute \
        --instance-id $INSTANCE_ID \
        --user-data file:///tmp/add_ssh_key.sh \
        --region $REGION
    
    echo "▶️ Starting instance..."
    aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
    
    echo "⏳ Waiting for SSH service..."
    sleep 30
    
    echo "🧪 Testing SSH connection..."
    if ssh -i ~/.ssh/finbert-aws -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@3.7.194.20 "echo 'SSH setup successful!'"; then
        echo "✅ SSH is now working!"
    else
        echo "❌ SSH still not working, use Session Manager instead"
    fi
else
    echo "ℹ️  Use Session Manager instead: aws ssm start-session --target $INSTANCE_ID --region $REGION"
fi