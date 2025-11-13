// Background service worker for Read Aloud extension

const TTS_SERVER_URL = "http://localhost:5000";

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "checkTTS") {
    checkTTSServer().then(sendResponse);
    return true; // Keep channel open for async response
  }

  if (request.action === "synthesize") {
    synthesizeSpeech(request.text, request.rate).then(sendResponse);
    return true;
  }

  // Add cast status check
  if (request.action === "castStatus") {
    checkCastStatus().then(sendResponse);
    return true;
  }

  // Add cast audio
  if (request.action === "castAudio") {
    castAudioData(request.audioData).then(sendResponse);
    return true;
  }

  // Add cast disconnect
  if (request.action === "castDisconnect") {
    disconnectCast().then(sendResponse);
    return true;
  }

  // Add cast stop
  if (request.action === "castStop") {
    stopCast().then(sendResponse);
    return true;
  }

  // Add cast control
  if (request.action === "castControl") {
    controlCast(request.control).then(sendResponse);
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
    return { success: false, error: "Server not responding" };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function synthesizeSpeech(text, rate = 1.0) {
  try {
    const response = await fetch(`${TTS_SERVER_URL}/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: text,
        rate: rate,
        engine: "auto",
      }),
    });

    if (!response.ok) {
      return {
        success: false,
        error: "TTS server error: " + response.statusText,
      };
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
async function checkCastStatus() {
  try {
    const response = await fetch("http://localhost:5000/api/cast/status");
    if (response.ok) {
      return await response.json();
    }
    return { connected: false };
  } catch (error) {
    return { connected: false, error: error.message };
  }
}

async function castAudioData(audioDataArray) {
  try {
    // Convert array back to blob
    const blob = new Blob([new Uint8Array(audioDataArray)], {
      type: "audio/wav",
    });

    const formData = new FormData();
    formData.append("audio", blob, "audio.wav");

    const response = await fetch("http://localhost:5000/api/cast/cast_data", {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      return { success: true };
    }
    return { success: false, error: "Cast failed" };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function disconnectCast() {
  try {
    const response = await fetch("http://localhost:5000/api/cast/disconnect", {
      method: "POST",
    });
    return { success: response.ok };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function stopCast() {
  try {
    const response = await fetch("http://localhost:5000/api/cast/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "stop" }),
    });
    return { success: response.ok };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function controlCast(action) {
  try {
    const response = await fetch("http://localhost:5000/api/cast/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: action }),
    });
    return { success: response.ok };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

chrome.runtime.onInstalled.addListener(() => {
  console.log("Read Aloud extension installed");
});
