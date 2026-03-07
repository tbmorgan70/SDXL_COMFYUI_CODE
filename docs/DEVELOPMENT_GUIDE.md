# 🛠️ Development Guide

**Last Updated:** March 6, 2026  
**For:** Contributors and developers working on SDXL ComfyUI Code

---

## 🎯 Welcome Contributors!

This guide will help you:
- Set up your development environment
- Understand the codebase structure
- Follow coding standards
- Contribute effectively
- Test your changes

---

## 🚀 Getting Started

### Prerequisites

**Required:**
- Python 3.7 or higher
- Git
- Text editor or IDE (VS Code recommended)

**Optional:**
- Virtual environment tool (venv, conda)
- Python linter (pylint, flake8)

### Initial Setup

```powershell
# 1. Clone the repository
git clone https://github.com/tbmorgan70/SDXL_COMFYUI_CODE.git
cd SDXL_COMFYUI_CODE

# 2. Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate    # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install tool-specific dependencies
pip install -r sorter/requirements.txt

# 5. Verify installation
python sorter/main.py --help
```

---

## 📁 Repository Structure

### Understanding the Layout

```
SDXL_COMFYUI_CODE/
│
├── 📚 Documentation (Root Level)
│   ├── README.md                    # Project overview
│   ├── VERSION.md                   # Version tracking
│   ├── ROADMAP.md                   # Development plans
│   ├── GIT_WORKFLOW.md              # Git best practices
│   ├── KNOWLEDGE_INDEX.md           # Doc navigator
│   └── CONVERSATION_LOG.md          # Dev session log
│
├── 📁 docs/                         # Additional documentation
│   ├── ARCHITECTURE.md              # System design
│   └── DEVELOPMENT_GUIDE.md         # This file
│
├── 🎯 sorter/                       # Main tool (Python)
│   ├── main.py                      # CLI interface
│   ├── gui.py                       # GUI interface
│   ├── core/                        # Core modules
│   ├── sorters/                     # Sorting algorithms
│   └── tests/                       # Unit tests
│
├── 🔄 civitai_converter/            # Converter tool
├── 🌐 builder/                      # HTML builders
├── 📝 modular_builder/              # Modular system
├── 🧪 tests/                        # Repository-level tests
└── 📦 archive/                      # Historical versions
```

### Where to Work

**Adding Features:**
- Sorter features → `sorter/` directory
- New builders → `builder/` directory
- Converter improvements → `civitai_converter/`

**Documentation:**
- User docs → Tool-specific READMEs
- Technical docs → `docs/` directory
- Changes → Update CHANGELOG.md files

**Tests:**
- Unit tests → `tests/` or component-specific test folders
- Integration tests → `tests/` root level

---

## 💻 Development Workflow

### 1. Before You Start

```powershell
# Update your local repository
git pull origin main

# Create a feature branch
git checkout -b feature-your-feature-name

# Or for bug fixes
git checkout -b fix-bug-description
```

### 2. Make Your Changes

Follow the coding standards (see below) and work on your feature or fix.

### 3. Test Your Changes

```powershell
# Run existing tests
python -m pytest tests/

# Test specific component
python -m pytest tests/test_your_feature.py

# Manual testing
python sorter/main.py  # Test CLI
python sorter/gui.py   # Test GUI
```

### 4. Commit and Push

```powershell
# Stage your changes
git add .

# Check what you're committing
git status
git diff --staged

# Commit with descriptive message
git commit -m "Add feature: description of what you did"

# Push to your branch
git push origin feature-your-feature-name
```

### 5. Create Pull Request

1. Go to GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill out PR template with:
   - What changed
   - Why it changed
   - How to test it
5. Submit for review

---

## 📝 Coding Standards

### Python Code Style

**Follow PEP 8:**
```python
# Good: Clear, descriptive names
def extract_checkpoint_name(metadata_dict):
    """Extract checkpoint name from ComfyUI metadata."""
    checkpoint_node = metadata_dict.get('checkpoint', {})
    return checkpoint_node.get('inputs', {}).get('ckpt_name', 'unknown')

# Avoid: Unclear, abbreviated names
def ext_ckpt(md):
    return md.get('ckpt_name')
```

**Key Principles:**
- **Descriptive names:** Variables, functions, classes should be self-documenting
- **4-space indentation:** No tabs
- **Line length:** Max 88 characters (Black formatter standard)
- **Docstrings:** All functions and classes need documentation
- **Type hints:** Use when possible for clarity

