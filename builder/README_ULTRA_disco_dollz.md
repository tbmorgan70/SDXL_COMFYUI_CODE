# ULTRA Disco Dollz Prompt Builder

A sophisticated dual-toggle prompt builder for generating high-quality SDXL prompts with disco/cybergoth aesthetics. This HTML-based tool features dynamic category filtering, visual effects, and customizable prompt elements.

## Features

- **Dual Toggle System**: Switch between Realism/Anime and SFW/NSFW content
- **10 Customizable Categories**: Body type, outfit, makeup, pose, expression, accessories, setting, details, vibe, and lighting
- **Visual Effects**: Disco-themed animations, glitch effects, and sparkle overlays
- **Randomization**: One-click random prompt generation with toggle respect
- **Local Storage**: Remembers toggle preferences between sessions
- **Copy Functionality**: Easy prompt copying to clipboard

## How to Use

1. **Open the File**: Load `ULTRA_disco_dollz_latest.HTML` in any modern web browser
2. **Set Toggles**: 
   - Check "ANIME" for anime-style prompts (unchecked = realistic style)
   - Check "NSFW" for adult content (unchecked = safe for work)
3. **Select Elements**: Click on items in each category to add them to your prompt
4. **Generate**: Use the randomize button or manually select elements
5. **Copy**: Click "Copy Prompt" to copy the generated text

## Dual Toggle Logic (A/B C/D System)

The prompt builder uses a sophisticated filtering system based on two toggle states:

### Toggle 1 (A/B): Style Toggle
- **A (Realism)**: `data-toggle1="a"` - Realistic, photographic style prompts
- **B (Anime)**: `data-toggle1="b"` - Anime, illustrated, fantastical style prompts
- **No attribute**: Available for both styles

### Toggle 2 (C/D): Content Toggle  
- **C (SFW)**: `data-toggle2="c"` - Safe for work content
- **D (NSFW)**: `data-toggle2="d"` - Adult/mature content
- **No attribute**: Available for both content types

### Example Implementation
```html
<!-- Realism + SFW -->
<li data-toggle1="a" data-toggle2="c" onclick="pick('outfit', this)">
  vintage sequin halter top and satin bell-bottoms
</li>

<!-- Anime + NSFW -->
<li data-toggle1="b" data-toggle2="d" onclick="pick('outfit', this)">
  latex body suit with deep cleavage and belly cutout
</li>

<!-- Available for all toggles -->
<li onclick="pick('vibe', this)">
  chaotic joy and unfiltered nightlife energy
</li>
```

## Customizing Categories

### Adding New Categories

1. **HTML Structure**: Add a new section div with this template:
```html
<div class="section" id="new-category">
  <h3 id="label-new-category">Category Name</h3>
  <label class="cat-toggle">
    <input type="checkbox" id="enable-new-category" checked> include
  </label>
  <input type="text" value="Category Name" oninput="updateLabel('new-category', this.value)">
  <ul>
    <!-- Your prompt items here -->
  </ul>
</div>
```

2. **JavaScript Update**: Add the category to the `settingOrder` array:
```javascript
const settingOrder = ['bodytype', 'outfit', 'makeup', 'pose', 'expression', 'accessory', 'setting', 'details', 'vibe', 'lighting', 'new-category'];
```

3. **Initialize Selection Object**: Add to the `sel` object:
```javascript
const sel = {'bodytype':'', 'outfit':'', 'new-category':'', /* ... other categories */ };
```

### Modifying Existing Prompts

Each prompt item follows this structure:
```html
<li data-toggle1="[a|b]" data-toggle2="[c|d]" onclick="pick('category', this)">
  Your prompt text here
</li>
```

**Toggle Combinations:**
- `data-toggle1="a" data-toggle2="c"` - Realism + SFW
- `data-toggle1="a" data-toggle2="d"` - Realism + NSFW  
- `data-toggle1="b" data-toggle2="c"` - Anime + SFW
- `data-toggle1="b" data-toggle2="d"` - Anime + NSFW
- No attributes - Available for all toggle states

### Removing Categories

1. Delete the entire `<div class="section">` block
2. Remove the category from `settingOrder` array
3. Remove the category from `sel` object initialization

## Styling and Effects

### Disco Theme Elements

The builder includes several visual effect layers:

- **Disco Static**: Animated color gradients (`#disco-static`)
- **Scanlines**: Moving horizontal lines (`#disco-scanlines`) 
- **Sparkles**: Rotating disco ball reflections (`#disco-sparkles`)

### Customizing Visual Effects

**Disable Effects**: Comment out or remove the effect divs:
```html
<!-- <div id="disco-static"></div> -->
<!-- <div id="disco-scanlines"></div> -->
<!-- <div id="disco-sparkles"></div> -->
```

**Modify Colors**: Update the CSS color values in the `<style>` section:
```css
/* Change primary disco colors */
rgba(255,0,255,0.1)  /* Magenta */
rgba(0,255,255,0.1)  /* Cyan */
rgba(255,215,0,0.1)  /* Gold */
```

## File Structure

```
ULTRA_disco_dollz_latest.HTML
├── CSS Styles (embedded)
│   ├── Disco effects animations
│   ├── Layout and typography
│   └── Interactive element styling
├── HTML Content
│   ├── Header with toggles
│   ├── Category sections (10 total)
│   └── Footer with prompt box
└── JavaScript Logic
    ├── Toggle state management
    ├── Category selection handling
    ├── Prompt generation
    └── Local storage integration
```

## Best Practices for Customization

### Adding New Prompts
1. **Consistency**: Keep similar length and style within categories
2. **Toggle Logic**: Ensure appropriate toggle attributes for content type
3. **Testing**: Verify prompts work well with your SDXL model
4. **Organization**: Group similar concepts within categories

### Category Guidelines
- **Body Type**: Physical descriptions, ethnicity, body shape
- **Outfit**: Clothing, fabrics, styles
- **Makeup & Hair**: Cosmetics, hairstyles, color schemes  
- **Pose**: Body positioning, stance, action
- **Expression**: Facial expressions, emotions
- **Accessories**: Props, jewelry, additional items
- **Setting**: Environment, location, background
- **Details**: Fine details, textures, specific elements
- **Vibe**: Overall mood, energy, atmosphere
- **Lighting**: Illumination, effects, visual atmosphere

## Technical Notes

- **Browser Compatibility**: Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- **Mobile Responsive**: Sections will wrap on smaller screens
- **Local Storage**: Toggle preferences persist between sessions
- **No External Dependencies**: Completely self-contained HTML file

## Troubleshooting

**Prompts not filtering correctly**: Check that toggle attributes match the expected values (a/b for style, c/d for content)

**Visual effects not working**: Ensure CSS animations are enabled in your browser

**Copy function not working**: Use a modern browser with clipboard API support

**Categories not updating**: Verify the category ID matches in HTML, CSS, and JavaScript

## License

This tool is designed for personal and educational use. Modify and distribute as needed for your AI art projects.

---

*Created for SDXL prompt generation with ComfyUI workflows. Optimized for disco/cybergoth aesthetic generation.*
