# Cast Setup - Simplified Single Server

## 1. Install pychromecast (optional, for Cast support)

```bash
pip install pychromecast --break-system-packages
```

## 2. Update content.js - Change castServerUrl

Find line 13 (around):
```javascript
let castServerUrl = 'http://localhost:5001';
```

Change to:
```javascript
let castServerUrl = 'http://localhost:5000';
```

## 3. Update openCastSetup() function

Find the `openCastSetup()` function and change:
```javascript
function openCastSetup() {
  // Open cast relay page in new tab
  window.open(`${castServerUrl}/`, 'castsetup', 'width=600,height=400');
```

To:
```javascript
function openCastSetup() {
  // Open cast relay page in new tab
  window.open(`${castServerUrl}/cast`, 'castsetup', 'width=600,height=400');
```

## 4. Start the Combined Server

```bash
python3 combined_server.py
```

This single server now handles:
- TTS synthesis (port 5000)
- Chromecast discovery and control (port 5000)

## Usage:

1. Start the server: `python3 combined_server.py`
2. Load your extension
3. Click "📡 Setup Cast Device" 
4. Select your Chromecast from the popup window
5. Play audio - it will stream to your Chromecast

## Benefits of Combined Server:

- ✅ Single server to run (not two)
- ✅ Single port (5000)
- ✅ Simpler configuration
- ✅ All functionality in one place
