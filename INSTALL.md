# Installation Guide for Read Aloud Extension (Local TTS)

This extension uses local text-to-speech engines instead of the Web Speech API, making it work on Linux.

## Prerequisites

### 1. Install a TTS Engine

Choose **one or both**:

#### Option A: eSpeak (Lightweight, Fast)
```bash
# Ubuntu/Debian
sudo apt-get install espeak-ng

# Fedora
sudo dnf install espeak-ng

# Arch
sudo pacman -S espeak-ng
```

#### Option B: Piper (High Quality, Neural TTS)
```bash
# Download Piper
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz
tar -xzf piper_amd64.tar.gz
sudo mv piper/piper /usr/local/bin/

# Download a voice model (example: en_US)
mkdir -p ~/.local/share/piper/models
cd ~/.local/share/piper/models
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### 2. Install Python Dependencies

```bash
cd read-aloud-extension
pip install -r requirements.txt
```

Or with system packages:
```bash
# Ubuntu/Debian
sudo apt-get install python3-flask python3-flask-cors

# Fedora
sudo dnf install python3-flask python3-flask-cors
```

## Running the Extension

### 1. Start the TTS Server

```bash
cd read-aloud-extension
python3 tts_server.py
```

You should see:
```
Read Aloud TTS Server
==================================================
eSpeak available: True
Piper available: True

Starting server on http://localhost:5000
==================================================
```

### 2. Install Chrome Extension

1. Open Chrome/Chromium
2. Go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the `read-aloud-extension` folder

### 3. Use the Extension

1. You'll see a 🔊 icon in the bottom-right of pages
2. Click it to expand the panel
3. Click "Full Page" or select text and click "Selection"
4. Click ▶️ to start playback

## Troubleshooting

### TTS Server Not Running
If you see "TTS Server: Not running":
- Make sure you started `tts_server.py`
- Check that nothing else is using port 5000

### No Audio Output
- Check that eSpeak or Piper is installed: `which espeak-ng` or `which piper`
- Test eSpeak: `espeak-ng "Hello world"`
- Check Flask server logs for errors

### CORS Errors
- Make sure flask-cors is installed: `pip install flask-cors`

## Voice Selection

### eSpeak Voices
List available voices:
```bash
espeak-ng --voices
```

### Piper Voices
Download more voices from: https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0

## Running as a Service (Optional)

To auto-start the TTS server on boot, create a systemd service:

```bash
sudo nano /etc/systemd/system/read-aloud-tts.service
```

Add:
```ini
[Unit]
Description=Read Aloud TTS Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/read-aloud-extension
ExecStart=/usr/bin/python3 /path/to/read-aloud-extension/tts_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable read-aloud-tts
sudo systemctl start read-aloud-tts
```

## Performance Tips

- **eSpeak** is faster but sounds more robotic
- **Piper** sounds better but requires more CPU
- Adjust chunk size in `content.js` (currently 50 words) for better performance
- Lower playback speeds work better than higher speeds
