# Read Aloud Chrome Extension

A Chrome extension that reads webpage content aloud with synchronized word highlighting.

## Features

- 🎙️ Text-to-speech using browser's built-in Web Speech API
- 📝 **Read selected text** or entire page
- ✨ Real-time word highlighting as content is read
- ⏯️ Play, pause, and stop controls
- ⏪⏩ Rewind and forward (skip 10 words)
- 🔄 Restart from beginning
- 🎚️ Adjustable playback speed (0.5x - 2.0x)
- 🗣️ Multiple voice options
- 📊 Progress bar
- 🎨 Minimizable floating panel

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the `read-aloud-extension` folder

## Usage

1. The floating panel appears in the bottom-right of every webpage
2. Click the arrow (▼) to expand the panel

### Reading the entire page:

- Click **▶️ Page** to read the full page content

### Reading selected text:

- Select any text on the page with your mouse
- The panel will show "X words selected"
- Click **▶️ Selection** to read only the selected text

### Controls:

- **Pause** (⏸️) - Pause playback
- **Stop** (⏹️) - Stop and reset
- **Restart** (🔄) - Start from beginning
- **Rewind** (⏪) - Skip back 10 words
- **Forward** (⏩) - Skip forward 10 words

Adjust speed and voice as desired. Click the arrow (▲) to minimize the panel.

## Technical Note

This extension uses the **Web Speech API** (native to Chrome) for text-to-speech conversion. No external dependencies or local models are required.

For Linux SpeechSynthesisUtterance does not work. So you can use local server to handle it. Read how to setup [Install](./INSTALL.md).

## Browser Support

- Chrome 33+
- Edge 14+
- Safari 16+ (with limitations)

## Files

- `manifest.json` - Extension configuration
- `content.js` - Main functionality
- `background.js` - Service worker
- `styles.css` - UI styling
- `icon*.png` - Extension icons
