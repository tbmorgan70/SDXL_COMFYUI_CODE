# 🔀 Git Workflow Guide

**Last Updated:** March 1, 2026  
**Purpose:** Comprehensive guide for maintaining Git workflow and repository sync

---

## 🚀 Quick Reference

### Essential Daily Commands
```powershell
# Start your session
git pull origin main

# Check what's changed
git status
git diff

# Save your work
git add .
git commit -m "Descriptive message"
git push origin main
```

---

## 📋 Daily Workflow Best Practices

### 1. **Start Each Session with Pull**
```powershell
git pull origin main
```
**Why:** Ensures you have the latest changes and prevents conflicts later.  
**When:** Every time you start working, even if you think nothing changed.

### 2. **Make Small, Frequent Commits**
Don't wait until the end of the day. Commit after completing logical units of work:

```powershell
# After completing a feature or fixing a bug
git add .
git commit -m "Add color validation to image sorter"
git push origin main
```

**Best Practice:** Commit early and often. Each commit should represent one logical change.

### 3. **Use Descriptive Commit Messages**

#### ✅ Good Examples:
- `"Fix bug in text file sorter when handling empty directories"`
- `"Add new HTML builder for retro sci-fi prompts"`
- `"Update sorter README with v2.4 features"`
- `"Consolidate duplicate modular_builder structure"`

#### ❌ Avoid:
- `"fixes"`
- `"updates"`
- `"changes"`
- `"stuff"`

#### Format Guidelines:
- Start with a verb (Add, Fix, Update, Remove, Refactor)
- Be specific about what changed
- Keep under 72 characters for the first line
- Add details in subsequent lines if needed

### 4. **Push Regularly**
- Push at least once per work session
- Push after significant changes
- Push before switching machines or taking breaks

---

## 🔄 Recommended Daily Pattern

```powershell
# ===== Morning Routine =====
git pull origin main

# ===== Work on Your Code =====
# Make changes, test features, etc.

# ===== After Completing a Logical Unit =====
git add .
git status              # Review what you're committing
git commit -m "Descriptive message about what changed"
git push origin main

# ===== Repeat add/commit/push cycle as needed =====
```

---

## 🛠️ Common Scenarios & Solutions

### Scenario 1: Forgot to Pull First
**Problem:** You get a "non-fast-forward" error when pushing.

**Solution:**
```powershell
git pull origin main    # Merge remote changes
git push origin main    # Now push your changes
```

### Scenario 2: Have Uncommitted Changes, Need to Pull
**Problem:** You have local changes but need to pull updates.

**Solution:**
```powershell
git stash               # Temporarily save your changes
git pull origin main    # Get remote changes
git stash pop          # Restore your changes
```

### Scenario 3: Want to See What Changed Before Committing
```powershell
git status             # List changed files
git diff              # See exact changes in files
git diff filename.py   # See changes in specific file
```

### Scenario 4: Made a Mistake in Last Commit Message
```powershell
git commit --amend -m "Corrected commit message"
git push --force origin main  # Use with caution!
```

### Scenario 5: Want to Undo Uncommitted Changes
```powershell
# Undo changes to specific file
git checkout -- filename.py

# Undo all uncommitted changes
git reset --hard HEAD
```

---

## 📊 Checking Repository Status

### View Current State
```powershell
# See modified, staged, and untracked files
git status

# See branch information and ahead/behind count
git status -sb

# View commit history
git log

# View compact commit history
git log --oneline

# View commit history with graph
git log --oneline --graph --all
```

### View Changes
```powershell
# See all changes
git diff

# See staged changes only
git diff --staged

# See changes in specific file
git diff path/to/file.py

# Compare with remote
git fetch
git diff origin/main
```

---

## 🌿 Branch Strategy for Larger Features

Once comfortable with basics, use branches for bigger features:

