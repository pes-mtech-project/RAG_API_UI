# 🌐 Route53 DNS Management for FinBERT RAG

## Overview

The FinBERT RAG application now includes automated Route53 DNS management that provides:
- **Stable URLs**: Custom domain names that don't change with deployments
- **Automatic Updates**: DNS records automatically updated when ALB endpoints change
- **Environment Isolation**: Separate subdomains for development and production

## 🔧 DNS Configuration

### Domains
- **Development**: `news-rag-dev.lauki.co` → Development ECS deployment
- **Production**: `news-rag.lauki.co` → Production ECS deployment

### Route53 Setup
- **Hosted Zone**: `lauki.co` (ID: `Z0338885B3LPG5PPUGOI`)
- **Record Type**: CNAME records with 5-minute TTL
- **Management**: Automated via CDK and GitHub Actions workflows

## 🚀 How It Works

### 1. Initial DNS Record Creation
```bash
# Create the initial DNS record
./scripts/setup-route53-dns.sh

# Or create manually for development
./scripts/create-dns-record.sh
```

### 2. Automated DNS Updates
- **Development**: Updated via `.github/workflows/ecs-deployment.yml`
- **Production**: Updated via `.github/workflows/production-release.yml`
- **Script**: `./scripts/update-dns-record.sh`

### 3. CDK Infrastructure Integration
The CDK stack (`infrastructure/lib/finbert-rag-stack.ts`) includes Route53 configuration:
```typescript
// Route53 DNS Configuration
hostedZoneId: 'Z0338885B3LPG5PPUGOI',
hostedZoneName: 'lauki.co',
subdomainName: 'news-rag-dev', // or 'news-rag' for prod
```

## 📋 Manual DNS Management

### Update DNS Record Manually
```bash
# Update development DNS
./scripts/update-dns-record.sh dev <alb-dns-name>

# Update production DNS  
./scripts/update-dns-record.sh prod <alb-dns-name>

# Example
./scripts/update-dns-record.sh dev my-alb-123456789.ap-south-1.elb.amazonaws.com
```

### Check Current DNS Record
```bash
# Check development
dig +short news-rag-dev.lauki.co CNAME

# Check production  
dig +short news-rag.lauki.co CNAME

# Test connectivity
curl http://news-rag-dev.lauki.co/health
curl http://news-rag.lauki.co/health
```

### Verify DNS Propagation
```bash
# Check multiple DNS servers
nslookup news-rag-dev.lauki.co 8.8.8.8
nslookup news-rag-dev.lauki.co 1.1.1.1

# Check propagation status
dig @8.8.8.8 news-rag-dev.lauki.co CNAME
dig @1.1.1.1 news-rag-dev.lauki.co CNAME
```

## 🔄 Workflow Integration

### Development Workflow (ecs-deployment.yml)
1. **Detect Changes**: Only update DNS if infrastructure changes
2. **Deploy ECS**: Deploy to development ECS cluster
3. **Health Check**: Verify ALB is responding
4. **Update DNS**: Automatically update `news-rag-dev.lauki.co`
5. **Verify**: Test custom domain endpoint

### Production Workflow (production-release.yml)
1. **Version Management**: Create semantic version tags
2. **Build & Push**: Build and push production container
3. **Deploy ECS**: Deploy to production ECS cluster  
4. **Health Check**: Verify production ALB is responding
5. **Update DNS**: Automatically update `news-rag.lauki.co`
6. **Create Release**: Create GitHub release with deployment info

## 🛠️ Script Reference

### `./scripts/setup-route53-dns.sh`
- **Purpose**: Initial setup of Route53 DNS records
- **Features**: Zone detection, record creation, verification
- **Usage**: One-time setup or manual record creation

### `./scripts/update-dns-record.sh`
- **Purpose**: Update existing DNS records with new ALB endpoints
- **Features**: Change detection, automatic updates, verification
- **Usage**: Called by workflows or manual updates
- **Parameters**: 
  - `$1`: Environment (`dev` or `prod`)
  - `$2`: Target ALB DNS name

### DNS Update Flow
```bash
./scripts/update-dns-record.sh dev new-alb.ap-south-1.elb.amazonaws.com
```
1. 🔍 **Check Current**: Compare current DNS target with new target
2. ⏩ **Skip if Same**: Exit early if DNS already points to correct ALB
3. 🔧 **Update Record**: Create Route53 change batch and submit
4. ⏳ **Wait**: Wait for DNS propagation to complete
5. ✅ **Verify**: Confirm DNS resolves to new target
6. 🌐 **Test**: Optional HTTP connectivity test

## 🎯 Benefits

### For Developers
- **Stable URLs**: Bookmark and share consistent URLs
- **No Manual Updates**: DNS automatically updates with deployments
- **Environment Clarity**: Clear separation between dev and prod

### For Users  
- **Memorable URLs**: `news-rag.lauki.co` vs `long-alb-name.elb.amazonaws.com`
- **Always Current**: URLs always point to latest deployment
- **Fast Propagation**: 5-minute TTL for quick updates

### For Operations
- **Automated Management**: No manual DNS configuration needed
- **Health Verification**: Automatic health checks before DNS updates
- **Rollback Capability**: Easy to revert DNS to previous ALB if needed

## 🔧 Troubleshooting

### DNS Not Updating
```bash
# Check AWS permissions
aws route53 list-hosted-zones

# Verify hosted zone
aws route53 list-resource-record-sets --hosted-zone-id Z0338885B3LPG5PPUGOI

# Check recent changes
aws route53 list-resource-record-sets --hosted-zone-id Z0338885B3LPG5PPUGOI \
  --query "ResourceRecordSets[?Type=='CNAME']"
```

### DNS Propagation Issues
```bash
# Check TTL and wait
dig news-rag-dev.lauki.co CNAME +noall +answer

# Force DNS cache clear (macOS)
sudo dscacheutil -flushcache

# Check from different locations
curl -H "Host: news-rag-dev.lauki.co" http://1.2.3.4/health
```

### Workflow Failures
1. **Check AWS CLI**: Ensure workflow has Route53 permissions
2. **Verify Script**: Test `update-dns-record.sh` manually
3. **Check Outputs**: Verify CDK outputs contain ALB DNS name
4. **Review Logs**: Check GitHub Actions logs for DNS update step

## 🎉 Success Verification

After deployment, verify everything works:

```bash
# Test all endpoints
curl http://news-rag-dev.lauki.co/health     # Development
curl http://news-rag.lauki.co/health         # Production

# Check response format
curl -s http://news-rag-dev.lauki.co/health | jq .

# Verify API docs
open http://news-rag-dev.lauki.co/docs       # Development
open http://news-rag.lauki.co/docs           # Production
```

Expected health response:
```json
{
  "status": "healthy",
  "api": "operational", 
  "elasticsearch": "accessible",
  "timestamp": "2025-10-04T03:52:15.573525"
}
```

---

**🚀 Ready for deployment!** The DNS infrastructure is now fully automated and integrated with your CI/CD pipeline.