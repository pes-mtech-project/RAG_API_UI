# AWS ECS Infrastructure Setup

This directory contains AWS CDK infrastructure code for deploying the FinBERT RAG application to Amazon ECS with Fargate.

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Node.js 18+** and npm
3. **AWS CDK CLI** (`npm install -g aws-cdk`)
4. **GitHub Secrets** configured:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_ACCOUNT_ID`

## Quick Start

### 1. Install Dependencies
```bash
cd infrastructure
npm install
```

### 2. Bootstrap CDK (First Time Only)
```bash
npx cdk bootstrap
```

### 3. Deploy Development Environment
```bash
npm run deploy:dev
```

### 4. Deploy Production Environment
```bash
npm run deploy:prod
```

## Architecture

### Components Created
- **VPC** with public/private subnets across 2 AZs
- **ECS Cluster** (Fargate)
- **Application Load Balancer** with health checks
- **Auto Scaling** based on CPU and memory metrics
- **CloudWatch Logs** for monitoring
- **Security Groups** with minimal required access

### Environments

#### Development (`dev`)
- **Cluster**: `finbert-rag-dev-cluster`
- **Service**: `finbert-api-dev`
- **Scaling**: 1-2 tasks
- **CPU Threshold**: 70%
- **Memory Threshold**: 80%

#### Production (`prod`)
- **Cluster**: `finbert-rag-prod-cluster`
- **Service**: `finbert-api-prod`
- **Scaling**: 1-5 tasks
- **CPU Threshold**: 60%
- **Memory Threshold**: 70%

## Container Configuration

### Resource Allocation
- **CPU**: 512 CPU units (0.5 vCPU)
- **Memory**: 1024 MB (1 GB)
- **Platform**: Fargate Latest

### Environment Variables
- `API_HOST=0.0.0.0`
- `API_PORT=8000`
- `ENVIRONMENT=dev|prod`

## Networking

### Load Balancer
- **Type**: Application Load Balancer (ALB)
- **Scheme**: Internet-facing
- **Protocol**: HTTP (Port 80)
- **Health Check**: `/health` endpoint

### Security Groups
- **ALB**: Allows inbound HTTP (80) from anywhere
- **ECS Tasks**: Allows inbound traffic from ALB only

## Monitoring & Logging

### CloudWatch Logs
- **Log Group**: `/ecs/finbert-api-{env}`
- **Retention**: 
  - Development: 7 days
  - Production: 30 days

### Auto Scaling Metrics
- **CPU Utilization**: Target 60-70%
- **Memory Utilization**: Target 70-80%
- **Scale Out**: 2 minutes cooldown
- **Scale In**: 5 minutes cooldown

## Deployment Process

### Automated via GitHub Actions
1. **Build**: Container images built and pushed to GHCR
2. **Deploy**: CDK deploys/updates infrastructure
3. **Update**: ECS service updated with new container image
4. **Verify**: Health checks ensure successful deployment

### Manual Deployment
```bash
# Deploy development
npm run deploy:dev

# Deploy production  
npm run deploy:prod

# View differences
npm run diff

# Destroy environment (careful!)
npm run destroy:dev
npm run destroy:prod
```

## Outputs

After deployment, the following outputs are available:

- **Load Balancer DNS**: ALB endpoint for API access
- **API URL**: Complete HTTP URL for the API
- **Cluster Name**: ECS cluster identifier
- **Service Name**: ECS service identifier
- **VPC ID**: Created VPC identifier

## Cost Optimization

### Development
- **Tasks**: Minimum 1, maximum 2
- **Auto-scale down**: Aggressive scaling to reduce costs
- **Log retention**: 7 days only

### Production
- **Tasks**: Minimum 1, maximum 5
- **Auto-scale**: Conservative scaling for stability
- **Log retention**: 30 days for debugging

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Required**
   ```bash
   npx cdk bootstrap aws://ACCOUNT-ID/REGION
   ```

2. **Insufficient Permissions**
   - Ensure AWS credentials have ECS, EC2, IAM, CloudFormation permissions

3. **Container Image Not Found**
   - Verify GHCR image exists and is accessible
   - Check GitHub Actions build logs

4. **Health Check Failures**
   - Verify `/health` endpoint responds with 200
   - Check container logs in CloudWatch

### Useful Commands

```bash
# View stack resources
aws cloudformation list-stack-resources --stack-name FinBertRagDevStack

# Check ECS service status
aws ecs describe-services --cluster finbert-rag-dev-cluster --services finbert-api-dev

# View container logs
aws logs tail /ecs/finbert-api-dev --follow

# Force new deployment
aws ecs update-service --cluster CLUSTER --service SERVICE --force-new-deployment
```

## Security

### IAM Roles
- **Execution Role**: Minimal permissions for ECS task execution
- **Task Role**: Application-specific permissions (can be extended)

### Network Security
- **Private Subnets**: ECS tasks run in private subnets
- **NAT Gateway**: Provides controlled internet access
- **Security Groups**: Restricts traffic to required ports only

### Container Security
- **Read-only root filesystem**: Can be enabled
- **Non-root user**: Container should run as non-root
- **Secrets management**: Use AWS Secrets Manager for sensitive data