### Create and Work on Feature Branch
```powershell
# Create and switch to new branch
git checkout -b feature-name

# Work on your feature...
# (make changes, commit regularly)
git add .
git commit -m "Implement feature X"

# Switch back to main
git checkout main

# Merge feature into main
git merge feature-name

# Push to remote
git push origin main

# Delete feature branch (optional)
git branch -d feature-name
```

### Example Feature Branch Workflow
```powershell
# Starting new feature
git checkout -b add-lora-sorting
git add .
git commit -m "Add LoRA stack sorting algorithm"
git commit -m "Add tests for LoRA sorting"
git commit -m "Update documentation for LoRA feature"

# Feature complete, merge it
git checkout main
git merge add-lora-sorting
git push origin main

# Clean up
git branch -d add-lora-sorting
```

---

## ⚙️ Configuration & Shortcuts

### Set Up User Information (One-time Setup)
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Useful Git Aliases
```powershell
# Set up shortcuts
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.cm commit
git config --global alias.last 'log -1 HEAD'

# Now you can use:
git st     # Instead of git status
git co main # Instead of git checkout main
```

### Configure Default Editor
```powershell
# Use VS Code as default editor
git config --global core.editor "code --wait"
```

---

## 🔐 Security Best Practices

### What NOT to Commit
- Passwords or API keys
- Personal access tokens
- Database credentials
- Large binary files (videos, large datasets)
- Build artifacts (use .gitignore)

### Use .gitignore
Ensure your `.gitignore` includes:
```
__pycache__/
*.pyc
*.pyo
.env
venv/
*.log
.vscode/settings.json
```

---

## 🎯 Key Principles Summary

1. **Pull before you start working** - Always sync first
2. **Commit early and often** - Small, logical commits
3. **Push regularly** - Don't let work pile up locally
4. **Use meaningful commit messages** - Future you will thank you
5. **Check `git status` before committing** - Know what you're committing
6. **Branch for big features** - Keep main stable
7. **Never commit secrets** - Use .gitignore and .env files

---

## 📚 Additional Resources

### Git Commands Reference
```powershell
# Clone a repository
git clone https://github.com/username/repo.git

# View remote info
git remote -v

# Fetch without merging
git fetch origin

# View all branches
git branch -a

# Switch branches
git checkout branch-name

# Create and switch to new branch
git checkout -b new-branch-name

# Delete branch
git branch -d branch-name

# View tags
git tag

# Create tag
git tag -a v1.0.0 -m "Version 1.0.0"
```

### Troubleshooting Commands
```powershell
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# View reflog (all actions)
git reflog

# Restore file from specific commit
git checkout <commit-hash> -- path/to/file
```

---

## 📝 Historical Context

This guide consolidates best practices from development sessions and conversations. Key learnings:

- Repository was consolidated from multiple separate repos (v2.0)
- Case standardization completed (UPPER → lower)
- Clean folder structure established
- Archive organization implemented

For historical reference, see:
- [RECOVERED_KNOWLEDGE.md](RECOVERED_KNOWLEDGE.md) - Past conversations
- [CONVERSATION_LOG.md](CONVERSATION_LOG.md) - Recent development sessions
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Repository consolidation guide

---

## 🤝 For Contributors

### First-Time Setup
```powershell
# Clone repository
git clone https://github.com/tbmorgan70/SDXL_COMFYUI_CODE.git
cd SDXL_COMFYUI_CODE

# Install dependencies
pip install -r requirements.txt

# Create your branch
git checkout -b your-feature-name

# Make your changes and commit
git add .
git commit -m "Your contribution"

# Push and create pull request
git push origin your-feature-name
```

### Pull Request Guidelines
1. Create feature branch from main
2. Make focused, logical commits
3. Test your changes
4. Update documentation
5. Submit PR with clear description

---

**Maintained By:** Project contributors  
**Update Frequency:** As workflow evolves  
**Questions?** Open an issue or check [CONVERSATION_LOG.md](CONVERSATION_LOG.md)
