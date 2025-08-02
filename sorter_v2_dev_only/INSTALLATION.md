# Sorter 2.0 Installation Guide

## Quick Installation

### Option 1: Standard Installation (Recommended)
```bash
# 1. Navigate to the sorter directory
cd sorter_v2

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the standard GUI
python gui_standard.py
```

### Option 2: Enhanced GUI Installation
```bash
# 1. Navigate to the sorter directory
cd sorter_v2

# 2. Install all dependencies including CustomTkinter
pip install -r requirements.txt
pip install customtkinter

# 3. Launch the modern GUI
python gui.py
```

### Option 3: Command Line Only
```bash
# 1. Navigate to the sorter directory
cd sorter_v2

# 2. Install minimal dependencies
pip install Pillow

# 3. Launch command line interface
python main.py
```

## Detailed Installation Instructions

### Prerequisites

**Python Version:**
- Python 3.7 or higher required
- Python 3.9+ recommended for best performance
- Check your version: `python --version`

**Operating System:**
- Windows 10/11 (tested)
- macOS 10.14+ (should work)
- Linux Ubuntu 18.04+ (should work)

### Step-by-Step Installation

#### Windows Installation

1. **Install Python (if not already installed):**
   - Download from [python.org](https://python.org)
   - During installation, check "Add Python to PATH"
   - Verify installation: Open Command Prompt and type `python --version`

2. **Download Sorter 2.0:**
   - Extract the sorter_v2 folder to your desired location
   - Example: `C:\Users\YourName\Desktop\sorter_v2`

3. **Install Dependencies:**
   ```cmd
   cd C:\Users\YourName\Desktop\sorter_v2
   pip install -r requirements.txt
   ```

4. **Test Installation:**
   ```cmd
   python gui_standard.py
   ```

#### macOS Installation

1. **Install Python (if not already installed):**
   ```bash
   # Using Homebrew (recommended)
   brew install python

   # Or download from python.org
   ```

2. **Download and Extract Sorter 2.0:**
   ```bash
   cd ~/Desktop
   # Extract sorter_v2 folder here
   cd sorter_v2
   ```

3. **Install Dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Test Installation:**
   ```bash
   python3 gui_standard.py
   ```

#### Linux Installation

1. **Install Python (usually pre-installed):**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-tk

   # CentOS/RHEL
   sudo yum install python3 python3-pip tkinter
   ```

2. **Download and Extract Sorter 2.0:**
   ```bash
   cd ~/Desktop
   # Extract sorter_v2 folder here
   cd sorter_v2
   ```

3. **Install Dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Test Installation:**
   ```bash
   python3 gui_standard.py
   ```

## Dependency Details

### Required Dependencies (requirements.txt)
```
Pillow>=8.0.0
```

**Pillow (PIL):**
- Purpose: Image processing and metadata extraction
- Size: ~10MB download
- License: PIL Software License

### Optional Dependencies

**CustomTkinter:**
```bash
pip install customtkinter
```
- Purpose: Modern GUI appearance with dark/light themes
- Size: ~5MB download
- License: MIT License
- Only needed for enhanced GUI (`gui.py`)

## Virtual Environment Setup (Recommended)

Using a virtual environment keeps Sorter 2.0 dependencies separate from your system Python:

### Windows
```cmd
cd sorter_v2
python -m venv sorter_env
sorter_env\Scripts\activate
pip install -r requirements.txt
```

### macOS/Linux
```bash
cd sorter_v2
python3 -m venv sorter_env
source sorter_env/bin/activate
pip install -r requirements.txt
```

### Using the Virtual Environment
**Activate:** (run this each time before using Sorter)
- Windows: `sorter_env\Scripts\activate`
- macOS/Linux: `source sorter_env/bin/activate`

**Deactivate:** (when finished)
```bash
deactivate
```

## Troubleshooting Installation

### Common Issues

**"python is not recognized" (Windows)**
- Solution: Add Python to your PATH during installation
- Alternative: Use Python Launcher: `py` instead of `python`

**"pip is not found"**
- Windows: `python -m pip install -r requirements.txt`
- macOS/Linux: `python3 -m pip install -r requirements.txt`

**"Permission denied" errors**
- Solution: Use `--user` flag: `pip install --user -r requirements.txt`
- Alternative: Use virtual environment (recommended)

**"No module named 'tkinter'"**
- Ubuntu/Debian: `sudo apt install python3-tk`
- CentOS/RHEL: `sudo yum install tkinter`
- macOS: Usually included with Python

**CustomTkinter installation fails**
- Solution: Update pip first: `pip install --upgrade pip`
- Alternative: Use standard GUI: `python gui_standard.py`

### Verification Steps

1. **Test Python Installation:**
   ```bash
   python --version
   # Should show Python 3.7 or higher
   ```

2. **Test Pillow Installation:**
   ```bash
   python -c "from PIL import Image; print('Pillow working')"
   ```

3. **Test GUI Libraries:**
   ```bash
   python -c "import tkinter; print('Tkinter working')"
   ```

4. **Test Sorter 2.0:**
   ```bash
   cd sorter_v2
   python -c "from core.metadata_engine import MetadataEngine; print('Sorter 2.0 ready')"
   ```

## Post-Installation Setup

### First Launch Checklist

1. **Create Test Folder:**
   - Create a folder with a few ComfyUI images
   - Test with 5-10 images initially

2. **Launch Sorter:**
   ```bash
   python gui_standard.py
   ```

3. **Test Basic Operation:**
   - Select your test folder as source
   - Choose "Sort by Checkpoint" operation
   - Run the operation and verify results

### Configuration

**Default Settings:**
- Supported formats: PNG, JPG, JPEG, WEBP
- Log files saved in session directories
- Progress tracking enabled
- Automatic folder creation enabled

**Customization:**
- Edit `core/metadata_engine.py` to add file formats
- Modify `sorters/color_sorter.py` for custom colors
- Adjust logging levels in `core/diagnostics.py`

## Uninstallation

### Remove Sorter 2.0
1. Delete the `sorter_v2` folder
2. If using virtual environment: Delete the `sorter_env` folder

### Remove Dependencies (if not needed elsewhere)
```bash
pip uninstall Pillow customtkinter
```

## Getting Support

### Before Requesting Help
1. Check your Python version: `python --version`
2. Verify installation: Run verification steps above
3. Check error messages in the console
4. Try the command-line interface: `python main.py`

### Information to Include in Support Requests
- Operating system and version
- Python version
- Complete error message
- Steps you followed
- Whether you're using virtual environment

### Self-Help Resources
- Check the `USER_GUIDE.md` for usage help
- Review `DEVELOPER_GUIDE.md` for technical details
- Try different GUI options if one doesn't work
- Test with small image collections first

## Advanced Installation Options

### Portable Installation
Create a portable version that doesn't require system Python:

1. Use PyInstaller to create executable:
   ```bash
   pip install pyinstaller
   pyinstaller --onefile gui_standard.py
   ```

2. Include all dependencies in the `dist` folder

### System-Wide Installation
Install Sorter 2.0 system-wide (not recommended for beginners):

```bash
# Copy to Python site-packages
python setup.py install

# Or create symbolic links
sudo ln -s /path/to/sorter_v2 /usr/local/bin/sorter
```

### Docker Installation (Advanced)
For containerized deployment:

```dockerfile
FROM python:3.9-slim
COPY sorter_v2 /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t sorter2 .
docker run -v /path/to/images:/images sorter2
```
