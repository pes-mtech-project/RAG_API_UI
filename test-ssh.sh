echo "Testing SSH connection..."
ssh -i ~/.ssh/finbert-aws -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@3.7.194.20 "echo \"SSH connection successful! Ready for deployment.\"" 
