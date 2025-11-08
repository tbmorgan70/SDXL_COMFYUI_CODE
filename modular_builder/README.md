# Modular Prompt Generator - CSV System

A powerful, fully customizable prompt builder for AI image generation (SDXL, Stable Diffusion, etc.). Build complex prompts using modular categories, CSV file loading, and dynamic combinations.

## 🎬 Quick Start

1. **Double-click** `START_SERVER.bat` to launch
2. **Customize** base prompt and quality tags in the input boxes
3. **Select** items from categories or use 🎲 Randomize
4. **Watch** the combinations counter to see total possibilities
5. **Copy** your prompt or 📦 Batch Generate multiple prompts

## 🚀 What's New

### Latest Updates:
- ✨ **Customizable Base Prompt**: Enter your own base prompt (e.g., "1girl, solo", "1boy", "landscape", etc.)
- ✨ **Customizable Quality Tags**: Edit quality tags to match your workflow
- 🎰 **Live Combinations Counter**: See exactly how many possible prompt combinations you can generate!
- 📦 **Dynamic CSV Loading**: All 10 categories now support loading different CSV files
- 🔒 **Lock System**: Lock specific selections while randomizing others

Your prompt generator is now COMPLETELY modular and customizable! Each category can load different content from CSV files, making it incredibly flexible for different projects.

## 🎯 Key Features

### User Input Controls:
- **Base Prompt Box**: Customize your starting prompt (defaults to "1girl, solo")
- **Quality Tags Box**: Modify quality/style tags (defaults to "8K, ultra-textural, highly detailed, cinematic lighting, masterpiece")
- **Live Updates**: Both fields update the prompt in real-time as you type

### Combinations Counter:
- Shows total possible prompt combinations (e.g., "1,234,567")
- Updates dynamically when you:
  - Toggle categories on/off
  - Load new CSV files
  - Change selections
- Helps you understand the scope of your prompt library!

### Category System:
- 10 fully modular categories
- Each category can load different themed CSV files
- Mix and match themes for unique combinations
- Include/exclude categories as needed
- Lock specific selections during randomization

## 📁 File Structure
```
modular_builder/
├── Nova_skyrift_darkside_adventures_newnogood.html  # Main application
├── START_SERVER.bat                                  # Quick start (Windows)
├── start_server.py                                   # Python server script
├── README.md                                         # This file
└── categories/                                       # CSV files directory
    ├── cat_bodytype_generic.csv
    ├── cat_bodytype_fantasy.csv
    ├── cat_scene_cyberpunk.csv
    ├── cat_outfit_spacetime.csv
    └── ... (many more category files)
```

## 🔧 How It Works

### Getting Started:
1. **Launch the Server**: Double-click `START_SERVER.bat` (or run `python start_server.py`)
2. **Browser Opens**: Application loads automatically
3. **Customize Inputs**: Modify base prompt and quality tags as needed
4. **Select Categories**: Choose which categories to include
5. **Load Themes**: Use dropdowns to load different CSV files for each category
6. **Generate Prompts**: Click items to build prompts, or use Randomize/Batch features

### Category Controls:
Each category section has:
- **Include Checkbox**: Toggle category on/off
- **Lock Checkbox**: Lock selection during randomization
- **Theme Dropdown**: Load different CSV files
  - **Current (Default)**: Keeps existing content
  - **CSV files**: Loads new themed content
- **Label Input**: Customize category display name
- **Item List**: Scrollable list of prompt pieces

### 10 Available Categories:
1. **Body Type** - Character physical descriptions
2. **Scene** - Environmental settings
3. **Outfit** - Clothing and attire
4. **Visual FX** - Effects and styling
5. **Art Reference** - Art styles and references
6. **Setting** - Location details
7. **Mood** - Atmosphere and tone
8. **Accessories** - Additional items
9. **Hair & Makeup** - Styling details
10. **Emotion** - Character expressions

## 📝 Creating New Categories

### CSV Format:
```csv
prompt_piece
your first prompt piece here
your second prompt piece here
etc...
```

**Important**: 
- First line must be the header: `prompt_piece`
- No quotes needed around entries
- One prompt piece per line
- Empty lines are ignored

### Naming Convention:
`cat_[categoryname]_[theme].csv`

