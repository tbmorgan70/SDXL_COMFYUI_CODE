# Technical Reference - Prompt Builders

## 🏗️ Architecture Overview

### File Structure
```
builder/
├── README.md                           # Main documentation
├── usage_guide.md                     # User guide
├── technical_reference.md             # This file
├── prompt_elements_dashboard.html     # Comprehensive reference
├── hd_wallpaper_legacy.html           # Abstract wallpaper builder
├── nova_skyrift.html                  # Character portrait builder
├── ultra_*.html                       # Enhanced builders
├── 1girl_*.html                       # Character-focused builders
└── [other specialized builders]
```

### Technology Stack
- **Frontend**: Pure HTML5, CSS3, ES6 JavaScript
- **Dependencies**: None (fully self-contained)
- **Compatibility**: All modern browsers
- **Responsive**: Mobile and desktop optimized

## 🔧 Code Architecture

### Core Components

#### 1. HTML Structure
```html
<!DOCTYPE html>
<html>
<head>
  <!-- Documentation header -->
  <!-- Styling -->
</head>
<body>
  <!-- Category sections -->
  <!-- Control interface -->
  <!-- Output area -->
  <!-- JavaScript logic -->
</body>
</html>
```

#### 2. CSS Framework
- Dark theme implementation
- Responsive grid layouts
- Hover states and transitions
- Mobile-first design principles

#### 3. JavaScript Pattern
```javascript
// State management
const sel = {category1:'', category2:'', category3:''};

// Element selection
function pick(category, element) {
  // Update selection state
  // Update UI highlighting
  // Regenerate prompt
}

// Utility functions
function randomize() { /* Random selection */ }
function copyPrompt() { /* Clipboard operations */ }
function updatePrompt() { /* Prompt assembly */ }
```

## 📊 Builder Types & Patterns

### Legacy Builders
**Pattern**: Simple 4-category structure
```javascript
// Categories: intro, colors, style, scene
const sel = {intro:'', colors:'', style:'', scene:''};
const suffix = 'quality tags here';
```

**Features**:
- Proven stable codebase
- Minimal resource usage
- Fast loading
- Simple maintenance

### ULTRA Builders
**Pattern**: Enhanced multi-category structure
```javascript
// Extended categories with more options
const sel = {
  race:'', body:'', hair:'', clothing:'',
  makeup:'', accessories:'', background:'',
  pose:'', mood:''
};
```

**Features**:
- Extended customization
- Advanced UI components
- Enhanced styling
- Feature toggles

### Dashboard Pattern
**Pattern**: Reference and educational tool
```javascript
// Category expansion/collapse
function toggleCategory(categoryId) {
  // Accordion-style interface
  // Content visibility management
}

// Individual element copying
function copyElement(text) {
  // Single element clipboard operations
}
```

## 🎨 Styling System

### CSS Variables
```css
:root {
  --bg-primary: #111;
  --bg-secondary: #222;
  --text-primary: #eee;
  --text-secondary: #ccc;
  --accent-color: #ffdd57;
  --hover-color: #444;
}
```

### Responsive Breakpoints
```css
/* Mobile First */
.section { width: 100%; }

/* Tablet */
@media (min-width: 768px) {
  .section { width: 48%; }
}

/* Desktop */
@media (min-width: 1024px) {
  .section { width: 23%; }
}
```

### Component Classes
- `.section`: Category containers
- `.category`: Dashboard-style sections
- `.category-header`: Collapsible headers
- `.category-content`: Expandable content
- `#promptBox`: Output text area
- `.copy-btn`: Action buttons

## 🔧 JavaScript Functionality

### State Management
```javascript
// Global state object
const sel = {};

// State update pattern
function pick(category, element) {
  // Clear previous selection highlighting
  document.querySelectorAll(`#${category} li`)
    .forEach(li => li.style.background = '#222');
  
  // Update state
  sel[category] = element.textContent;
  
  // Highlight current selection
  element.style.background = '#444';
  
  // Regenerate prompt
  updatePrompt();
}
```

### Prompt Assembly
```javascript
function updatePrompt() {
  let prompt = Object.values(sel)
    .filter(val => val) // Remove empty values
    .join(', ');
  
  if (suffix) prompt += ', ' + suffix;
  
  document.getElementById('promptBox').value = prompt;
}
```

### Utility Functions
```javascript
// Randomization
function randomize() {
  Object.keys(sel).forEach(category => {
    const items = document.querySelectorAll(`#${category} li`);
    const randomItem = items[Math.floor(Math.random() * items.length)];
    pick(category, randomItem);
  });
}

