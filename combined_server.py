#!/usr/bin/env python3
"""
Combined TTS and Cast Server for Read Aloud Extension
Supports eSpeak, Piper TTS engines and Chromecast casting
"""

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import subprocess
import tempfile
import os
import shutil
from pathlib import Path
import threading
import time
import traceback
from uuid import UUID

app = Flask(__name__)
CORS(app)

# Check which TTS engines are available
ESPEAK_AVAILABLE = shutil.which('espeak') or shutil.which('espeak-ng')
PIPER_AVAILABLE = shutil.which('piper')

# Chromecast globals
chromecasts = {}
current_cast = None
scan_thread = None
scanning = False
PYCHROMECAST_AVAILABLE = False

# Try to import pychromecast
try:
    import pychromecast
    PYCHROMECAST_AVAILABLE = True
except ImportError:
    print("Warning: pychromecast not installed. Cast functionality disabled.")
    print("Install with: pip install pychromecast")

CAST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cast Device Setup</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 40px;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
        }
        h2 { 
            color: #667eea; 
            margin-top: 0;
        }
        .device { 
            padding: 15px; 
            margin: 10px 0; 
            border: 2px solid #e0e0e0; 
            border-radius: 8px;
            cursor: pointer; 
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .device:hover { 
            background: #f5f5ff; 
            border-color: #667eea;
            transform: translateY(-2px);
        }
        .device-icon {
            font-size: 24px;
        }
        .device-info {
            flex: 1;
        }
        .device-name {
            font-weight: 600;
            color: #333;
        }
        .device-model {
            font-size: 12px;
            color: #999;
        }
        .status {
            text-align: center;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .status.info {
            background: #e3f2fd;
            color: #1976d2;
        }
        .status.success {
            background: #c8e6c9;
            color: #2e7d32;
        }
        .loading {
            text-align: center;
            color: #999;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔊 Cast Device Setup</h2>
        <div id="status" class="status info">Scanning for devices...</div>
        <div id="devices" class="loading">Looking for Chromecasts on your network...</div>
    </div>
    <script>
        // Fetch devices from backend
        function updateDevices() {
            fetch('/api/cast/devices')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('devices');
                    if (data.devices.length === 0) {
                        container.innerHTML = '<div class="loading">No devices found. Make sure your Chromecast is on the same network.</div>';
                    } else {
                        container.innerHTML = data.devices.map(d => 
                            `<div class="device" onclick="connect('${d.uuid}')">
                                <div class="device-icon">📡</div>
                                <div class="device-info">
                                    <div class="device-name">${d.name}</div>
                                    <div class="device-model">${d.model} - ${d.host}</div>
                                </div>
                            </div>`
                        ).join('');
                    }
                });
        }

        function connect(uuid) {
            document.getElementById('status').textContent = 'Connecting...';
            fetch('/api/cast/connect', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({uuid: uuid})
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    document.getElementById('status').className = 'status success';
                    document.getElementById('status').textContent = '✓ Connected to ' + data.device + '! You can close this window.';
                } else {
                    document.getElementById('status').className = 'status info';
                    document.getElementById('status').textContent = 'Connection failed. Try again.';
                }
            });
        }

        // Update devices every 5 seconds
        updateDevices();
        setInterval(updateDevices, 5000);
    </script>
