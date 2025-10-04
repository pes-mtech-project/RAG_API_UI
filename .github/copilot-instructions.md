# FinBERT News RAG App — Copilot Instructions

## Project Overview
This is a **modular, production-ready** RAG (Retrieval-Augmented Generation) system for financial news, built with **SOLID principles**. Features multi-dimensional embedding search, persistent model caching, and comprehensive performance optimization. Deployed via AWS ECS Fargate with automated CI/CD.

## **🏗️ Enhanced Modular Architecture** 
- **API**: Modular FastAPI app (`api/app/`) with service layer, multiple embedding endpoints, model caching
- **Entry Point**: `startup.py` with model preloading (not `main.py`)
- **Service Layer**: ElasticsearchService, EmbeddingService, SearchService, ModelPreloader
- **Routers**: search.py (new endpoints), legacy.py (backward compatibility)
- **Models**: Pydantic schemas for request/response validation
- **UI**: Enhanced Streamlit app (`streamlit/`) with multi-endpoint support
- **Infrastructure**: AWS CDK (TypeScript, `infrastructure/`) for ECS clusters, ALB, scaling
- **Data Layer**: Elasticsearch (GCP Cloud) with k-NN vector search (8.x optimized)
- **Deployment**: Docker Compose for local/dev, ECS Fargate for prod/dev environments

## **🚀 NEW: Multi-Dimensional Embedding Endpoints**
- **`/search/cosine/embedding384d/`**: Fast search (all-MiniLM-L6-v2, 384d)
- **`/search/cosine/embedding768d/`**: Balanced search (all-mpnet-base-v2, 768d) 
- **`/search/cosine/embedding1155d/`**: Enhanced search (384d+768d+3d sentiment)
- **`/health`**: System status with model cache information

## **🔧 Enhanced Developer Workflows**
- **Local Development** (With Model Caching):
	- Start optimized services: `docker-compose up --build` 
	- API only (modular): `cd api && python startup.py` (NOT `uvicorn main:app`)
	- UI only: `cd streamlit && streamlit run app.py`
	- Test new endpoints: `curl -X POST http://localhost:8000/search/cosine/embedding384d/`
- **Performance Testing**:
	- Exhaustive test suite: `python test_exhaustive_api.py` (138 requests)
	- Model caching validation: `python test_model_caching.py`
	- Load testing: Multiple concurrent curl requests
- **Build & Deploy**:
	- Build containers: `./scripts/build.sh latest`
	- Deploy local: `./scripts/deploy-local.sh`
	- ECS/CDK deploy: `cd infrastructure && npm run deploy:dev|prod`
- **Diagnostics & Maintenance**:
	- Dev instance: `./archive/diagnose-dev-instance.sh`, `./archive/restart-dev-instance.sh`
	- Prod instance: `./archive/diagnose-instance.sh`, `./archive/restart-instance.sh`
	- Model cache check: `docker exec finbert-api ls ~/.cache/sentence_transformers/`

## CI/CD & Branching
- **Production**: `main` branch → full stack deploy to prod ECS
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
- **GHCR**: All container images pushed/pulled from GitHub Container Registry
- **AWS**: ECS, ALB, CloudWatch, IAM, VPC, Security Groups managed via CDK

## **📁 Enhanced File Structure**
- `api/app/`: Modular FastAPI application
  - `startup.py`: Application entry point with model preloading
  - `main.py`: FastAPI factory function
  - `services/`: Service layer (ElasticsearchService, EmbeddingService, SearchService)
  - `routers/`: API endpoints (search.py, legacy.py)  
  - `models/`: Pydantic request/response schemas
- `streamlit/`: Enhanced UI with multi-endpoint support
- `docker/`: Dockerfiles for all containers
- `tests/`: Comprehensive testing suite
  - `test_exhaustive_api.py`: 138-request performance validation
  - `test_model_caching.py`: Model caching verification
- `infrastructure/`: AWS CDK deployment code
- `PERFORMANCE_REPORT.md`: Detailed performance analysis
- `.env.example`: Environment template with model cache paths

## **🎯 Performance Standards**
- **Response Time Target**: < 0.5s average across all endpoints
- **Success Rate**: 100% under normal load
- **Model Caching**: No downloads after initial load (4.9x speedup achieved)
- **Concurrent Load**: > 4 requests/second sustained throughput

## **🔍 Debugging Patterns**
- **Model Download Issues**: Check `~/.cache/sentence_transformers/` persistence
- **Performance Issues**: Use `time curl` for response time validation
- **Service Issues**: Check `docker logs finbert-api` for startup errors
- **Health Checks**: `/health` endpoint shows system status and model cache info

