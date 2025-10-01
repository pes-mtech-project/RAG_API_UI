#!/bin/bash
# Development instance user data script

# Log all output for debugging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "$(date): Starting development instance setup"

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install other utilities
yum install -y git curl wget python3 python3-pip

# Create development directory
mkdir -p /home/ec2-user/finbert-dev
chown -R ec2-user:ec2-user /home/ec2-user/

# Configure environment for development
cat > /home/ec2-user/.bashrc << 'EOF'
# Development environment settings
export ENVIRONMENT=development
export BRANCH=develop
export API_PORT=8010
export UI_PORT=8511
export PATH=$PATH:/usr/local/bin

# Aliases for development
alias dev-logs='docker-compose -f docker-compose.dev.yml logs -f'
alias dev-ps='docker-compose -f docker-compose.dev.yml ps'
alias dev-restart='docker-compose -f docker-compose.dev.yml restart'
alias dev-stop='docker-compose -f docker-compose.dev.yml down'
alias dev-start='docker-compose -f docker-compose.dev.yml up -d'

echo "🚧 Development environment ready"
echo "📍 API: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8010"
echo "📍 UI:  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8511"
EOF

echo "$(date): Development instance setup completed"