#!/bin/bash

# 🚀 FinBERT RAG Release Management Script
# Automates version management and production releases

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/pes-mtech-project/RAG_API_UI"
MAIN_BRANCH="main"
DEVELOP_BRANCH="develop"

# Functions
print_header() {
    echo -e "${BLUE}=================================="
    echo -e "🚀 FinBERT RAG Release Manager"
    echo -e "==================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if we're in a git repository
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        print_error "Not in a git repository!"
        exit 1
    fi
    
    # Check if we have GitHub CLI
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is required but not installed"
        print_info "Install it from: https://cli.github.com/"
        exit 1
    fi
    
    # Check if logged into GitHub CLI
    if ! gh auth status >/dev/null 2>&1; then
        print_error "Not logged into GitHub CLI"
        print_info "Run: gh auth login"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

get_current_version() {
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    echo "${last_tag#v}"  # Remove 'v' prefix
}

increment_version() {
    local version=$1
    local type=$2
    
    IFS='.' read -ra PARTS <<< "$version"
    local major=${PARTS[0]:-0}
    local minor=${PARTS[1]:-0}
    local patch=${PARTS[2]:-0}
    
    case $type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid version type: $type"
            exit 1
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

validate_version() {
    local version=$1
    if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format: $version (expected: X.Y.Z)"
        return 1
    fi
    return 0
}

show_status() {
    print_info "Repository Status:"
    echo ""
    
    local current_branch=$(git branch --show-current)
    local current_version=$(get_current_version)
    local uncommitted_changes=$(git status --porcelain | wc -l)
    
    echo "📂 Current Branch: $current_branch"
    echo "🏷️  Latest Version: v$current_version"
    echo "📝 Uncommitted Changes: $uncommitted_changes"
    
    if [[ $uncommitted_changes -gt 0 ]]; then
        print_warning "You have uncommitted changes!"
        git status --short
        echo ""
    fi
    
    # Show recent commits
    print_info "Recent commits:"
    git log --oneline -5
    echo ""
}

create_release() {
    local version_type=$1
    local custom_version=$2
    
    print_info "Starting release process..."
    
    # Get current version and calculate new version
    local current_version=$(get_current_version)
    local new_version
    
    if [[ -n "$custom_version" ]]; then
        new_version="$custom_version"
    else
        new_version=$(increment_version "$current_version" "$version_type")
    fi
    
    if ! validate_version "$new_version"; then
        exit 1
    fi
    
    local new_tag="v$new_version"
    
    print_info "Version bump: v$current_version → $new_tag"
    
    # Confirm with user
    echo ""
    print_warning "This will:"
    echo "  1. Switch to main branch"
    echo "  2. Pull latest changes"
    echo "  3. Trigger production deployment workflow with version: $new_tag"
    echo "  4. Create GitHub release"
    echo ""
    
    read -p "🤔 Continue with release? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Release cancelled"
        exit 0
    fi
    
    # Switch to main branch and pull latest
    print_info "Switching to main branch..."
    git checkout "$MAIN_BRANCH"
    git pull origin "$MAIN_BRANCH"
    
    # Trigger release workflow via GitHub CLI
    print_info "Triggering production release workflow..."
    
    gh workflow run "production-release.yml" \
        -f version="$new_version" \
        -f environment="prod" \
        -f force_deploy="true"
    
    print_success "Release workflow triggered!"
    print_info "Monitor progress at: $REPO_URL/actions"
    
    # Wait a moment and show workflow status
    sleep 3
    print_info "Latest workflow runs:"
    gh run list --workflow="production-release.yml" --limit=3
}

prepare_for_main() {
    print_info "Preparing branch for main merge..."
    
    local current_branch=$(git branch --show-current)
    
    if [[ "$current_branch" == "$MAIN_BRANCH" ]]; then
        print_error "Already on main branch"
        exit 1
    fi
    
    # Check if we're on develop or feature branch
    print_info "Current branch: $current_branch"
    
    # Run quality checks
    print_info "Running pre-merge checks..."
    
    # Check if we have any uncommitted changes
    if [[ $(git status --porcelain | wc -l) -gt 0 ]]; then
        print_warning "You have uncommitted changes. Please commit or stash them first."
        return 1
    fi
    
    # Push current branch
    print_info "Pushing current branch..."
    git push origin "$current_branch"
    
    print_success "Branch prepared for merge to main"
    print_info "Next steps:"
    echo "  1. Create PR: $current_branch → $MAIN_BRANCH"
    echo "  2. Review and merge PR"
    echo "  3. Run: $0 release [patch|minor|major]"
}

show_deployment_status() {
    print_info "Current Deployment Status:"
    echo ""
    
    # Show latest releases
    print_info "Latest releases:"
    gh release list --limit=5
    
    echo ""
    
    # Show workflow runs
    print_info "Recent workflow runs:"
    gh run list --limit=5
    
    echo ""
    
    # Show container images
    print_info "Latest container images:"
    echo "📦 API: ghcr.io/pes-mtech-project/finbert-news-rag-app/finbert-api"
}

show_help() {
    print_header
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  status                    Show repository and deployment status"
    echo "  prepare                   Prepare current branch for main merge"
    echo "  release <type> [version]  Create a new release"
    echo "                           Types: patch, minor, major"
    echo "                           Version: custom version (e.g., 1.2.3)"
    echo "  deployment               Show deployment status"
    echo "  help                     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 prepare"
    echo "  $0 release patch"
    echo "  $0 release minor"
    echo "  $0 release major"
    echo "  $0 release custom 2.1.0"
    echo "  $0 deployment"
    echo ""
    echo "Workflow:"
    echo "  1. Develop features on feature/develop branches"
    echo "  2. Run '$0 prepare' to prepare for main merge"
    echo "  3. Create and merge PR to main"
    echo "  4. Run '$0 release patch/minor/major' to deploy to production"
}

main() {
    local command=${1:-help}
    
    case $command in
        status)
            print_header
            check_prerequisites
            show_status
            ;;
        prepare)
            print_header
            check_prerequisites
            prepare_for_main
            ;;
        release)
            local version_type=${2:-patch}
            local custom_version=""
            
            if [[ "$version_type" == "custom" ]]; then
                custom_version="$3"
                if [[ -z "$custom_version" ]]; then
                    print_error "Custom version required when using 'custom' type"
                    exit 1
                fi
            fi
            
            print_header
            check_prerequisites
            create_release "$version_type" "$custom_version"
            ;;
        deployment)
            print_header
            check_prerequisites
            show_deployment_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"