### Example Well-Formatted Function

```python
from typing import Dict, Optional, List
from pathlib import Path

def sort_images_by_checkpoint(
    input_dir: Path,
    output_dir: Path,
    file_extensions: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Sort images into folders based on their checkpoint model.
    
    Args:
        input_dir: Directory containing images to sort
        output_dir: Directory where sorted images will be placed
        file_extensions: List of extensions to process (default: ['.png', '.jpg'])
    
    Returns:
        Dictionary with checkpoint names as keys and image counts as values
    
    Raises:
        ValueError: If input_dir doesn't exist
        PermissionError: If output_dir can't be created
    """
    if not input_dir.exists():
        raise ValueError(f"Input directory not found: {input_dir}")
    
    # Implementation...
    results = {}
    return results
```

### HTML/JavaScript Standards

**HTML:**
- Semantic HTML5 elements
- Proper indentation (2 spaces)
- Descriptive IDs and classes
- Comments for major sections

**JavaScript:**
- Modern ES6+ syntax
- Clear function names
- Comments for complex logic
- Error handling

```javascript
// Good: Clear, documented
function generateRandomPrompt(categories) {
    /**
     * Generate a random prompt from selected categories.
     * @param {Array} categories - Array of category objects
     * @returns {string} Generated prompt
     */
    if (!categories || categories.length === 0) {
        console.error('No categories provided');
        return '';
    }
    
    // Implementation...
    return prompt;
}
```

---

## 🧪 Testing Guidelines

### Writing Tests

**Location:** Place tests in `tests/` folder or component-specific test directories.

**Naming Convention:**
- Test files: `test_feature_name.py`
- Test functions: `test_specific_behavior()`

**Example Test:**

```python
import pytest
from pathlib import Path
from sorter.core.metadata_engine import extract_checkpoint_name

def test_extract_checkpoint_name_valid_metadata():
    """Test checkpoint extraction with valid metadata."""
    metadata = {
        'checkpoint': {
            'inputs': {
                'ckpt_name': 'sdxl_base_v1.0.safetensors'
            }
        }
    }
    
    result = extract_checkpoint_name(metadata)
    assert result == 'sdxl_base_v1.0'

def test_extract_checkpoint_name_missing_metadata():
    """Test checkpoint extraction with missing metadata."""
    metadata = {}
    
    result = extract_checkpoint_name(metadata)
    assert result == 'unknown'

def test_extract_checkpoint_name_malformed():
    """Test checkpoint extraction with malformed metadata."""
    metadata = {'checkpoint': None}
    
    result = extract_checkpoint_name(metadata)
    assert result == 'unknown'
```

### Running Tests

```powershell
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_metadata.py

# Run with verbose output
python -m pytest -v tests/

# Run with coverage report
python -m pytest --cov=sorter tests/
```

### Test Coverage Goals

- **Target:** 90% code coverage (per ROADMAP.md)
- **Priority:** Core functionality first
- **Focus:** Edge cases and error handling

---

## 📦 Adding New Features

### Feature Development Checklist

- [ ] **Plan:** Outline feature requirements
- [ ] **Branch:** Create feature branch
- [ ] **Code:** Implement feature following standards
- [ ] **Document:** Add docstrings and comments
- [ ] **Test:** Write unit tests for new code
- [ ] **Manual Test:** Test feature end-to-end
- [ ] **Update Docs:** Update relevant README/docs
- [ ] **Changelog:** Add entry to CHANGELOG.md
- [ ] **Commit:** Clear, descriptive commit messages
- [ ] **PR:** Submit pull request with description

### Example: Adding New Sorting Mode

1. **Create sorter module:**
   ```
   sorter/sorters/my_new_sorter.py
   ```

2. **Implement sorting logic:**
   ```python
   from pathlib import Path
   from typing import List
   
   def sort_by_new_criteria(files: List[Path], output_dir: Path):
       """Sort files using new criteria."""
       # Implementation
       pass
   ```

3. **Add to main menu:**
   - Update `sorter/main.py` (CLI)
   - Update `sorter/gui.py` (GUI)

4. **Write tests:**
   ```
   tests/test_new_sorter.py
   ```

5. **Update documentation:**
   - `sorter/README.md`
   - `sorter/FEATURE_SHOWCASE.md`
   - `sorter/CHANGELOG.md`

6. **Update version:**
   - Increment version in `sorter/version.py`
   - Update `VERSION.md`

---