</body>
</html>
"""

# ============================================================================
# TTS FUNCTIONS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'engines': {
            'espeak': ESPEAK_AVAILABLE is not None,
            'piper': PIPER_AVAILABLE is not None,
            'chromecast': PYCHROMECAST_AVAILABLE
        }
    })

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """
    Synthesize text to speech
    Body: {
        "text": "text to speak",
        "engine": "espeak" or "piper" (optional, defaults to best available),
        "rate": 1.0 (speed multiplier, optional),
        "voice": "voice name" (optional)
    }
    """
    data = request.json
    text = data.get('text', '')
    engine = data.get('engine', 'auto')
    rate = data.get('rate', 1.0)
    voice = data.get('voice', None)
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Auto-select best available engine
    if engine == 'auto':
        engine = 'piper' if PIPER_AVAILABLE else 'espeak'
    
    try:
        if engine == 'espeak':
            audio_file = synthesize_espeak(text, rate, voice)
        elif engine == 'piper':
            audio_file = synthesize_piper(text, rate, voice)
        else:
            return jsonify({'error': f'Unknown engine: {engine}'}), 400
        
        return send_file(audio_file, mimetype='audio/wav')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def synthesize_espeak(text, rate=1.0, voice=None):
    """Synthesize using eSpeak"""
    if not ESPEAK_AVAILABLE:
        raise Exception('eSpeak not installed')
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()
    
    # Build command
    espeak_cmd = ESPEAK_AVAILABLE
    cmd = [espeak_cmd, '-w', temp_file.name]
    
    # Adjust speed (eSpeak uses words per minute, default ~175)
    speed = int(175 * rate)
    cmd.extend(['-s', str(speed)])
    
    # Set voice if provided
    if voice:
        cmd.extend(['-v', voice])
    
    cmd.append(text)
    
    # Run eSpeak
    subprocess.run(cmd, check=True, capture_output=True)
    
    return temp_file.name

def synthesize_piper(text, rate=1.0, voice=None):
    """Synthesize using Piper"""
    if not PIPER_AVAILABLE:
        raise Exception('Piper not installed')
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.close()
    
    # Build command
    cmd = ['piper', '-f', temp_file.name]
    
    # Set voice model if provided
    if voice:
        cmd.extend(['--model', voice])
    else:
        cmd.extend(['--model', 'en_US-lessac-medium'])  # use default
    
    # Piper reads from stdin
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    stdout, stderr = process.communicate(input=text.encode('utf-8'))
    
    if process.returncode != 0:
        raise Exception(f'Piper failed: {stderr.decode()}')
    
    return temp_file.name

@app.route('/voices', methods=['GET'])
def list_voices():
    """List available voices"""
    engine = request.args.get('engine', 'auto')
    
    if engine == 'auto':
        engine = 'piper' if PIPER_AVAILABLE else 'espeak'
    
    try:
        if engine == 'espeak':
            voices = get_espeak_voices()
        elif engine == 'piper':
            voices = get_piper_voices()
        else:
            return jsonify({'error': f'Unknown engine: {engine}'}), 400
        
        return jsonify({'engine': engine, 'voices': voices})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_espeak_voices():
    """Get list of eSpeak voices"""
    if not ESPEAK_AVAILABLE:
        return []
    
    result = subprocess.run(
        [ESPEAK_AVAILABLE, '--voices'],
        capture_output=True,
        text=True
    )
    
    voices = []
    for line in result.stdout.split('\n')[1:]:  # Skip header
        if line.strip():
            parts = line.split()
            if len(parts) >= 4:
                voices.append({
                    'name': parts[3],
                    'language': parts[1]
                })
    
    return voices

def get_piper_voices():
    """Get list of Piper voices (from models directory)"""
    # Look for piper models in common locations
    model_dirs = [
        Path.home() / '.local/share/piper/models',
        Path('/usr/share/piper/models'),
        Path('/usr/local/share/piper/models')
    ]
    
    voices = []
    for model_dir in model_dirs:
        if model_dir.exists():
            for model_file in model_dir.glob('**/*.onnx'):
                voices.append({
                    'name': model_file.stem,
                    'path': str(model_file)
                })
    
    return voices

# ============================================================================
# CHROMECAST FUNCTIONS
# ============================================================================

def discover_chromecasts():
    """Background thread to discover Chromecasts"""
    global chromecasts, scanning
    
    if not PYCHROMECAST_AVAILABLE:
        return
    
    scanning = True
    while scanning:
        try:
            services, browser = pychromecast.discovery.discover_chromecasts()
            pychromecast.discovery.stop_discovery(browser)
            
            chromecasts = {}
            for service in services:
                # cc = pychromecast.get_chromecast_from_service(service, browser)
                chromecasts[service.uuid] = {
                    # 'device': cc,
                    'uuid': service.uuid,
                    'name': service.friendly_name,
                    'model': service.model_name,
                    'host': service.host,
                    'port': service.port
                }
            
            time.sleep(10)  # Re-scan every 10 seconds
        except Exception as e:
            print(f"Discovery error: {e}")
            time.sleep(5)

@app.route('/cast')
def cast_page():
    """Serve the cast selection page"""
    if not PYCHROMECAST_AVAILABLE:
        return "Chromecast support not available. Install pychromecast: pip install pychromecast", 503
    return render_template_string(CAST_PAGE)

@app.route('/api/cast/devices', methods=['GET'])
def get_cast_devices():
    """Return list of discovered Chromecasts"""
    if not PYCHROMECAST_AVAILABLE:
        return jsonify({'devices': [], 'error': 'pychromecast not installed'}), 503
    
    devices = [
        {
            'uuid': info['uuid'],
            'name': info['name'],
            'model': info['model'],
            'host': info['host']
        }
        for info in chromecasts.values()
    ]
    return jsonify({'devices': devices})

@app.route('/api/cast/connect', methods=['POST'])
def connect_cast_device():
    """Connect to a specific Chromecast"""
    global current_cast
    
    if not PYCHROMECAST_AVAILABLE:
        return jsonify({'error': 'pychromecast not installed'}), 503
    
    data = request.json
    uuid_str = data.get('uuid')
    uuid = UUID(uuid_str)

    
    if uuid not in chromecasts:
        return jsonify({'error': 'Device not found'}), 404
    
    try:
        current_cast = pychromecast.get_chromecast_from_host((chromecasts[uuid]['host'], 
                                                              chromecasts[uuid]['port'], chromecasts[uuid]['uuid'], 
                                                              chromecasts[uuid]['model'], chromecasts[uuid]['name']))                
        # current_cast = chromecasts[uuid]['device']
        current_cast.wait()
        return jsonify({'success': True, 'device': chromecasts[uuid]['name']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get your local IP address instead of localhost
def get_local_ip():
    """Get the local IP address of this machine"""
    import socket
    try:
        # Create a socket and connect to an external address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"
    
@app.route('/api/cast/cast_data', methods=['POST'])
def cast_audio_data():
    """Cast audio data to the connected device"""
    global current_cast
    
    if not PYCHROMECAST_AVAILABLE:
        return jsonify({'error': 'pychromecast not installed'}), 503
    
    if not current_cast:
        return jsonify({'error': 'No device connected'}), 400
    
    try:
        # Get audio data from request
        files = request.files
        if 'audio' not in files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = files['audio']
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        audio_file.save(temp_file.name)
        temp_file.close()
        
        # Serve the file via this server
        local_ip = get_local_ip()
        audio_url = f"http://{local_ip}:5000/serve_cast_audio/{os.path.basename(temp_file.name)}"
        
        # Store temp file path for serving
        app.config[os.path.basename(temp_file.name)] = temp_file.name
        
        # Get media controller
        mc = current_cast.media_controller
        
        # Play the audio
        mc.play_media(audio_url, 'audio/wav')
        mc.block_until_active()
        
        return jsonify({'success': True})
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/serve_cast_audio/<filename>')
def serve_cast_audio(filename):
    """Serve temporary audio file for casting"""
    if filename not in app.config:
        return "File not found", 404
    
    file_path = app.config[filename]
    return send_file(file_path, mimetype='audio/wav')

@app.route('/api/cast/status', methods=['GET'])
def get_cast_status():
    """Get current casting status"""
    if not PYCHROMECAST_AVAILABLE:
        return jsonify({'connected': False, 'error': 'pychromecast not installed'})
    
    if not current_cast:
        return jsonify({'connected': False})
    
    try:
        mc = current_cast.media_controller
        status = {
            'connected': True,
            'device': current_cast.name,
            'playing': mc.status.player_state == 'PLAYING',
            'paused': mc.status.player_state == 'PAUSED',
        }
        return jsonify(status)
    except:
        return jsonify({'connected': False})

@app.route('/api/cast/control', methods=['POST'])
def control_cast_playback():
    """Control playback (play/pause/stop)"""
    global current_cast
    
    if not PYCHROMECAST_AVAILABLE:
        return jsonify({'error': 'pychromecast not installed'}), 503
    
    if not current_cast:
        return jsonify({'error': 'No device connected'}), 400
    
    try:
        data = request.json
        action = data.get('action')
        
        mc = current_cast.media_controller
        
        if action == 'play':
            mc.play()
        elif action == 'pause':
            mc.pause()
        elif action == 'stop':
            mc.stop()
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cast/disconnect', methods=['POST'])
def disconnect_cast():
    """Disconnect from current device"""
    global current_cast
    
    if not PYCHROMECAST_AVAILABLE:
        return jsonify({'error': 'pychromecast not installed'}), 503
    
    if current_cast:
        try:
            current_cast.quit_app()
        except:
            pass
        current_cast = None
    
    return jsonify({'success': True})

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("Read Aloud - Combined TTS & Cast Server")
    print("=" * 50)
    print(f"eSpeak available: {ESPEAK_AVAILABLE is not None}")
    print(f"Piper available: {PIPER_AVAILABLE is not None}")
    print(f"Chromecast available: {PYCHROMECAST_AVAILABLE}")
    
    if PYCHROMECAST_AVAILABLE:
        print("\nStarting Chromecast discovery...")
        scan_thread = threading.Thread(target=discover_chromecasts, daemon=True)
        scan_thread.start()
    else:
        print("\nChromecast support disabled (pychromecast not installed)")
    
    print("\nServer starting on http://localhost:5000")
    print("TTS API: http://localhost:5000/synthesize")
    if PYCHROMECAST_AVAILABLE:
        print("Cast Setup: http://localhost:5000/cast")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        scanning = False
