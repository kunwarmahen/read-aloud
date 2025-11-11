// Content script for Read Aloud extension

let currentAudio = null;
let currentUtterance = null;
let currentText = '';
let currentWordIndex = 0;
let words = [];
let isPaused = false;
let isPlaying = false;
let selectedText = '';
let currentHighlight = null;
let highlightInPage = false;
let ttsServerUrl = 'http://localhost:5000';
let playbackRate = 1.0;
let ttsMode = 'web'; // 'web' or 'server'
let webSpeechAvailable = false;

// Create floating panel
function createFloatingPanel() {
  if (document.getElementById('read-aloud-panel')) return;

  const panel = document.createElement('div');
  panel.id = 'read-aloud-panel';
  panel.className = 'collapsed';
  panel.innerHTML = `
    <div class="panel-icon" id="panel-icon" title="Read Aloud">
      🔊
    </div>
    <div class="panel-expanded">
      <div class="panel-header">
        <span class="panel-title">🔊 Read Aloud</span>
        <button id="close-panel" class="close-btn" title="Collapse">✕</button>
      </div>
      <div class="panel-content">
        <div class="tts-mode-section">
          <div class="tts-mode-info" id="tts-mode-info">Checking TTS...</div>
          <div class="server-config" id="server-config" style="display: none;">
            <input type="text" id="server-url-input" value="http://localhost:5000" placeholder="http://localhost:5000" />
            <button id="save-server-btn" class="mini-btn">Save</button>
            <button id="cancel-server-btn" class="mini-btn">Cancel</button>
          </div>
        </div>

        <div class="selection-info" id="selection-info"></div>
        
        <div class="source-buttons">
          <button id="load-page-btn" class="source-btn" title="Load page content">
            <span class="btn-icon">📄</span>
            <span class="btn-text">Full Page</span>
          </button>
          <button id="load-selection-btn" class="source-btn" title="Load selected text" disabled>
            <span class="btn-icon">✂️</span>
            <span class="btn-text">Selection</span>
            <span class="btn-helper">Select text first</span>
          </button>
        </div>

        <div class="highlight-toggle">
          <label>
            <input type="checkbox" id="highlight-toggle" />
            <span class="toggle-label">Highlight on page</span>
          </label>
        </div>

        <div class="text-display" id="text-display">
          <p class="placeholder-text">Select text or click Full Page to load content</p>
        </div>

        <div class="playback-controls">
          <button id="rewind-btn" class="playback-btn" title="Rewind 10 words" disabled>⏪</button>
          <button id="play-pause-btn" class="playback-btn pause-play" title="Play" disabled>▶️</button>
          <button id="stop-btn" class="playback-btn" title="Stop" disabled>⏹️</button>
          <button id="forward-btn" class="playback-btn" title="Forward 10 words" disabled>⏩</button>
          <button id="restart-btn" class="playback-btn" title="Restart" disabled>🔄</button>
        </div>

        <div class="speed-control">
          <label>Speed: <span id="speed-value">1.0</span>x</label>
          <input type="range" id="speed-slider" min="0.5" max="2.0" step="0.1" value="1.0">
        </div>
        <div class="voice-control" id="voice-control-section">
          <label>Voice:</label>
          <select id="voice-select"></select>
        </div>
        <div class="progress-bar">
          <div id="progress-fill"></div>
        </div>
        <div class="status">Ready</div>
        <button id="setup-server-btn" class="mini-btn" style="display: none; margin-top: 8px; width: 100%;">⚙️ Setup TTS Server</button>
      </div>
    </div>
  `;
  document.body.appendChild(panel);

  // Set up event listeners
  setupEventListeners();
  populateVoiceList();
}

