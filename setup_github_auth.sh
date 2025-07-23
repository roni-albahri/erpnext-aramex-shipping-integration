#!/bin/bash

# GitHub Authentication Setup Script
# This script helps configure Personal Access Token authentication

echo "=== GitHub Authentication Setup ==="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Function to configure git for a repository
configure_repo() {
    local repo_path=$1
    local repo_name=$2
    
    echo "Configuring $repo_name..."
    cd "$repo_path" || return
    
    # Show current remote
    echo "Current remote:"
    git remote -v
    
    # Configure credential helper
    git config credential.helper store
    
    echo "✅ $repo_name configured for PAT authentication"
    echo ""
}

# Configure both repositories
echo "📁 Configuring repositories for Personal Access Token authentication..."
echo ""

# Configure main workspace
configure_repo "/project/sandbox/user-workspace" "Main Workspace"

# Configure ERPNext Aramex Shipping
configure_repo "/project/sandbox/user-workspace/erpnext_aramex_shipping" "ERPNext Aramex Shipping"

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Generate a Personal Access Token from GitHub"
echo "   - Go to: https://github.com/settings/tokens"
echo "   - Create new token with 'repo' scope"
echo ""
echo "2. Test authentication by running:"
echo "   git push origin main"
echo "   - Use your GitHub username as username"
echo "   - Use your PAT as password"
echo ""
echo "3. For detailed instructions, see: AUTHENTICATION_SETUP.md"