## 🐛 Debugging Tips

### Common Issues

**Import Errors:**
```powershell
# Ensure you're in the right directory
cd sorter/

# Or use module syntax
python -m sorter.main
```

**Missing Dependencies:**
```powershell
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

**GUI Not Opening:**
```powershell
# Check tkinter installation
python -c "import tkinter; print('OK')"

# If missing, reinstall Python with tkinter
```

### Debugging Tools

**Print Debugging:**
```python
print(f"Debug: variable value = {variable}")
```

**Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

**Python Debugger (pdb):**
```python
import pdb; pdb.set_trace()  # Breakpoint
```

---

## 📋 Code Review Guidelines

### As a Reviewer

**Check for:**
- [ ] Code follows style guidelines
- [ ] Functions have docstrings
- [ ] Tests are included
- [ ] Documentation is updated
- [ ] No obvious bugs or security issues
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate

**Provide:**
- Constructive feedback
- Specific suggestions
- Praise for good work
- Clear action items

### As a Contributor

**Before Requesting Review:**
- [ ] Self-review your changes
- [ ] Run all tests locally
- [ ] Check for typos and formatting
- [ ] Update relevant documentation
- [ ] Write clear PR description

---

## 🔧 Development Tools

### Recommended Tools

**IDE/Editors:**
- **VS Code** - Excellent Python support, Git integration
- **PyCharm** - Full-featured Python IDE
- **Sublime Text** - Lightweight, fast

**VS Code Extensions:**
- Python (Microsoft)
- Pylance (Microsoft)
- GitLens
- Python Test Explorer

**Linting/Formatting:**
```powershell
# Install tools
pip install black flake8 pylint

# Format code
black sorter/

# Lint code
flake8 sorter/
pylint sorter/
```

**Version Control:**
- Git GUI: GitKraken, SourceTree, GitHub Desktop
- Command line Git (most flexible)

---

## 📚 Learning Resources

### Python Development
- [Python Official Docs](https://docs.python.org/3/)
- [PEP 8 Style Guide](https://pep8.org/)
- [Real Python Tutorials](https://realpython.com/)

### Testing
- [Pytest Documentation](https://docs.pytest.org/)
- [Test-Driven Development Guide](https://testdriven.io/)

### Git Workflow
- [GIT_WORKFLOW.md](../GIT_WORKFLOW.md) - Repository-specific guide
- [Pro Git Book](https://git-scm.com/book/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

### Project-Specific
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [VERSION.md](../VERSION.md) - Version history
- [ROADMAP.md](../ROADMAP.md) - Future plans

---

## 🤝 Communication

### Getting Help

**Stuck on something?**
1. Check documentation (KNOWLEDGE_INDEX.md)
2. Search existing issues on GitHub
3. Ask in discussions/issues
4. Consult CONVERSATION_LOG.md for context

### Reporting Bugs

**Create an issue with:**
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version)
- Screenshots if relevant

### Suggesting Features

**Propose features with:**
- Use case description
- How it benefits users
- Possible implementation approach
- Willingness to contribute code

---

## 🎯 Development Roadmap Context

### Current Phase (Q2 2026)
Per [ROADMAP.md](../ROADMAP.md):
- Repository cleanup and organization (v3.0)
- Documentation enhancement
- Test coverage improvement

### Next Phase (Q3 2026)
- Tool integration planning
- Unified configuration system
- API development preparation

### Contributing Alignment
Check [ROADMAP.md](../ROADMAP.md) to see where your contributions fit into the bigger picture.

---

## ✅ Pre-Commit Checklist

Before every commit:

- [ ] Code runs without errors
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Docstrings are present
- [ ] No commented-out code left behind
- [ ] No debug print statements
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] Commit message is descriptive

---

## 📞 Contact & Support

**Repository:** https://github.com/tbmorgan70/SDXL_COMFYUI_CODE  
**Issues:** GitHub Issues tab  
**Discussions:** GitHub Discussions tab

**Before opening an issue:**
1. Search existing issues
2. Check documentation
3. Try debugging locally

---

## 🙏 Thank You!

Your contributions help make this project better for everyone. Whether it's:
- Fixing typos
- Reporting bugs
- Adding features
- Improving documentation
- Helping other users

**Every contribution matters!** 🎉

---

**Document Status:** Living guide - updated as processes evolve  
**Maintained By:** Project maintainers and contributors  
**Feedback Welcome:** Open an issue to suggest improvements to this guide
