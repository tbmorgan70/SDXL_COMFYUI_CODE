# Changelog

## Version 2.0 - Fully Customizable Edition

### New Features
- ✨ **Customizable Base Prompt**: User input box for base prompt (replaces hardcoded "1girl, solo")
- ✨ **Customizable Quality Tags**: User input box for quality/style tags (replaces hardcoded quality string)
- 🎰 **Live Combinations Counter**: Real-time display of total possible prompt combinations
  - Updates when categories are toggled on/off
  - Updates when CSV files are loaded
  - Formatted with commas for readability (e.g., "1,234,567")
- 📋 **Enhanced UI**: Cleaner input controls with labels above the prompt output

### Improvements
- Removed duplicate quality tag checking logic (no longer needed)
- All input boxes trigger real-time updates
- Better visual hierarchy with input boxes before output
- Combinations counter styled to match the theme
- All 10 categories now support dynamic CSV loading

### Technical Changes
- Added `updateCombinationsCount()` function
- Updated `update()` function to read from input boxes
- Updated `generateBatchPrompts()` to use dynamic inputs
- Added `onchange` handlers to all category checkboxes
- Initialized counter on page load

### Bug Fixes
- Fixed prompt generation to properly use user-supplied values
- Improved real-time updates across all interactions

---

## Version 1.0 - Modular CSV System

### Initial Features
- 10 modular categories with individual controls
- CSV file loading system for dynamic content
- Lock system for randomization
- Batch prompt generation
- Copy to clipboard functionality
- Local server setup for file access
- Category enable/disable toggles
- Custom category naming
