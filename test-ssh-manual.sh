#!/bin/bash

# Manual SSH Connection Test
echo "🔍 SSH Connection Test for FinBERT Infrastructure"
echo "================================================"

IP="3.7.194.20"
echo "Target IP: $IP"
echo ""

echo "📋 Step-by-step SSH connection test:"
echo ""

echo "1. Check if SSH key file exists:"
if [ -f "finbert-rag-key-new.pem" ]; then
    echo "   ✅ finbert-rag-key-new.pem found"
    echo "   📝 File permissions: $(ls -la finbert-rag-key-new.pem)"
    KEY_FILE="finbert-rag-key-new.pem"
elif [ -f "~/.ssh/finbert-rag-key-new.pem" ]; then
    echo "   ✅ finbert-rag-key-new.pem found in ~/.ssh/"
    KEY_FILE="~/.ssh/finbert-rag-key-new.pem"
else
    echo "   ❌ SSH key file not found"
    echo ""
    echo "   🔧 To get the SSH key:"
    echo "   - Check if the infrastructure workflow completed successfully"
    echo "   - Look for the key in the workflow logs"
    echo "   - Or create a new key pair in AWS console"
    echo ""
    exit 1
fi

echo ""
echo "2. Fix key permissions (if needed):"
chmod 600 "$KEY_FILE"
echo "   ✅ Key permissions set to 600"

echo ""
echo "3. Test basic connectivity:"
echo "   Testing port 22 accessibility..."
if timeout 5 bash -c "</dev/tcp/$IP/22" 2>/dev/null; then
    echo "   ✅ Port 22 is accessible"
else
    echo "   ❌ Port 22 not accessible"
    echo "   This might mean:"
    echo "   - Instance is not running"
    echo "   - Security group blocks SSH"
    echo "   - Workflow still in progress"
    echo ""
fi

echo ""
echo "4. 🔗 SSH Connection Commands:"
echo ""
echo "Basic SSH (interactive):"
echo "ssh -i $KEY_FILE ec2-user@$IP"
echo ""
echo "SSH with options (recommended):"
echo "ssh -i $KEY_FILE -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@$IP"
echo ""
echo "Test SSH (quick check):"
echo "ssh -i $KEY_FILE -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$IP 'echo \"SSH Success!\" && whoami && uptime'"
echo ""

echo "📋 Troubleshooting:"
echo "- If 'Permission denied': Check key file and permissions"
echo "- If 'Connection refused': Instance may not be running"
echo "- If 'Connection timed out': Check security group or instance status"
echo "- If 'Host key verification failed': Use -o StrictHostKeyChecking=no"
echo ""

echo "🔍 Check infrastructure status:"
echo "Go to: https://github.com/pes-mtech-project/RAG_API_UI/actions"