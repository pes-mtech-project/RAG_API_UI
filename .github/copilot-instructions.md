# FinBERT News RAG App — Copilot Instructions

## Project Overview
This is a multi-service, containerized RAG (Retrieval-Augmented Generation) system for financial news, built with FastAPI (API), Streamlit (UI), and deployed via AWS ECS Fargate. CI/CD is automated using GitHub Actions, with images stored in GitHub Container Registry (GHCR).

## Architecture & Service Boundaries
- **API**: FastAPI app (`api/`), exposes REST endpoints, containerized via `docker/Dockerfile.api`
- **UI**: Streamlit app (`streamlit/`), containerized via `docker/Dockerfile.ui`
- **Infrastructure**: AWS CDK (TypeScript, `infrastructure/`), manages ECS clusters, ALB, scaling, networking
- **Data Layer**: Elasticsearch (GCP Cloud, external), accessed via API
- **Base Images**: Pre-built ML dependencies in `docker/Dockerfile.base` for faster builds
- **Deployment**: Docker Compose for local/dev, ECS Fargate for prod/dev environments

## Developer Workflows
- **Local Development**:
	- Start all services: `docker-compose up --build`
	- API only: `cd api && uvicorn main:app --reload`
	- UI only: `cd streamlit && streamlit run app.py`
	- Separate UI for dev: `./archive/run-ui-separately.sh [API_HOST] [API_PORT]`
- **Build & Deploy**:
	- Build API container: `./scripts/build.sh latest` (UI builds locally only)
	- Deploy local: `./scripts/deploy-local.sh`
	- ECS/CDK deploy: `cd infrastructure && npm run deploy:dev|prod`
- **Release Management**:
	- Prepare release: `./scripts/release-manager.sh prepare`
	- Create release: `./scripts/release-manager.sh release patch|minor|major`
	- Check status: `./scripts/release-manager.sh status|deployment`
- **Diagnostics & Maintenance**:
	- Dev instance: `./archive/diagnose-dev-instance.sh`, `./archive/restart-dev-instance.sh`
	- Prod instance: `./archive/diagnose-instance.sh`, `./archive/restart-instance.sh`
	- SSH test: `./archive/test-ssh-dev.sh` or `./archive/test-ssh.sh`
	- Monitor deployments: `./monitor-deployment.sh`, `./monitor-workflow.sh`

## CI/CD & Branching
- **Production**: `main` branch → API-only deploy to prod ECS (UI builds locally)
- **Development**: `develop` branch → API deploy to dev ECS, UI runs locally
- **Feature/Hotfix**: PRs to `develop` or `main` as per urgency
- **Container tags**: `latest` (prod), `develop` (dev)

## Conventions & Patterns
- **Docker**: Multi-stage builds, health checks, non-root users
- **Python**: PEP 8, type hints, clear docstrings
- **Infrastructure**: All CDK stacks parameterized by environment (`dev`/`prod`)
- **Environment Variables**: Set via `.env` and CDK, e.g. `API_PORT`, `ENVIRONMENT`, `API_HOST`
- **Monitoring**: CloudWatch logs, `/health` endpoint for ALB health checks

## Integration Points
- **Elasticsearch**: API connects to GCP-hosted Elasticsearch, credentials via `.env`
- **GHCR**: API container images pushed/pulled from GitHub Container Registry  
- **AWS**: ECS, ALB, CloudWatch, IAM, VPC, Security Groups managed via CDK
- **Route53**: Automated DNS management for custom domains (`news-rag.lauki.co`, `news-rag-dev.lauki.co`)

## Key Files & Directories
- `api/`, `streamlit/`: Service source code
- `docker/`: Dockerfiles for all containers (includes base image for ML dependencies)
- `infrastructure/`: AWS CDK code, deployment scripts
- `archive/`: Diagnostic and maintenance scripts
- `scripts/`: Build/deploy scripts, release management, DNS management
- `.env.example`: Environment variable template
- `PRODUCTION_DEPLOYMENT.md`: Comprehensive deployment guide
- `DNS_MANAGEMENT.md`: Route53 DNS configuration and automation guide

## Example: Health Check Pattern
All containers expose `/health` endpoint for ALB/ECS health checks. See `main.py` (API) and `app.py` (UI) for implementation.

## Example: Automated Deployment
On push to `main` or `develop`, GitHub Actions build containers, push to GHCR, trigger ECS/CDK deployment, and automatically update Route53 DNS records. See workflow logs for status.

## Example: DNS Management Pattern
DNS records are automatically updated after successful deployments:
```bash
# Manual DNS update
./scripts/update-dns-record.sh dev new-alb-123.ap-south-1.elb.amazonaws.com

# Check DNS status
dig +short news-rag-dev.lauki.co CNAME
curl http://news-rag-dev.lauki.co/health
```

## Example: Release Management Pattern
The release process uses semantic versioning with automated GitHub releases:
```bash
# Prepare branch for release
./scripts/release-manager.sh prepare

# Create versioned release (creates git tag, GitHub release, triggers deployment)
./scripts/release-manager.sh release patch  # v1.2.3 -> v1.2.4
```

## Troubleshooting
- Use diagnostic scripts in `archive/` for instance/container issues
- Check CloudWatch logs for ECS task/container failures
- Use `npm run diff` in `infrastructure/` to view pending CDK changes

---
**For unclear or missing patterns, ask the user for clarification.**

