#!/usr/bin/env python3
"""
Cast Relay Server for Read Aloud Extension
Handles Chromecast communication via pychromecast
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import pychromecast
import threading
import time
import tempfile
import os
import traceback
from uuid import UUID

app = Flask(__name__)
CORS(app)

# Global variables
chromecasts = {}
current_cast = None
scan_thread = None
scanning = False

CAST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cast Relay</title>
    <script src="https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .device { padding: 10px; margin: 10px; border: 1px solid #ccc; cursor: pointer; }
        .device:hover { background: #f0f0f0; }
    </style>
</head>
<body>
    <h2>Available Cast Devices</h2>
    <div id="devices"></div>
    <script>
        window['__onGCastApiAvailable'] = function(isAvailable) {
            if (isAvailable) {
                initializeCastApi();
            }
        };

        function initializeCastApi() {
            cast.framework.CastContext.getInstance().setOptions({
                receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
                autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
            });
        }

        // Fetch devices from backend
        setInterval(() => {
            fetch('/api/devices')
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('devices');
                    container.innerHTML = data.devices.map(d => 
                        `<div class="device" onclick="connect('${d.uuid}')">${d.name} (${d.model})</div>`
                    ).join('');
                });
        }, 5000);

        function connect(uuid) {
            fetch('/api/connect', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({uuid: uuid})
            }).then(() => {
                alert('Connected! You can close this window.');
            });
        }
    </script>
</body>
</html>
"""

def discover_chromecasts():
    """Background thread to discover Chromecasts"""
    global chromecasts, scanning
    scanning = True
    while scanning:
        try:
            # 
            services, browser = pychromecast.discovery.discover_chromecasts()
            pychromecast.discovery.stop_discovery(browser)
            
            chromecasts = {}
            for service in services:
                # cc = pychromecast.get_chromecast_from_host((service.host, service.port, service.uuid, service.model_name, service.friendly_name))                
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
            traceback.print_exc()
            print(f"Discovery error: {e}")
            time.sleep(5)

@app.route('/')
def index():
    """Serve the cast selection page"""
    return render_template_string(CAST_PAGE)

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Return list of discovered Chromecasts"""
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

@app.route('/api/connect', methods=['POST'])
def connect_device():
    """Connect to a specific Chromecast"""
    global current_cast
    
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cast', methods=['POST'])
def cast_audio():
    """Cast audio to the connected device"""
    global current_cast
    
    if not current_cast:
        return jsonify({'error': 'No device connected'}), 400
    
    try:
        data = request.json
        audio_url = data.get('url')  # URL to audio file
        
        if not audio_url:
            return jsonify({'error': 'No audio URL provided'}), 400
        
        # Get media controller
        mc = current_cast.media_controller
        
        # Play the audio
        mc.play_media(audio_url, 'audio/wav')
        mc.block_until_active()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cast_data', methods=['POST'])
def cast_audio_data():
    """Cast audio data (base64) to the connected device"""
    global current_cast
    
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
        audio_url = f"http://{request.host}/serve_audio/{os.path.basename(temp_file.name)}"
        
        # Store temp file path for serving
        app.config[os.path.basename(temp_file.name)] = temp_file.name
        
        # Get media controller
        mc = current_cast.media_controller
        
        # Play the audio
        mc.play_media(audio_url, 'audio/wav')
        mc.block_until_active()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/serve_audio/<filename>')
def serve_audio(filename):
    """Serve temporary audio file"""
    from flask import send_file
    
    if filename not in app.config:
        return "File not found", 404
    
    file_path = app.config[filename]
    return send_file(file_path, mimetype='audio/wav')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current casting status"""
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

@app.route('/api/control', methods=['POST'])
def control_playback():
    """Control playback (play/pause/stop)"""
    global current_cast
    
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

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from current device"""
    global current_cast
    
    if current_cast:
        try:
            current_cast.quit_app()
        except:
            pass
        current_cast = None
    
    return jsonify({'success': True})

if __name__ == '__main__':
    print("Cast Relay Server")
    print("=" * 50)
    print("Starting Chromecast discovery...")
    
    # Start discovery thread
    scan_thread = threading.Thread(target=discover_chromecasts, daemon=True)
    scan_thread.start()
    
    print("Server starting on http://localhost:5001")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=False)
    finally:
        scanning = False
