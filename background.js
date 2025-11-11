// Background service worker for Read Aloud extension

const TTS_SERVER_URL = 'http://localhost:5000';

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'checkTTS') {
    checkTTSServer().then(sendResponse);
    return true; // Keep channel open for async response
  }
  
  if (request.action === 'synthesize') {
    synthesizeSpeech(request.text, request.rate).then(sendResponse);
    return true;
  }
});

async function checkTTSServer() {
  try {
    const response = await fetch(`${TTS_SERVER_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      return { success: true, data };
    }
    return { success: false, error: 'Server not responding' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function synthesizeSpeech(text, rate = 1.0) {
  try {
    const response = await fetch(`${TTS_SERVER_URL}/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        rate: rate,
        engine: 'auto'
      })
    });
    
    if (!response.ok) {
      return { success: false, error: 'TTS server error: ' + response.statusText };
    }
    
    const audioBlob = await response.blob();
    const reader = new FileReader();
    
    return new Promise((resolve) => {
      reader.onloadend = () => {
        resolve({ success: true, audioData: reader.result });
      };
      reader.readAsDataURL(audioBlob);
    });
    
  } catch (error) {
    return { success: false, error: error.message };
  }
}

chrome.runtime.onInstalled.addListener(() => {
  console.log('Read Aloud extension installed');
});
