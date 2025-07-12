# Development Notes

## Git Workflow Best Practices (from chat session)

### Daily Workflow:
1. Start with `git pull origin main`
2. Make changes
3. Commit frequently with descriptive messages
4. Push regularly with `git push origin main`

### Recommended Pattern:
```powershell
# Morning routine
git pull origin main

# After completing work:
git add .
git status
git commit -m "Descriptive message"
git push origin main
```

### Key Principles:
- Pull before starting work
- Commit early and often  
- Push regularly
- Use meaningful commit messages
- Check `git status` before committing

### Common Commands:
```powershell
git status          # Check what's changed
git diff           # See detailed changes
git stash          # Temporarily save changes
git stash pop      # Restore stashed changes
```

## Project Structure:
- `builder/` - HTML prompt builders for SDXL/ComfyUI
- `SORTER/` - Python utilities for file organization
- Root - Documentation and project files

## Current Work:
- Building generic random prompt generator with 10 customizable categories
- Implementing dual toggle switches and fancy UI
