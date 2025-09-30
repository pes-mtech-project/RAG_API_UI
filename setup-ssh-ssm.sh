#!/bin/bash

# Alternative SSH Key Setup using AWS Systems Manager
# This method doesn't require stopping the instance

echo "🔑 Setting up SSH access via AWS Systems Manager..."

INSTANCE_ID="i-05cf3774f0646b47d"
REGION="ap-south-1"

# Read the public key
SSH_PUBLIC_KEY=$(cat ~/.ssh/finbert-aws.pub)

# Create a temporary script to add the SSH key
cat > /tmp/add-ssh-key.sh << EOF
#!/bin/bash
# Add SSH public key to authorized_keys
mkdir -p /home/ec2-user/.ssh
echo "$SSH_PUBLIC_KEY" >> /home/ec2-user/.ssh/authorized_keys
chmod 700 /home/ec2-user/.ssh
chmod 600 /home/ec2-user/.ssh/authorized_keys
chown -R ec2-user:ec2-user /home/ec2-user/.ssh
echo "SSH key added successfully"
EOF

# Try to use Systems Manager to run the command
echo "Attempting to add SSH key via Systems Manager..."
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["mkdir -p /home/ec2-user/.ssh","echo \"'$SSH_PUBLIC_KEY'\" >> /home/ec2-user/.ssh/authorized_keys","chmod 700 /home/ec2-user/.ssh","chmod 600 /home/ec2-user/.ssh/authorized_keys","chown -R ec2-user:ec2-user /home/ec2-user/.ssh","echo \"SSH key added successfully\""]' \
    --region "$REGION" \
    --output text

if [ $? -eq 0 ]; then
    echo "✅ SSH key setup command sent successfully"
    echo "⏳ Waiting 30 seconds for execution..."
    sleep 30
    echo "🧪 Testing SSH connection..."
    ssh -i ~/.ssh/finbert-aws -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@3.7.194.20 "echo 'SSH connection successful!'"
else
    echo "❌ Systems Manager approach failed, trying alternative method..."
    echo "Please run the GitHub workflow 'Add SSH Key to EC2' manually"
fi