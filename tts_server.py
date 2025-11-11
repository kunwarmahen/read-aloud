#!/usr/bin/env python3
"""
Local TTS Server for Read Aloud Extension
Supports eSpeak and Piper TTS engines
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import tempfile
import os
import shutil
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Check which TTS engines are available
ESPEAK_AVAILABLE = shutil.which('espeak') or shutil.which('espeak-ng')
PIPER_AVAILABLE = shutil.which('piper')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'engines': {
            'espeak': ESPEAK_AVAILABLE is not None,
            'piper': PIPER_AVAILABLE is not None
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

if __name__ == '__main__':
    print("Read Aloud TTS Server")
    print("=" * 50)
    print(f"eSpeak available: {ESPEAK_AVAILABLE is not None}")
    print(f"Piper available: {PIPER_AVAILABLE is not None}")
    print("\nStarting server on http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