function setupEventListeners() {
  const panel = document.getElementById('read-aloud-panel');
  const panelIcon = document.getElementById('panel-icon');
  const closeBtn = document.getElementById('close-panel');
  const loadPageBtn = document.getElementById('load-page-btn');
  const loadSelectionBtn = document.getElementById('load-selection-btn');
  const playPauseBtn = document.getElementById('play-pause-btn');
  const stopBtn = document.getElementById('stop-btn');
  const restartBtn = document.getElementById('restart-btn');
  const rewindBtn = document.getElementById('rewind-btn');
  const forwardBtn = document.getElementById('forward-btn');
  const speedSlider = document.getElementById('speed-slider');
  const speedValue = document.getElementById('speed-value');
  const voiceSelect = document.getElementById('voice-select');
  const highlightToggle = document.getElementById('highlight-toggle');
  const setupServerBtn = document.getElementById('setup-server-btn');
  const saveServerBtn = document.getElementById('save-server-btn');
  const cancelServerBtn = document.getElementById('cancel-server-btn');
  const serverUrlInput = document.getElementById('server-url-input');

  panelIcon.addEventListener('click', () => {
    panel.classList.remove('collapsed');
  });

  closeBtn.addEventListener('click', () => {
    panel.classList.add('collapsed');
  });

  setupServerBtn.addEventListener('click', () => {
    document.getElementById('server-config').style.display = 'flex';
    setupServerBtn.style.display = 'none';
  });

  saveServerBtn.addEventListener('click', async () => {
    ttsServerUrl = serverUrlInput.value;
    await chrome.storage.local.set({ ttsServerUrl });
    document.getElementById('server-config').style.display = 'none';
    setupServerBtn.style.display = 'inline-block';
    checkTTSMode();
  });

  cancelServerBtn.addEventListener('click', () => {
    serverUrlInput.value = ttsServerUrl;
    document.getElementById('server-config').style.display = 'none';
    setupServerBtn.style.display = 'inline-block';
  });

  highlightToggle.addEventListener('change', (e) => {
    highlightInPage = e.target.checked;
    if (words.length > 0) {
      displayTextWithHighlight();
    }
  });

  loadPageBtn.addEventListener('click', () => loadText(false));
  loadSelectionBtn.addEventListener('click', () => loadText(true));
  playPauseBtn.addEventListener('click', togglePlayPause);
  stopBtn.addEventListener('click', stopText);
  restartBtn.addEventListener('click', restartText);
  rewindBtn.addEventListener('click', () => skipWords(-10));
  forwardBtn.addEventListener('click', () => skipWords(10));

  speedSlider.addEventListener('input', (e) => {
    speedValue.textContent = e.target.value;
    playbackRate = parseFloat(e.target.value);
    if (ttsMode === 'server' && currentAudio && isPlaying) {
      currentAudio.playbackRate = playbackRate;
    }
  });

  voiceSelect.addEventListener('change', () => {
    // Voice changing applies on next play
  });

  document.addEventListener('mouseup', handleTextSelection);
  document.addEventListener('keyup', handleTextSelection);
}

function handleTextSelection() {
  const selection = window.getSelection();
  const text = selection.toString().trim();
  const selectionInfo = document.getElementById('selection-info');
  const loadSelectionBtn = document.getElementById('load-selection-btn');
  const btnHelper = loadSelectionBtn.querySelector('.btn-helper');
  
  if (text && text.length > 0) {
    selectedText = text;
    const wordCount = text.split(/\s+/).length;
    selectionInfo.textContent = `✓ ${wordCount} word${wordCount > 1 ? 's' : ''} selected`;
    selectionInfo.style.display = 'block';
    loadSelectionBtn.disabled = false;
    btnHelper.textContent = `${wordCount} words`;
  } else {
    selectedText = '';
    selectionInfo.style.display = 'none';
    if (!isPlaying) {
      loadSelectionBtn.disabled = true;
      btnHelper.textContent = 'Select text first';
    }
  }
}

function populateVoiceList() {
  checkTTSMode();
}

async function checkTTSMode() {
  // Load saved server URL
  const stored = await chrome.storage.local.get(['ttsServerUrl']);
  if (stored.ttsServerUrl) {
    ttsServerUrl = stored.ttsServerUrl;
    document.getElementById('server-url-input').value = ttsServerUrl;
  }

  // First check if Web Speech API is available
  if (window.speechSynthesis) {
    try {
      const voices = speechSynthesis.getVoices();
      if (voices.length > 0) {
        webSpeechAvailable = true;
        ttsMode = 'web';
        populateWebVoices(voices);
        updateTTSModeInfo('Using Web Speech API', true);
        document.getElementById('setup-server-btn').style.display = 'none';
        return;
      }
    } catch (e) {
      console.log('Web Speech API not functional:', e);
    }
  }

  // If Web Speech not available, try TTS server
  try {
    const response = await chrome.runtime.sendMessage({ action: 'checkTTS' });
    if (response.success) {
      ttsMode = 'server';
      updateTTSModeInfo('Using Local TTS Server', true);
      document.getElementById('setup-server-btn').style.display = 'inline-block';
      document.getElementById('voice-control-section').style.display = 'none';
    } else {
      ttsMode = 'none';
      updateTTSModeInfo('TTS not available. Configure server below.', false);
      document.getElementById('setup-server-btn').style.display = 'inline-block';
      document.getElementById('voice-control-section').style.display = 'none';
    }
  } catch (error) {
    ttsMode = 'none';
    updateTTSModeInfo('TTS not available. Configure server below.', false);
    document.getElementById('setup-server-btn').style.display = 'inline-block';
    document.getElementById('voice-control-section').style.display = 'none';
  }
}

