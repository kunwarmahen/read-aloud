# Read Aloud Chrome Extension 🔊

A powerful Chrome extension that reads webpage content aloud with synchronized word highlighting and Chromecast support.

![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-4285F4?logo=googlechrome)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20Mac-lightgrey)

## ✨ Features

### Core Features

- 🎙️ **Dual TTS Modes**: Browser's Web Speech API or Local TTS Server (eSpeak/Piper)
- 📝 **Flexible Reading**: Read entire page or just selected text
- ✨ **Word Highlighting**: Real-time synchronized word-by-word highlighting
- 📺 **Chromecast Support**: Stream audio to any Chromecast device on your network
- 🎨 **Clean UI**: Minimizable floating panel that stays out of your way

### Playback Controls

- ⏯️ Play, pause, and stop controls
- ⏪⏩ Skip backward/forward by 10 words
- 🔄 Restart from beginning
- 🎚️ Adjustable playback speed (0.5x - 2.0x)
- 🗣️ Multiple voice options (when using Web Speech API)
- 📊 Visual progress bar

### Display Options

- 💡 Toggle between in-panel text display or on-page highlighting
- 🎯 Context-aware display showing current word with surrounding context
- 📱 Responsive design that works on any screen size

## 🚀 Quick Start

### Installation

1. **Clone or Download**

   ```bash
   git clone https://github.com/kunwarmahen/read-aloud.git
   cd read-aloud
   ```

2. **Load Extension in Chrome**

   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right corner)
   - Click "Load unpacked"
   - Select the `read-aloud-extension` folder

3. **Done!** The extension is now active on all webpages.

### Basic Usage

1. **Navigate to any webpage** - the floating 🔊 icon appears in the bottom-right
2. **Click the icon** to expand the control panel
3. **Choose your content**:
   - Click **📄 Full Page** to read entire page
   - Select text with mouse, then click **✂️ Selection** to read only that text
4. **Click ▶️ to start** reading
5. Use playback controls as needed

## 🐧 Linux Setup (Local TTS Server)

The Web Speech API has limited support on Linux. For better experience, use the local TTS server.

### Prerequisites

Install a TTS engine (choose one or both):

**Option A: eSpeak (Lightweight, Fast)**

```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# Fedora
sudo dnf install espeak-ng

# Arch
sudo pacman -S espeak-ng
```

**Option B: Piper (High Quality, Neural TTS)**

```bash
# Download Piper
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz
tar -xzf piper_amd64.tar.gz
sudo mv piper/piper /usr/local/bin/

# Download a voice model
mkdir -p ~/.local/share/piper/models
cd ~/.local/share/piper/models
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### Install Python Dependencies

```bash
cd read-aloud-extension
pip install -r requirements.txt --break-system-packages
```

Or using system packages:

```bash
# Ubuntu/Debian
sudo apt-get install python3-flask python3-flask-cors

# For Chromecast support (optional)
pip install pychromecast --break-system-packages
```

### Start the Server

```bash
python3 combined_server.py
```

The server provides:

- **TTS Synthesis**: `http://localhost:5000/synthesize`
- **Chromecast Control**: `http://localhost:5000/chromecast`

Server output:

```
Read Aloud - Combined TTS & Cast Server
==================================================
eSpeak available: True
Piper available: True
Chromecast available: True

Server starting on http://localhost:5000
==================================================
```

## 📡 Chromecast Setup

### Requirements

- Chromecast device on the same network
- Local TTS server running (`combined_server.py`)
- `pychromecast` installed (see above)

### Usage

1. **Start the server**: `python3 combined_server.py`
2. **In the extension**, click **📡 Setup Cast Device** at the bottom
3. **Select your Chromecast** from the popup window
4. **Button changes to "📡✓ Connected"** when connected
5. **Play your content** - it will stream to the Chromecast
6. **Use pause/resume** - works with Chromecast playback
7. **Click disconnect** to stop casting

### Casting Notes

- ⚠️ Rewind, Forward, and Speed controls are **disabled during casting** (audio is pre-generated)
- ✅ Pause/Resume **works with Chromecast**
- ✅ Word highlighting **continues during casting**
- ⚠️ **Brave Browser users**: Lower Brave Shields for localhost or the cast API will be blocked

## 🎯 Usage Tips

### Reading Selected Text

1. Highlight any text on the page
2. Panel shows "✓ X words selected"
3. Click **✂️ Selection** to load
4. Click **▶️** to start reading

### Display Modes

- **In-Panel Display** (default): Shows text with current word highlighted inside the extension
- **On-Page Highlight**: Check "Highlight on page" to highlight words directly on the webpage

### Keyboard-Free Operation

The extension is designed for hands-free use - once you start playback, it continues automatically until finished or stopped.

## 🛠️ Technical Details

### Architecture

```
┌─────────────────┐
│ Chrome Extension│
│   (content.js)  │
└────────┬────────┘
         │
         ├─── Web Speech API (Windows/Mac)
         │
         └─── Local Server (Linux/All)
              ├─── eSpeak/Piper TTS
              └─── Chromecast Relay
                   └─── Chromecast Device
```

### Files Structure

```
read-aloud-extension/
├── manifest.json          # Extension configuration
├── content.js             # Main extension logic
├── background.js          # Service worker (API proxy)
├── styles.css             # UI styling
├── icon*.png              # Extension icons
├── combined_server.py     # TTS + Cast server
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── INSTALL.md             # Detailed installation guide
```

### Browser Compatibility

| Feature        | Chrome | Edge | Brave      | Safari     |
| -------------- | ------ | ---- | ---------- | ---------- |
| Web Speech API | ✅     | ✅   | ✅         | ⚠️ Limited |
| Local TTS      | ✅     | ✅   | ✅         | ✅         |
| Chromecast     | ✅     | ✅   | ⚠️ Shields | ❌         |

## 🐛 Troubleshooting

### Extension doesn't load

- Make sure Developer mode is enabled in `chrome://extensions/`
- Try removing and re-adding the extension

### No audio on Linux

- Verify eSpeak is installed: `which espeak-ng`
- Start the local server: `python3 combined_server.py`
- Click "⚙️ Setup TTS Server" in the extension if needed

### Chromecast not working

- Ensure `pychromecast` is installed
- Check that Chromecast is on the same network
- Start `combined_server.py` and check console for "Chromecast available: True"
- Brave users: Lower Shields for localhost

### Cast button not showing

- The button appears only when the server is running
- Check server logs for errors
- Visit `http://localhost:5000/chromecast` to verify server is accessible

### Casting continues after stop

- This is normal - the current audio chunk finishes playing
- The next chunk won't start

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Make your changes
3. Test thoroughly with both Web Speech API and local server
4. Submit a PR with a clear description

## 📄 License

MIT License - feel free to use this project for any purpose.

## 🙏 Acknowledgments

- [eSpeak NG](https://github.com/espeak-ng/espeak-ng) - Open source speech synthesizer
- [Piper](https://github.com/rhasspy/piper) - Neural text-to-speech
- [pychromecast](https://github.com/home-assistant-libs/pychromecast) - Python Chromecast library
- [Flask](https://flask.palletsprojects.com/) - Web framework for the server

## 📬 Contact

For bugs, features, or questions, please [open an issue](https://github.com/kunwarmahen/read-aloud/issues).

---

**Made with ❤️ for accessibility and convenience**
