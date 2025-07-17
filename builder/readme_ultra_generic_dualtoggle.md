# ULTRA Generic Dual Toggle Prompt Builder

## Overview

The ULTRA Generic Dual Toggle Prompt Builder is a sophisticated web-based tool for generating AI image prompts with customizable categories and dual toggle switches. Built with a cyberpunk aesthetic featuring punk rock and gothic themes, this builder provides an intuitive interface for creating detailed prompts for SDXL/ComfyUI workflows.

## Features

### 🎭 Dual Toggle System
- **Style Toggle**: Switch between Punk Rock and Gothic themes
- **Content Toggle**: Toggle between SFW and NSFW content modes
- **Dynamic Content**: Categories automatically show/hide relevant options based on toggle states
- **Persistent Settings**: Toggle preferences are saved in browser localStorage

### 🎨 Visual Design
- **Cyberpunk Aesthetic**: Dark theme with neon colors (pink/green)
- **Animated Effects**: 
  - Static/glitch overlay effects
  - Scanline animations
  - Sparkle disco ball effects
  - Pulsing section borders
  - Glitch text animations
- **Responsive Layout**: Flexible grid system that adapts to different screen sizes

### 📋 10 Customizable Categories

1. **Body Type** - Physique, build, proportions
2. **Hair & Makeup** - Style, color, texture, vibe  
3. **Camera Angle** - Perspective, lens, framing
4. **Pose** - Body position, gesture, attitude
5. **Clothing** - Style, color, material, fit
6. **Accessories** - Jewelry, props, extras
7. **Settings** - Environment, location, mood
8. **Style Reference** - Genre, inspiration, art style
9. **Vibe** - Mood, energy, emotional impact
10. **Lighting** - Type, color, direction, atmosphere

### ⚙️ Functionality
- **Category Labels**: Fully customizable section names
- **Include/Exclude**: Toggle individual categories on/off
- **Smart Selection**: Visual feedback for selected items
- **Random Generation**: Intelligent randomization respecting toggle states
- **Prompt Building**: Automatic prompt assembly with proper formatting
- **Copy to Clipboard**: One-click prompt copying

## Usage Guide

### Getting Started
1. Open `ULTRA_txt2img_generic_dualtoggle.html` in any modern web browser
2. The interface loads with default "Punk Rock" theme in SFW mode
3. All categories are enabled by default with placeholder content

### Toggle Controls
- **Gothic Mode Checkbox (🖤)**: Switch between Punk Rock ↔ Gothic themes
- **NSFW Mode Checkbox (🔞)**: Enable adult content options

### Customizing Categories
1. **Rename Categories**: Click in the text input field below each category title
2. **Add Content**: Replace placeholder text with actual prompt options
3. **Toggle Categories**: Use checkboxes to include/exclude from final prompt
4. **Select Items**: Click on any option to add it to your prompt

### Content Management
Each category supports content tagged with:
- `data-toggle-punk="true"` - Shows only in Punk Rock mode
- `data-toggle-goth="true"` - Shows only in Gothic mode  
- `data-toggle-nsfw="true"` - Shows only when NSFW mode is enabled
- Items without tags are always visible

### Generating Prompts
- **Manual Selection**: Click individual items from each category
- **Randomize Button (🎲)**: Automatically selects random items from visible options
- **Copy Button (📋)**: Copies the complete prompt to clipboard

## Technical Implementation

### File Structure
```
ULTRA_txt2img_generic_dualtoggle.html
├── HTML Structure
│   ├── Visual effects overlays
│   ├── Header with title and toggles
│   ├── 10 customizable category sections
│   └── Fixed footer with prompt box and controls
├── CSS Styling
│   ├── Cyberpunk animations and effects
│   ├── Responsive grid layout
│   ├── Interactive hover states
│   └── Visual feedback for selections
└── JavaScript Logic
    ├── Toggle state management
    ├── Dynamic content filtering
    ├── Prompt building engine
    └── Local storage persistence
```

### Key Functions

#### `toggleItems()`
- Manages visibility of content based on toggle states
- Updates title text dynamically
- Clears selections when switching modes

#### `pick(section, element)`
- Handles item selection with visual feedback
- Updates internal selection state
- Triggers prompt regeneration

#### `randomize()`
- Intelligently selects random items from visible options
- Respects current toggle states
- Maintains category enable/disable settings

#### `update()`
- Assembles final prompt from selected items
- Adds base tags (`1girl, solo`) and quality suffixes
- Updates the prompt display box

### Data Attributes System
Content items use data attributes for smart filtering:
```html
<li data-toggle-punk="true" data-toggle-nsfw="true">Punk NSFW content</li>
<li data-toggle-goth="true">Gothic SFW content</li>
<li data-toggle-nsfw="true">Generic NSFW content</li>
<li>Always visible content</li>
```

## Customization Guide

### Adding New Content
1. Create new `<li>` elements within category `<ul>` sections
2. Add appropriate `data-toggle-*` attributes for filtering
3. Include `onclick="pick('categoryname', this)"` for functionality

### Modifying Categories
1. **Change Category Names**: Edit the `<h3>` title and input field
2. **Add/Remove Categories**: Update both HTML structure and JavaScript arrays
3. **Reorder Categories**: Modify the `settingOrder` array in JavaScript

### Styling Customization
- **Colors**: Update CSS custom properties for theme colors
- **Animations**: Modify keyframe animations in the `<style>` section
- **Layout**: Adjust flexbox properties in `.section` class

### Toggle Behavior
Modify the toggle logic in `toggleItems()` function to:
- Add new toggle states
- Change filtering behavior  
- Customize title updates

## Browser Compatibility

- **Modern Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
- **Features Used**: 
  - CSS Grid/Flexbox
  - CSS Animations
  - LocalStorage API
  - ES6 JavaScript

## File Dependencies

- **Standalone**: No external dependencies required
- **Self-Contained**: All CSS and JavaScript embedded
- **Portable**: Single HTML file can be opened anywhere

## Performance Notes

- **Lightweight**: ~25KB total file size
- **Client-Side**: No server requirements
- **Responsive**: Smooth animations at 60fps
- **Memory Efficient**: Minimal DOM manipulation

## Future Enhancement Ideas

### Content Management
- Import/export category configurations
- JSON-based content loading
- Bulk content editing interface
- Community content sharing

### Advanced Features  
- Multi-style support beyond punk/goth
- Weighted randomization options
- Prompt history and favorites
- Integration with ComfyUI API

### UI Improvements
- Dark/light theme toggle
- Accessibility enhancements
- Mobile-optimized layout
- Keyboard shortcuts

## Troubleshooting

### Common Issues

**Toggles Not Working**
- Check browser JavaScript is enabled
- Verify localStorage permissions
- Clear browser cache and reload

**Content Not Showing**
- Verify `data-toggle-*` attributes are correct
- Check for JavaScript console errors
- Ensure proper HTML structure

**Styling Issues**
- Confirm CSS is properly embedded
- Check for conflicting browser extensions
- Test in different browsers

**Copy Function Fails**
- Use modern browser with clipboard API support
- Check site permissions for clipboard access
- Manual selection works as fallback

## Contributing

To contribute improvements:
1. Test changes thoroughly across browsers
2. Maintain the cyberpunk aesthetic
3. Preserve toggle functionality
4. Document any new features added

## License

This prompt builder is part of the SDXL_COMFYUI_CODE project. Check the main repository README for licensing information.
