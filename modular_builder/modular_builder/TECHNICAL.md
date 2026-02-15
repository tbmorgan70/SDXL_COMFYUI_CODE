# Technical Documentation

## Architecture Overview

### File Structure
```
modular_builder/
├── Nova_skyrift_darkside_adventures_newnogood.html  # Main application (single-file)
├── START_SERVER.bat                                  # Windows launcher
├── start_server.py                                   # Python HTTP server
├── README.md                                         # Main documentation
├── GETTING_STARTED.md                                # User guide
├── CHANGELOG.md                                      # Version history
└── categories/                                       # CSV data files
    └── cat_[name]_[theme].csv
```

### Technology Stack
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Server**: Python 3 http.server (development)
- **Data Format**: CSV files
- **No Dependencies**: Works with just Python 3 (standard library)

---

## Core JavaScript Functions

### Data Structure: `sel` Object
```javascript
const sel = {
  bodytype: '',
  scene: '',
  outfit: '',
  visualfx: '',
  artreference: '',
  setting: '',
  mood: '',
  accessories: '',
  hairmakeup: '',
  emotion: ''
};
```
Stores currently selected prompt piece for each category.

### Key Functions

#### `update()`
Main function that builds the final prompt:
1. Reads base prompt from input box
2. Collects selected items from enabled categories
3. Appends quality tags from input box
4. Updates prompt output
5. Triggers combinations counter update

#### `updateCombinationsCount()`
Calculates total possible combinations:
1. Iterates through all categories
2. Counts items in enabled categories only
3. Multiplies counts together
4. Formats with commas and displays

#### `pick(section, element)`
Handles item selection:
1. Clears previous selection styling
2. Highlights selected item
3. Updates `sel` object
4. Calls `update()`

#### `loadCategory(categoryId, csvFile)`
Loads CSV files dynamically:
1. Fetches CSV from server
2. Parses content with `parseCSV()`
3. Updates UI with `updateCategoryItems()`
4. Clears current selection
5. Updates combinations counter

#### `parseCSV(csvText)`
Simple CSV parser:
- Skips header row
- Trims whitespace
- Returns array of prompt pieces

#### `generateBatchPrompts(count)`
Batch generation system:
1. Stores current selections
2. Loops `count` times
3. Randomizes unlocked categories
4. Builds prompt with user inputs
5. Restores original selections
6. Downloads as text file

#### `randomize()`
Smart randomization:
- Only randomizes **unlocked** categories
- Respects user locks (🔒)
- Calls `update()` after each change

---

## CSS Architecture

