# FinBERT News RAG App — Copilot Instructions

## Project Overview
This is a multi-service, containerized RAG (Retrieval-Augmented Generation) system for financial news, built with FastAPI (API), Streamlit (UI), and deployed via AWS ECS Fargate. CI/CD is automated using GitHub Actions, with images stored in GitHub Container Registry (GHCR).

## Architecture & Service Boundaries
- **API**: FastAPI app (`api/`), exposes REST endpoints, containerized via `docker/Dockerfile.api`.
- **UI**: Streamlit app (`streamlit/`), containerized via `docker/Dockerfile.ui`.
- **Infrastructure**: AWS CDK (TypeScript, `infrastructure/`), manages ECS clusters, ALB, scaling, networking.
- **Data Layer**: Elasticsearch (GCP Cloud, external), accessed via API.
- **Deployment**: Docker Compose for local/dev, ECS Fargate for prod/dev environments.

## Developer Workflows
- **Local Development**:
	- Start all services: `docker-compose up --build`
	- API only: `cd api && uvicorn main:app --reload`
	- UI only: `cd streamlit && streamlit run app.py`
	- Separate UI for dev: `./run-ui-separately.sh [API_HOST] [API_PORT]`
- **Build & Deploy**:
	- Build containers: `./scripts/build.sh latest`
	- Deploy local: `./scripts/deploy-local.sh`
	- ECS/CDK deploy: `cd infrastructure && npm run deploy:dev|prod`
- **Diagnostics & Maintenance**:
	- Dev instance: `./archive/diagnose-dev-instance.sh`, `./archive/restart-dev-instance.sh`
	- Prod instance: `./archive/diagnose-instance.sh`, `./archive/restart-instance.sh`
	- SSH test: `./archive/test-ssh-dev.sh` or `./archive/test-ssh.sh`

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

## Key Files & Directories
- `api/`, `streamlit/`: Service source code
- `docker/`: Dockerfiles for all containers
- `infrastructure/`: AWS CDK code, deployment scripts
- `archive/`: Diagnostic and maintenance scripts
- `scripts/`: Build/deploy scripts
- `.env.example`: Environment variable template

## Example: Health Check Pattern
All containers expose `/health` endpoint for ALB/ECS health checks. See `main.py` (API) and `app.py` (UI) for implementation.

## Example: Automated Deployment
On push to `main` or `develop`, GitHub Actions build containers, push to GHCR, and trigger ECS/CDK deployment. See workflow logs for status.

## Troubleshooting
- Use diagnostic scripts in `archive/` for instance/container issues
- Check CloudWatch logs for ECS task/container failures
- Use `npm run diff` in `infrastructure/` to view pending CDK changes

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