## **🚀 Recent Major Changes (October 2025)**
- **BREAKING**: Entry point changed from `main.py` to `startup.py`
- **NEW**: Three embedding endpoints (384d, 768d, 1155d dimensions)
- **PERFORMANCE**: Persistent model caching eliminates downloads
- **ARCHITECTURE**: Complete modular refactor following SOLID principles
- **TESTING**: Comprehensive 138-request validation suite implemented

---
**For unclear or missing patterns, ask the user for clarification.**

# Workspace Rules (retain for agent compliance)
- Work through each checklist item systematically.
- Keep communication concise and focused.
- Follow development best practices.
<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->
- [x] Verify that the copilot-instructions.md file in the .github directory is created.

- [x] Clarify Project Requirements
	<!-- Project: FinBERT News RAG with Docker containers, GitHub Container Registry, CI/CD to AWS EC2 -->

- [x] Scaffold the Project
	<!--
	Created Docker containerization structure with:
	- Multi-service Docker Compose setup
	- Dockerfiles for API and UI services
	- GitHub Actions workflows for container registry
	- Deployment automation to AWS EC2
	-->

- [x] Customize the Project
	<!--
	Created comprehensive Docker containerization setup:
	- Multi-service architecture with API and UI containers
	- GitHub Container Registry integration (ghcr.io)
	- Automated CI/CD pipeline for AWS EC2 deployment
	- Production and development Docker Compose configurations
	- Container build and deployment scripts
	- Health checks and monitoring capabilities
	-->

- [x] Install Required Extensions
	<!-- No specific extensions required for container setup. Docker and YAML support already available. -->

- [x] Compile the Project
	<!--
	Verified that all previous steps have been completed.
	Install any missing dependencies.
	Run diagnostics and resolve any issues.
	Check for markdown files in project folder for relevant instructions on how to do this.
	-->

- [x] Create and Run Task
	<!--
	Verify that all previous steps have been completed.
	Check https://code.visualstudio.com/docs/debugtest/tasks to determine if the project needs a task. If so, use the create_and_run_task to create and launch a task based on package.json, README.md, and project structure.
	Skip this step otherwise.
	 -->

- [x] Launch the Project
	<!--
	Verify that all previous steps have been completed.
	Prompt user for debug mode, launch only if confirmed.
	 -->

- [x] Ensure Documentation is Complete
	<!--
	Verify that all previous steps have been completed.
	Verify that README.md and the copilot-instructions.md file in the .github directory exists and contains current project information.
	Clean up the copilot-instructions.md file in the .github directory by removing all HTML comments.
	 -->

<!--
## Execution Guidelines
PROGRESS TRACKING:
- If any tools are available to manage the above todo list, use it to track progress through this checklist.
- After completing each step, mark it complete and add a summary.
- Read current todo list status before starting each new step.

COMMUNICATION RULES:
- Avoid verbose explanations or printing full command outputs.
- If a step is skipped, state that briefly (e.g. "No extensions needed").
- Do not explain project structure unless asked.
- Keep explanations concise and focused.

DEVELOPMENT RULES:
- Use '.' as the working directory unless user specifies otherwise.
- Avoid adding media or external links unless explicitly requested.
- Use placeholders only with a note that they should be replaced.
- Use VS Code API tool only for VS Code extension projects.
- Once the project is created, it is already opened in Visual Studio Code—do not suggest commands to open this project in Visual Studio again.
- If the project setup information has additional rules, follow them strictly.

FOLDER CREATION RULES:
- Always use the current directory as the project root.
- If you are running any terminal commands, use the '.' argument to ensure that the current working directory is used ALWAYS.
- Do not create a new folder unless the user explicitly requests it besides a .vscode folder for a tasks.json file.
- If any of the scaffolding commands mention that the folder name is not correct, let the user know to create a new folder with the correct name and then reopen it again in vscode.

EXTENSION INSTALLATION RULES:
- Only install extension specified by the get_project_setup_info tool. DO NOT INSTALL any other extensions.

PROJECT CONTENT RULES:
- If the user has not specified project details, assume they want a "Hello World" project as a starting point.
- Avoid adding links of any type (URLs, files, folders, etc.) or integrations that are not explicitly required.
- Avoid generating images, videos, or any other media files unless explicitly requested.
- If you need to use any media assets as placeholders, let the user know that these are placeholders and should be replaced with the actual assets later.
- Ensure all generated components serve a clear purpose within the user's requested workflow.
- If a feature is assumed but not confirmed, prompt the user for clarification before including it.
- If you are working on a VS Code extension, use the VS Code API tool with a query to find relevant VS Code API references and samples related to that query.

TASK COMPLETION RULES:
- Your task is complete when:
  - Project is successfully scaffolded and compiled without errors
  - copilot-instructions.md file in the .github directory exists in the project
  - README.md file exists and is up to date
  - User is provided with clear instructions to debug/launch the project

Before starting a new task in the above plan, update progress in the plan.
-->
- Work through each checklist item systematically.
- Keep communication concise and focused.
- Follow development best practices.