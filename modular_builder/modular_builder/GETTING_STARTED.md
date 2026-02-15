# Getting Started with Modular Prompt Builder

## First Time Setup (1 minute)

### Step 1: Launch the Server
- **Windows**: Double-click `START_SERVER.bat`
- **Mac/Linux**: Run `python start_server.py` in terminal

Your browser will automatically open to the prompt builder!

### Step 2: Understand the Interface

#### Top Section - Input Controls:
- **Base Prompt**: Your starting prompt (e.g., "1girl, solo", "landscape", "abstract art")
- **Quality Tags**: Style and quality modifiers
- **Combinations Counter**: Shows total possible variations

#### Middle Section - Categories (10 total):
Each category has:
- ☑️ **Include checkbox**: Turn category on/off
- 🔒 **Lock checkbox**: Keep selection during randomization
- 📁 **Dropdown menu**: Load different themed CSV files
- 📝 **Label input**: Customize category name
- 📜 **Item list**: Click items to select

#### Bottom Section - Controls:
- 🎲 **Randomize**: Random selection from unlocked categories
- 📋 **Copy Prompt**: Copy final prompt to clipboard
- 📦 **Batch Generate**: Create multiple prompts at once

---

## Basic Usage

### Creating a Simple Prompt:
1. Type your base prompt (or keep default)
2. Click items from categories you want to include
3. Watch the prompt build in the output box
4. Click "📋 Copy Prompt"

### Using Randomize:
1. Lock any elements you want to keep (🔒)
2. Uncheck categories you don't want
3. Click "🎲 Randomize"
4. Keep clicking until you get something you like!

### Batch Generation:
1. Set up your base prompt and quality tags
2. Select which categories to include
3. Lock any must-have elements
4. Click "📦 Batch Generate"
5. Enter number of prompts (e.g., 100)
6. File downloads automatically with timestamp

---

## Loading Different Themes

### Switching Content:
1. Find the dropdown menu in any category
2. Select a CSV file from the list
3. Category items update instantly
4. Combinations counter updates automatically

### Example - Cyberpunk Character:
- Body Type → Load `cat_bodytype_generic.csv`
- Scene → Load `cat_scene_cyberpunk.csv`
- Outfit → (Keep default or load punk/goth)
- Visual FX → Load `cat_fx_retroglitch_static.csv`

### Example - Fantasy Character:
- Body Type → Load `cat_bodytype_fantasy.csv`
- Scene → Load `cat_scene_fantasy.csv`
- Outfit → Load `cat_outfit_fantasy.csv`

---

## Understanding the Combinations Counter

The counter shows: **Total Possible Combinations**

### How it's calculated:
- Multiplies the number of items in each **enabled** category
- Example: 10 bodies × 15 scenes × 20 outfits = **3,000 combinations**

### Why it matters:
- See the power of your prompt library
- Understand category impact (small changes = huge results)
- Plan batch generation sizes

---

## Tips for New Users

### Start Simple:
1. Keep default base prompt and quality tags
2. Click through categories to see what's available
3. Try randomize a few times
4. Experiment with locking elements

### Gradually Customize:
1. Adjust base prompt for your needs
2. Try different CSV files in categories
3. Disable categories you don't use
4. Create batch files for training data

### Advanced Usage:
1. Edit CSV files to add your own prompts
2. Create themed category sets
3. Use batch generation for large datasets
4. Mix and match themes for unique results

---

## Common Workflows

### Character Portraits:
- Base: "1girl, solo" or "1boy, solo"
- Enable: Body Type, Outfit, Hair & Makeup, Emotion
- Disable: Scene, Setting (for simple backgrounds)

### Full Scenes:
- Base: "1girl" (no solo needed)
- Enable: All categories
- Quality: Add "depth of field, environmental storytelling"

### Abstract Art:
- Base: "" (leave empty)
- Enable: Visual FX, Mood, Art Reference
- Disable: Character categories
- Quality: Adjust for your art style

### Batch Training Data:
1. Set up categories for your project
2. Lock consistent elements (e.g., art style)
3. Generate 500-1000 prompts
4. Use for model training or testing

---

## Need Help?

### Combinations Counter is 1:
- Check that categories are enabled (☑️)
- Make sure CSV files are loaded
- Verify categories have items

### CSV Files Won't Load:
- Must use the local server (START_SERVER.bat)
- Can't open HTML file directly
- Check file names match format: `cat_[name]_[theme].csv`

### Prompt is Empty:
- Add text to Base Prompt field
- Enable at least one category
- Select items from enabled categories

---

Happy prompting! 🎨✨