function populateWebVoices(voices) {
  const voiceSelect = document.getElementById('voice-select');
  voiceSelect.innerHTML = voices
    .map((voice, index) => 
      `<option value="${index}">${voice.name} (${voice.lang})</option>`)
    .join('');
}

function updateTTSModeInfo(message, success) {
  const modeInfo = document.getElementById('tts-mode-info');
  modeInfo.textContent = message;
  modeInfo.className = 'tts-mode-info ' + (success ? 'success' : 'warning');
}

// Populate voices when they're loaded (for Web Speech API)
if (typeof speechSynthesis !== 'undefined' && speechSynthesis.onvoiceschanged !== undefined) {
  speechSynthesis.onvoiceschanged = () => {
    if (ttsMode === 'web' || ttsMode === 'none') {
      checkTTSMode();
    }
  };
}

function extractPageText() {
  // Get main content, avoiding scripts, styles, etc.
  const body = document.body.cloneNode(true);
  
  // Remove unwanted elements
  const unwanted = body.querySelectorAll('script, style, noscript, iframe, nav, footer, header');
  unwanted.forEach(el => el.remove());

  // Get text content
  const text = body.innerText || body.textContent;
  return text.trim();
}

function updateStatus(message) {
  const status = document.querySelector('.status');
  if (status) status.textContent = message;
}

function updateProgress() {
  const progressFill = document.getElementById('progress-fill');
  if (progressFill && words.length > 0) {
    const percentage = (currentWordIndex / words.length) * 100;
    progressFill.style.width = percentage + '%';
  }
}

function displayTextWithHighlight() {
  const textDisplay = document.getElementById('text-display');
  
  if (highlightInPage) {
    // Hide text display when highlighting on page
    if (textDisplay) {
      textDisplay.style.display = 'none';
    }
    highlightWordOnPage();
  } else {
    // Show text in panel
    if (textDisplay) {
      textDisplay.style.display = 'block';
    }
    removePageHighlights();
    
    if (!textDisplay || words.length === 0) return;

    let html = '';
    const contextBefore = 15;
    const contextAfter = 15;
    
    const startIdx = Math.max(0, currentWordIndex - contextBefore);
    const endIdx = Math.min(words.length, currentWordIndex + contextAfter + 1);
    
    if (startIdx > 0) html += '... ';
    
    for (let i = startIdx; i < endIdx; i++) {
      if (i === currentWordIndex) {
        html += `<span class="current-word">${words[i]}</span> `;
      } else {
        html += words[i] + ' ';
      }
    }
    
    if (endIdx < words.length) html += '...';
    
    textDisplay.innerHTML = `<p>${html}</p>`;
    
    const currentWordEl = textDisplay.querySelector('.current-word');
    if (currentWordEl) {
      currentWordEl.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
    }
  }
}