### Theme System
- Dark background with gradient effects
- Punk/retro aesthetic with static overlays
- Responsive grid layout
- Color scheme: Black, Pink (#ff0040), Green (#00ff41)

### Key Classes
- `.section`: Individual category container
- `.cat-toggle`: Checkbox styling
- `.footer`: Fixed bottom bar with controls
- Animated effects: `#disco-static`, `#disco-scanlines`, `#disco-sparkles`

---

## CSV File Format

### Structure
```csv
prompt_piece
first prompt piece
second prompt piece
third prompt piece
```

### Rules
1. First line must be: `prompt_piece` (header)
2. One prompt per line
3. No quotes needed
4. Empty lines ignored
5. Commas allowed within entries

### Naming Convention
`cat_[category]_[theme].csv`

Examples:
- `cat_bodytype_fantasy.csv`
- `cat_scene_cyberpunk.csv`
- `cat_outfit_medieval.csv`

---

## Adding New Features

### Adding a New Category

1. **Update HTML** - Add section:
```html
<div class="section" id="newcategory">
  <h3 id="label-newcategory">New Category</h3>
  <label class="cat-toggle">
    <input type="checkbox" id="enable-newcategory" checked onchange="updateCombinationsCount()"> include
  </label>
  <label class="cat-toggle">
    <input type="checkbox" id="lock-newcategory"> 🔒 lock
  </label>
  <select id="category-newcategory" onchange="loadCategory('newcategory', this.value)">
    <option value="default">Current (Default)</option>
  </select>
  <input type="text" value="New Category" oninput="updateLabel('newcategory', this.value)">
  <ul>
    <li onclick="pick('newcategory', this)">Default item 1</li>
    <li onclick="pick('newcategory', this)">Default item 2</li>
  </ul>
</div>
```

2. **Update JavaScript** - Add to `sel` object:
```javascript
const sel = {
  // ... existing categories
  newcategory: ''
};
```

3. **Update JavaScript** - Add to `settingOrder` array:
```javascript
const settingOrder = [
  // ... existing categories
  'newcategory'
];
```

4. **Create CSV files** in `categories/` folder

### Modifying the Combinations Counter

Located in `updateCombinationsCount()`:
```javascript
function updateCombinationsCount() {
  let totalCombinations = 1;
  
  settingOrder.forEach(sec => {
    if (document.getElementById('enable-' + sec).checked) {
      const allItems = Array.from(document.querySelectorAll('#'+sec+' li'));
      const visibleItems = allItems.filter(li => li.style.display !== 'none');
      const count = visibleItems.length;
      
      if (count > 0) {
        totalCombinations *= count;
      }
    }
  });
  
  const formattedCount = totalCombinations.toLocaleString();
  document.getElementById('combinationsCount').textContent = formattedCount;
}
```

### Adding New Input Fields

Follow the pattern of `basePrompt` and `qualityTags`:
```html
<input type="text" id="newfield" value="default" oninput="update()">
```

Then reference in `update()` function:
```javascript
const newValue = document.getElementById('newfield').value.trim();
```

---

## Server Configuration

### Python Server (`start_server.py`)
- Default port: 8000
- Auto-finds available port if busy
- Auto-opens browser
- Serves all files in directory

### Customizing Port
Edit `start_server.py`:
```python
PORT = 8000  # Change to desired port
```

### Production Deployment
For production, use proper web server:
- **Apache**: Standard static hosting
- **Nginx**: High-performance option
- **Netlify/Vercel**: Easy deployment with CDN

---

## Event Flow

### Page Load:
1. `DOMContentLoaded` event fires
2. `loadAvailableCategories()` fetches CSV list
3. `populateAllDropdowns()` fills select menus
4. `updateCombinationsCount()` initializes counter

### Category Toggle:
1. User clicks checkbox
2. `onchange="updateCombinationsCount()"` fires
3. Counter recalculates
4. Display updates

### CSV Load:
1. User selects CSV from dropdown
2. `loadCategory()` fetches file
3. `parseCSV()` processes content
4. `updateCategoryItems()` updates UI
5. Counter auto-updates

### Item Selection:
1. User clicks item
2. `pick()` updates selection
3. `update()` rebuilds prompt
4. Output updates instantly

---

## Browser Compatibility

### Tested Browsers:
- ✅ Chrome/Edge (Chromium) 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Opera 76+

### Required Features:
- ES6+ JavaScript
- CSS Grid
- Fetch API
- LocalStorage (optional)
- Array methods (filter, map, forEach)

### Known Issues:
- ❌ File:// protocol blocks CSV loading → Use local server
- ⚠️ Very old browsers may not support ES6 syntax

---

## Performance Considerations

### Current Performance:
- **Categories**: 10 (can easily handle 20+)
- **Items per category**: 50-100 recommended, supports 500+
- **Batch generation**: Tested up to 10,000 prompts
- **CSV file size**: Keep under 100KB for fast loading

### Optimization Tips:
1. Minimize CSV file reads (cache in memory)
2. Debounce `update()` if adding real-time features
3. Use `documentFragment` for large item lists
4. Consider lazy-loading for 50+ categories

---

## Security Notes

### Local Server:
- Binds to localhost only (not accessible externally)
- No authentication needed (local use only)
- No data persistence (stateless)

### Production Considerations:
- Add HTTPS for public deployment
- Sanitize user inputs if adding save features
- Implement CSRF protection if adding backend
- Rate-limit batch generation endpoints

---

## Testing

### Manual Testing Checklist:
- [ ] All categories load CSV files correctly
- [ ] Combinations counter updates on all actions
- [ ] Randomize respects locks
- [ ] Batch generation creates valid prompts
- [ ] Input boxes trigger real-time updates
- [ ] Copy to clipboard works
- [ ] Server auto-opens browser

### Adding Automated Tests:
Consider using:
- **Jest**: Unit testing JavaScript functions
- **Playwright**: End-to-end browser testing
- **CSV validation**: Ensure file format compliance

---

## Future Enhancement Ideas

### Potential Features:
- 🎨 **Save Presets**: Store favorite configurations
- 🔍 **Search/Filter**: Search within categories
- 📊 **Statistics**: Track most-used prompts
- 🎭 **Themes**: Light/dark mode toggle
- 💾 **Export/Import**: Share configurations
- 🔄 **Undo/Redo**: History system
- 📱 **Mobile Optimization**: Better touch interface
- 🌐 **Multi-language**: i18n support
- 🔌 **API Integration**: Connect to AI services
- 📈 **Analytics**: Usage tracking

### Community Contributions:
- Share CSV category collections
- Theme variants (colors, layouts)
- Category templates for specific use cases
- Batch export format options

---

## Support & Contributing

For questions, issues, or contributions:
1. Check existing documentation
2. Test with latest version
3. Provide clear reproduction steps
4. Include browser/OS information

---

Built with ❤️ for the AI art community
