#!/bin/bash

# Quick script to update Elasticsearch credentials with proper API key
set -e

AWS_REGION="ap-south-1"
SECRET_NAME="finbert-rag/elasticsearch/credentials"

echo "🔐 Updating Elasticsearch credentials with correct API key"
echo "=========================================================="

echo "Current credentials in Secrets Manager:"
aws secretsmanager get-secret-value --secret-id "$SECRET_NAME" --region "$AWS_REGION" --query 'SecretString' --output text | jq '.'

echo
echo "I can see the 'key' field contains 'news_finbert_embeddings' which should be the actual API key."
echo

# Prompt for the correct API key
read -p "Enter the correct Elasticsearch API Key: " ES_KEY

if [ -z "$ES_KEY" ]; then
    echo "❌ API Key cannot be empty!"
    exit 1
fi

# Create the corrected JSON payload
SECRET_VALUE=$(jq -n \
    --arg host "https://my-elasticsearch-project-d21e57.es.us-central1.gcp.elastic.cloud" \
    --arg index "news_finbert_embeddings" \
    --arg key "$ES_KEY" \
    '{
        host: $host,
        index: $index,
        key: $key
    }')

echo "Updating AWS Secrets Manager with correct credentials..."

# Update the secret
aws secretsmanager update-secret \
    --secret-id "$SECRET_NAME" \
    --secret-string "$SECRET_VALUE" \
    --region "$AWS_REGION" > /dev/null

echo "✅ Credentials updated!"

echo "New credentials:"
aws secretsmanager get-secret-value --secret-id "$SECRET_NAME" --region "$AWS_REGION" --query 'SecretString' --output text | jq '.'

echo
echo "Now forcing ECS deployment to pick up the new credentials..."

# Force ECS deployment
aws ecs update-service \
    --cluster finbert-rag-prod-cluster \
    --service finbert-api-prod \
    --force-new-deployment \
    --region "$AWS_REGION" > /dev/null

echo "✅ ECS deployment initiated"
echo "⏳ Waiting for deployment to complete..."

# Wait for deployment
aws ecs wait services-stable \
    --cluster finbert-rag-prod-cluster \
    --services finbert-api-prod \
    --region "$AWS_REGION"

echo "✅ Deployment completed!"
echo
echo "Testing the service..."

# Test health endpoint
sleep 10
HEALTH_RESPONSE=$(curl -s "http://FinBer-FinBe-CK5al0msPiSr-619953726.ap-south-1.elb.amazonaws.com/health" --connect-timeout 10 --max-time 15)

echo "Health Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q '"elasticsearch":"accessible"'; then
    echo "🎉 Success! Elasticsearch connection is now accessible!"
elif echo "$HEALTH_RESPONSE" | grep -q '"elasticsearch":"red"'; then
    echo "⚠️ Elasticsearch still shows as 'red' - please verify the API key is correct"
else
    echo "ℹ️ Check the health response above for status"
fi