Examples:
- `cat_outfit_medieval.csv`
- `cat_mood_romantic.csv`
- `cat_setting_western.csv`
- `cat_bodytype_fantasy.csv`

## 🎯 Workflow Examples

### Project Switching:
1. **Cyberpunk Project**: 
   - Load `cat_scene_cyberpunk.csv`
   - Load `cat_outfit_cyberpunk.csv`
   - Set base prompt: "1girl, solo"
   - Set quality tags for your preferred style

2. **Fantasy Project**: 
   - Load `cat_bodytype_fantasy.csv`
   - Load `cat_scene_fantasy.csv`
   - Load `cat_outfit_fantasy.csv`
   - Adjust tags as needed

3. **Abstract Art**:
   - Load abstract-themed categories
   - Disable character categories
   - Focus on mood, palette, and composition

4. **Mixed Projects**: Mix and match themes across categories for unique combinations!

### Batch Generation Workflow:
1. Set up your base prompt and quality tags
2. Select which categories to include
3. Lock any specific choices you want in every prompt
4. Click "📦 Batch Generate"
5. Enter number of prompts to generate
6. Prompts saved automatically with timestamp

### Content Management:
- ✅ Edit CSV files instead of HTML
- ✅ Team members can contribute category files
- ✅ Version control friendly
- ✅ Easy backup and sharing
- ✅ Create project-specific category sets

## ✨ Core Features:
- 🎨 **Customizable Inputs**: User-defined base prompts and quality tags
- 🎰 **Live Counter**: Real-time display of total possible combinations
- 🔒 **Lock System**: Lock selections during randomization
- 📦 **Batch Generation**: Generate multiple prompts at once (respects locks)
- 🎲 **Smart Randomization**: Randomize unlocked categories only
- 📋 **Copy/Export**: Copy to clipboard or export batch to text file
- 💾 **Dynamic Loading**: All categories support CSV file loading
- 🎭 **Theme Mixing**: Combine different themes across categories
- 📊 **Visual Feedback**: See what's selected and what's possible
- ⚡ **Real-time Updates**: Instant prompt preview as you select/type

## 🌐 Server Setup (Required for CSV Loading)

### Why You Need a Local Server:
Browsers block loading local CSV files when opening HTML files directly (`file://` protocol). The included server solves this!

### Quick Start - Method 1 (Easiest):
1. **Double-click** `START_SERVER.bat`
2. Browser automatically opens the app
3. CSV categories work perfectly! ✨

### Manual Start - Method 2:
1. Open PowerShell/Command Prompt in this folder
2. Run: `python start_server.py`
3. Visit the URL shown (usually `http://localhost:8000`)

### What the Server Does:
- ✅ Enables CSV file loading
- ✅ Prevents CORS errors
- ✅ Allows all file access features
- ✅ Same beautiful interface
- ✅ Works offline (no internet needed)

### Troubleshooting:
- **Port already in use?** Close other apps using port 8000, or edit `start_server.py` to use a different port
- **Python not found?** Install Python from python.org
- **Browser doesn't open?** Manually visit `http://localhost:8000`

---

## 🚀 Next Steps:
1. ✅ Customize your base prompt and quality tags
2. ✅ Load CSV files for different themes and projects
3. ✅ Create your own category files
4. ✅ Use the combinations counter to understand your library size
5. ✅ Share category files with your team!

---

## 💡 Tips & Tricks

### Maximizing the Combinations Counter:
- **Enable more categories** = exponentially more combinations
- **Load larger CSV files** = more variety per category
- **Mix themes** for unique cross-genre prompts

### Efficient Workflow:
- **Lock favorites**: Use 🔒 to keep specific elements while randomizing others
- **Batch generate**: Create hundreds of variations quickly
- **Save presets**: Edit CSV files with your most-used prompts
- **Theme sets**: Create matching CSV files for cohesive projects

### Custom Prompts:
- **Clear base prompt** for non-character images (landscapes, abstract art)
- **Adjust quality tags** for different AI models or styles
- **Disable categories** you don't need for cleaner prompts
- **Use commas** in CSV entries for multi-part descriptions

### File Organization:
- Group related CSV files with consistent naming
- Create project folders with themed category sets
- Version control your CSV files for team collaboration
- Back up your custom categories regularly

---

This system transforms your generator into a universal prompt-building platform! 🎉