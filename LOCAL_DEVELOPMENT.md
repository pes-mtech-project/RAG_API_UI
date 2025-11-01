# Local Development Deployment Guide

## GitHub Actions Limit Solution

Your GitHub Actions free tier is exhausted. Here are your options:

### 🚀 **Immediate Solution: Local CI Pipeline** (Recommended)

Use the custom local deployment scripts that replace GitHub Actions functionality:

#### Option 1: Quick Development Cycle
```bash
./scripts/quick-dev-deploy.sh
```
- Fast iteration for development
- Builds, tests, and optionally deploys
- Perfect for rapid code changes

#### Option 2: Full CI Pipeline
```bash
./scripts/local-ci-pipeline.sh
```
- Complete CI/CD functionality
- Code quality checks (when tools installed)
- Comprehensive testing and deployment

### 🔧 **AWS Configuration** (Optional)

To enable AWS deployment from local scripts:

1. Update `.env` file with your AWS credentials:
```bash
AWS_ACCOUNT_ID=your-aws-account-id-here
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your-aws-access-key-here
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key-here
```

2. Install AWS CLI:
```bash
brew install awscli
# or
pip install awscli
```

### 📋 **Other Solutions**

#### Self-Hosted GitHub Runner (Best long-term)
- **Unlimited minutes** on your own hardware
- Keep existing GitHub Actions workflows
- Setup guide: [GitHub Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)

#### Alternative CI/CD Platforms
- **GitLab CI/CD**: 400 minutes/month free
- **CircleCI**: 6,000 minutes/month free  
- **Travis CI**: Free for open source

### 🏭 **Production Deployment**

Production deployments (main branch) continue using GitHub Actions exactly as before:
- No changes needed
- Same workflow and process
- Uses existing GitHub Actions credits efficiently

### 🧪 **Development Workflow**

```bash
# 1. Make code changes
# 2. Test locally
./scripts/quick-dev-deploy.sh

# 3. Choose deployment target:
# - Local only (skip AWS)
# - AWS development environment (requires AWS config)

# 4. Production deployment (when ready)
# - Merge to main branch
# - GitHub Actions handles production deployment automatically
```

### 📊 **Status**

✅ Local development pipeline ready  
✅ Production workflow preserved  
✅ Code quality checks integrated  
✅ Health checks and testing included  
🔧 AWS deployment (configure as needed)  

Your development workflow is now independent of GitHub Actions limits while maintaining the same production deployment process.