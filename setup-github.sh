#!/bin/bash
# Quick GitHub Setup Script for Mac/Linux

echo ""
echo "====================================="
echo "GitHub Setup for FileOrganizer Pro"
echo "====================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: Git not found. Install from: https://git-scm.com/download/linux"
    exit 1
fi

echo "[OK] Git found:"
git --version
echo ""

# Check if in correct directory
if [ ! -f "src/backend/api/main.py" ]; then
    echo "ERROR: Not in FileOrganizerPro directory"
    echo "Please run this script from the FileOrganizerPro root folder"
    exit 1
fi

echo "[OK] FileOrganizerPro directory detected"
echo ""

# Check git status
echo ""
echo "Checking git status..."
git status
echo ""

# Ask for GitHub username
read -p "Enter your GitHub username: " github_user
if [ -z "$github_user" ]; then
    echo "ERROR: GitHub username required"
    exit 1
fi

# Ask for repository name
read -p "Enter repository name (default: FileOrganizerPro): " repo_name
if [ -z "$repo_name" ]; then
    repo_name="FileOrganizerPro"
fi

echo ""
echo "====================================="
echo "Setup Information"
echo "====================================="
echo "GitHub User: $github_user"
echo "Repository: $repo_name"
echo "URL: https://github.com/$github_user/$repo_name"
echo ""
echo "Steps to complete:"
echo "1. Create repo on GitHub: https://github.com/new"
echo "2. Use name: $repo_name"
echo "3. Select: Public or Private"
echo "4. DO NOT initialize with files"
echo "5. Copy the commands GitHub shows"
echo "6. Come back and press Enter when ready"
echo ""
read -p "Press Enter to continue..."

# Initialize git
if [ ! -d ".git" ]; then
    echo ""
    echo "Initializing git repository..."
    git init
    git branch -M main
    echo "[OK] Git repository initialized"
else
    echo "[OK] Git repository already exists"
fi

echo ""
echo "Checking .gitignore..."
if [ -f ".gitignore" ]; then
    echo "[OK] .gitignore found"
else
    echo "Creating .gitignore..."
    cat > .gitignore << 'EOF'
.env
*.db
venv/
__pycache__/
.pytest_cache/
node_modules/
dist/
*.log
data/logs/
data/backups/
.DS_Store
EOF
    echo "[OK] .gitignore created"
fi

echo ""
echo "Adding files to git..."
git add .
echo "[OK] Files staged for commit"

echo ""
echo "Creating initial commit..."
git commit -m "Initial commit: FileOrganizer Pro v3.0 - Production-ready backend" -q
echo "[OK] Initial commit created"

echo ""
echo "====================================="
echo "Ready to Push to GitHub!"
echo "====================================="
echo ""
echo "Copy and paste these commands:"
echo ""
echo "git remote add origin https://github.com/$github_user/$repo_name.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
echo "Run these commands in this folder to push to GitHub."
echo ""