// Clipboard operations
async function copyPrompt() {
  try {
    await navigator.clipboard.writeText(
      document.getElementById('promptBox').value
    );
    // Success feedback
  } catch (err) {
    // Fallback method
    document.getElementById('promptBox').select();
    document.execCommand('copy');
  }
}
```

## 🔒 Content Management

### NSFW Toggle Implementation
```javascript
// Toggle state
let nsfwMode = false;

// Toggle function
function toggleNSFW() {
  nsfwMode = !nsfwMode;
  
  // Show/hide NSFW content
  document.querySelectorAll('.nsfw-content')
    .forEach(el => {
      el.style.display = nsfwMode ? 'block' : 'none';
    });
}
```

### Content Categorization
```html
<!-- SFW Content -->
<li onclick="pick('category', this)">safe content</li>

<!-- NSFW Content -->
<li class="nsfw-content" onclick="pick('category', this)" style="display:none;">
  adult content
</li>
```

## 📱 Mobile Optimization

### Responsive Design Patterns
```css
/* Mobile stack layout */
@media (max-width: 767px) {
  .section {
    width: 100%;
    margin-bottom: 20px;
  }
  
  #promptBox {
    height: 80px; /* Smaller on mobile */
  }
}
```

### Touch Interactions
```css
/* Enhanced touch targets */
li {
  min-height: 44px; /* iOS recommendation */
  display: flex;
  align-items: center;
}

/* Touch feedback */
li:active {
  background: #555 !important;
}
```

## 🔧 Customization Guide

### Adding New Categories
1. **HTML Structure**:
```html
<div class="section" id="newCategory">
  <h3>New Category</h3>
  <ul>
    <li onclick="pick('newCategory', this)">Option 1</li>
    <li onclick="pick('newCategory', this)">Option 2</li>
  </ul>
</div>
```

2. **JavaScript State**:
```javascript
const sel = {
  // ...existing categories...
  newCategory: ''
};
```

### Modifying Styling
```css
/* Custom theme example */
:root {
  --bg-primary: #your-color;
  --accent-color: #your-accent;
}

/* Custom category styling */
.section.special {
  border: 2px solid var(--accent-color);
}
```

### Adding New Features
```javascript
// Example: Save favorites
function saveFavorite() {
  const currentPrompt = document.getElementById('promptBox').value;
  localStorage.setItem('favoritePrompt', currentPrompt);
}

function loadFavorite() {
  const saved = localStorage.getItem('favoritePrompt');
  if (saved) {
    document.getElementById('promptBox').value = saved;
  }
}
```

## 🧪 Testing & Debugging

### Browser Console Testing
```javascript
// Test state management
console.log(sel);

// Test prompt generation
updatePrompt();
console.log(document.getElementById('promptBox').value);

// Test randomization
randomize();
```

### Common Issues & Solutions

#### 1. Clipboard Not Working
```javascript
// Fallback for older browsers
function copyPromptFallback() {
  const textArea = document.getElementById('promptBox');
  textArea.select();
  textArea.setSelectionRange(0, 99999); // Mobile
  
  try {
    document.execCommand('copy');
    return true;
  } catch (err) {
    console.error('Copy failed:', err);
    return false;
  }
}
```

#### 2. Mobile Layout Issues
```css
/* Ensure proper mobile viewport */
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">

/* Prevent zoom on input focus */
input, textarea {
  font-size: 16px; /* Prevents iOS zoom */
}
```

## 📈 Performance Optimization

### Loading Optimization
- Inline CSS/JS (no external requests)
- Minimal DOM manipulation
- Efficient event handling
- Lazy loading for large lists

### Memory Management
```javascript
// Efficient DOM queries
const promptBox = document.getElementById('promptBox');
const categoryElements = document.querySelectorAll('.section');

// Avoid repeated queries in loops
```

## 🔐 Security Considerations

### Input Sanitization
```javascript
// Sanitize user input if allowing custom elements
function sanitizeInput(input) {
  return input
    .replace(/[<>]/g, '') // Remove HTML brackets
    .trim()
    .substring(0, 200); // Limit length
}
```

### Content Security
- No external scripts or resources
- Static content only
- Client-side operation only
- No data transmission

## 📋 Maintenance Checklist

### Regular Updates
- [ ] Test in latest browser versions
- [ ] Validate HTML/CSS
- [ ] Check mobile responsiveness
- [ ] Update prompt elements for relevance
- [ ] Review and update documentation

### Code Quality
- [ ] Consistent naming conventions
- [ ] Proper commenting
- [ ] Error handling
- [ ] Performance monitoring

---

*This technical reference provides the foundation for understanding, maintaining, and extending the prompt builder collection.*
