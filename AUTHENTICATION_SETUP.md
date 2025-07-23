# GitHub Authentication Setup Guide

## Issue
GitHub removed password authentication on August 13, 2021. You need to use Personal Access Tokens (PAT) instead.

## Solution: Personal Access Token (PAT)

### Step 1: Generate Personal Access Token
1. Go to GitHub.com and log in
2. Click your profile picture → Settings
3. Scroll down to "Developer settings" → "Personal access tokens"
4. Click "Tokens (classic)" → "Generate new token (classic)"
5. Give it a descriptive name (e.g., "Local Development")
6. Set expiration (recommend 90 days or 1 year)
7. Select scopes:
   - ✅ **repo** (Full control of private repositories)
   - ✅ **workflow** (Update GitHub Action workflows)
   - ✅ **write:packages** (Upload packages to GitHub Package Registry)
8. Click "Generate token"
9. **Important**: Copy the token immediately - you won't see it again!

### Step 2: Configure Git to Use PAT
After generating your token, you have two options:

#### Option A: Use Git Credential Manager (Recommended)
```bash
git config --global credential.helper manager-core
# Next time you push, you'll be prompted for username and password
# Use your GitHub username and the PAT as password
```

#### Option B: Store in .env file
1. Copy `.env.example` to `.env`
2. Add your actual token to `.env`
3. Use the token when prompted for password

### Step 3: Test Authentication
```bash
# Test with a simple push
git push origin main
# When prompted for password, use your PAT
```

### Step 4: Update Both Repositories
Both repositories need to be configured:

1. **Main workspace**: `/project/sandbox/user-workspace`
2. **ERPNext Aramex**: `/project/sandbox/user-workspace/erpnext_aramex_shipping`

## Troubleshooting

### If push still fails:
1. Check if token has correct scopes
2. Verify token hasn't expired
3. Try clearing git credentials:
   ```bash
   git credential-manager reject https://github.com
   ```

### Security Best Practices:
- Never commit tokens to version control
- Use environment variables for sensitive data
- Rotate tokens regularly
- Use different tokens for different projects

## Quick Commands
```bash
# Check current remote URLs
git remote -v

# Update remote to use token (if needed)
git remote set-url origin https://YOUR_TOKEN@github.com/username/repo.git

# Test authentication
git push origin main