function highlightWordOnPage() {
  removePageHighlights();
  
  if (currentWordIndex >= words.length) return;
  
  const word = words[currentWordIndex];
  const searchText = word.replace(/[.,!?;:]/g, '');
  
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: function(node) {
        if (node.parentElement.closest('#read-aloud-panel')) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

  let node;
  while (node = walker.nextNode()) {
    const text = node.textContent;
    const regex = new RegExp('\\b' + searchText + '\\b', 'i');
    const match = text.match(regex);
    
    if (match) {
      const index = match.index;
      const before = text.substring(0, index);
      const matchText = text.substring(index, index + match[0].length);
      const after = text.substring(index + match[0].length);

      const highlight = document.createElement('span');
      highlight.className = 'read-aloud-page-highlight';
      highlight.textContent = matchText;

      const parent = node.parentNode;
      parent.replaceChild(document.createTextNode(after), node);
      parent.insertBefore(highlight, parent.firstChild);
      parent.insertBefore(document.createTextNode(before), highlight);
      
      highlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
  }
}

function removePageHighlights() {
  const highlights = document.querySelectorAll('.read-aloud-page-highlight');
  highlights.forEach(highlight => {
    const parent = highlight.parentNode;
    parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
    parent.normalize();
  });
}

function removeHighlights() {
  removePageHighlights();
}

function loadText(useSelection = false) {
  if (useSelection && selectedText) {
    currentText = selectedText;
    updateStatus('Selection loaded');
  } else {
    currentText = extractPageText();
    updateStatus('Page loaded');
  }
  
  if (!currentText) {
    updateStatus('No text found');
    return;
  }

  words = currentText.split(/\s+/).filter(w => w.length > 0);
  currentWordIndex = 0;
  displayTextWithHighlight();
  updateButtons();
  
  // Enable play button
  const playPauseBtn = document.getElementById('play-pause-btn');
  if (playPauseBtn) {
    playPauseBtn.disabled = false;
  }
}

function togglePlayPause() {
  if (!words || words.length === 0) {
    updateStatus('Please load content first');
    return;
  }

  if (isPlaying) {
    if (ttsMode === 'web') {
      if (isPaused) {
        speechSynthesis.resume();
        isPaused = false;
        updateStatus('Playing...');
      } else {
        speechSynthesis.pause();
        isPaused = true;
        updateStatus('Paused');
      }
    } else if (ttsMode === 'server') {
      if (isPaused) {
        if (currentAudio) {
          currentAudio.play();
        }
        isPaused = false;
        updateStatus('Playing...');
      } else {
        if (currentAudio) {
          currentAudio.pause();
        }
        isPaused = true;
        updateStatus('Paused');
      }
    }
    updateButtons();
  } else {
    if (ttsMode === 'web') {
      playWithWebSpeech();
    } else if (ttsMode === 'server') {
      playWithServer();
    } else {
      updateStatus('Please configure TTS server');
    }
  }
}

function playWithWebSpeech() {
  if (currentWordIndex >= words.length) {
    currentWordIndex = words.length;
    displayTextWithHighlight();
    stopText();
    updateStatus('Finished');
    return;
  }

  const textToSpeak = words.slice(currentWordIndex).join(' ');
  
  currentUtterance = new SpeechSynthesisUtterance(textToSpeak);
  
  const voiceSelect = document.getElementById('voice-select');
  const voices = speechSynthesis.getVoices();
  if (voiceSelect.value) {
    currentUtterance.voice = voices[voiceSelect.value];
  }

  const speedSlider = document.getElementById('speed-slider');
  currentUtterance.rate = parseFloat(speedSlider.value);
  currentUtterance.pitch = 1;
  currentUtterance.volume = 1;

  let lastBoundaryTime = Date.now();
  const minBoundaryInterval = 200;
  
  currentUtterance.onboundary = (event) => {
    if (event.name === 'word') {
      const now = Date.now();
      if (now - lastBoundaryTime < minBoundaryInterval) {
        return;
      }
      lastBoundaryTime = now;
      
      currentWordIndex++;
      if (currentWordIndex >= words.length) {
        currentWordIndex = words.length - 1;
      }
      displayTextWithHighlight();
      updateProgress();
    }
  };

  currentUtterance.onend = () => {
    currentWordIndex = words.length;
    displayTextWithHighlight();
    stopText();
    updateStatus('Finished');
  };

  currentUtterance.onerror = (event) => {
    console.error('Speech error:', event);
    updateStatus('Error: ' + event.error);
    stopText();
  };

  speechSynthesis.speak(currentUtterance);
  isPlaying = true;
  isPaused = false;
  updateStatus('Playing...');
  updateButtons();
}

async function playWithServer() {
  if (currentWordIndex >= words.length) {
    currentWordIndex = words.length;
    displayTextWithHighlight();
    stopText();
    updateStatus('Finished');
    return;
  }

  // Get chunk of words to synthesize (avoid too long chunks)
  const chunkSize = 50;
  const endIndex = Math.min(currentWordIndex + chunkSize, words.length);
  const textChunk = words.slice(currentWordIndex, endIndex).join(' ');
  
  try {
    updateStatus('Generating speech...');
    
    const speedSlider = document.getElementById('speed-slider');
    playbackRate = parseFloat(speedSlider.value);
    
    // Request audio from background worker
    const response = await chrome.runtime.sendMessage({
      action: 'synthesize',
      text: textChunk,
      rate: playbackRate
    });
    
    if (!response.success) {
      throw new Error(response.error);
    }
    
    // Create audio from base64 data URL
    currentAudio = new Audio(response.audioData);
    currentAudio.playbackRate = playbackRate;
    
    // Estimate word duration and update highlight
    const wordCount = endIndex - currentWordIndex;
    currentAudio.addEventListener('loadedmetadata', () => {
      const duration = currentAudio.duration;
      const msPerWord = (duration * 1000) / wordCount;
      startWordTracking(msPerWord, wordCount);
    });
    
    currentAudio.addEventListener('ended', () => {
      currentWordIndex = endIndex;
      
      if (currentWordIndex < words.length) {
        playWithServer();
      } else {
        currentWordIndex = words.length;
        displayTextWithHighlight();
        stopText();
        updateStatus('Finished');
      }
    });
    
    currentAudio.addEventListener('error', (e) => {
      console.error('Audio playback error:', e);
      updateStatus('Playback error');
      stopText();
    });
    
    await currentAudio.play();
    isPlaying = true;
    isPaused = false;
    updateStatus('Playing...');
    updateButtons();
    
  } catch (error) {
    console.error('TTS error:', error);
    updateStatus('Error: ' + error.message);
    stopText();
  }
}

function startWordTracking(msPerWord, wordCount) {
  let wordOffset = 0;
  const interval = setInterval(() => {
    if (!isPlaying || isPaused) {
      clearInterval(interval);
      return;
    }
    
    wordOffset++;
    if (wordOffset > wordCount) {
      clearInterval(interval);
      return;
    }
    
    displayTextWithHighlight();
    updateProgress();
    currentWordIndex++;
    
  }, msPerWord);
}

function stopText() {
  if (ttsMode === 'web') {
    speechSynthesis.cancel();
    currentUtterance = null;
  } else if (ttsMode === 'server') {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
  }
  
  removePageHighlights();
  isPlaying = false;
  isPaused = false;
  currentWordIndex = 0;
  
  if (words.length > 0) {
    displayTextWithHighlight();
  } else {
    const textDisplay = document.getElementById('text-display');
    if (textDisplay) {
      textDisplay.style.display = 'block';
      textDisplay.innerHTML = '<p class="placeholder-text">Select text or click Full Page to load content</p>';
    }
  }
  
  updateStatus('Stopped');
  updateButtons();
  updateProgress();
}

function restartText() {
  if (ttsMode === 'web') {
    speechSynthesis.cancel();
    currentUtterance = null;
  } else if (ttsMode === 'server') {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
  }
  
  currentWordIndex = 0;
  isPaused = false;
  isPlaying = false;
  displayTextWithHighlight();
  updateStatus('Ready to play');
  updateButtons();
}

function skipWords(count) {
  const newIndex = Math.max(0, Math.min(currentWordIndex + count, words.length - 1));
  currentWordIndex = newIndex;
  
  if (isPlaying) {
    if (ttsMode === 'web') {
      speechSynthesis.cancel();
      playWithWebSpeech();
    } else if (ttsMode === 'server') {
      if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
      }
      playWithServer();
    }
  } else {
    displayTextWithHighlight();
  }
}

function updateButtons() {
  const loadPageBtn = document.getElementById('load-page-btn');
  const loadSelectionBtn = document.getElementById('load-selection-btn');
  const playPauseBtn = document.getElementById('play-pause-btn');
  const stopBtn = document.getElementById('stop-btn');
  const rewindBtn = document.getElementById('rewind-btn');
  const forwardBtn = document.getElementById('forward-btn');
  const restartBtn = document.getElementById('restart-btn');

  const hasContent = words && words.length > 0;

  if (isPlaying) {
    loadPageBtn.disabled = true;
    loadSelectionBtn.disabled = true;
    playPauseBtn.disabled = false;
    stopBtn.disabled = false;
    rewindBtn.disabled = false;
    forwardBtn.disabled = false;
    restartBtn.disabled = false;
    
    // Update play/pause button
    if (isPaused) {
      playPauseBtn.textContent = '▶️';
      playPauseBtn.title = 'Resume';
    } else {
      playPauseBtn.textContent = '⏸️';
      playPauseBtn.title = 'Pause';
    }
  } else {
    loadPageBtn.disabled = false;
    loadSelectionBtn.disabled = !selectedText;
    playPauseBtn.disabled = !hasContent;
    stopBtn.disabled = !hasContent;
    rewindBtn.disabled = !hasContent;
    forwardBtn.disabled = !hasContent;
    restartBtn.disabled = !hasContent;
    playPauseBtn.textContent = '▶️';
    playPauseBtn.title = 'Play';
  }
}

// Initialize
createFloatingPanel();
