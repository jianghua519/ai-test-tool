document.addEventListener('DOMContentLoaded', async () => {
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const statusText = document.getElementById('statusText');
  const statusBox = document.getElementById('statusBox');
  const serverUrlInput = document.getElementById('serverUrl');

  // Load state
  const { recording, serverUrl } = await chrome.storage.local.get(['recording', 'serverUrl']);
  
  if (serverUrl) {
    serverUrlInput.value = serverUrl;
  }

  updateUI(recording);

  startBtn.addEventListener('click', async () => {
    const url = serverUrlInput.value;
    await chrome.storage.local.set({ serverUrl: url, recording: true, actions: [] });
    
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Inject content script if not already injected
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    });
    
    // Send message to content script
    chrome.tabs.sendMessage(tab.id, { type: 'START_RECORDING' });
    
    updateUI(true);
  });

  stopBtn.addEventListener('click', async () => {
    await chrome.storage.local.set({ recording: false });
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.tabs.sendMessage(tab.id, { type: 'STOP_RECORDING' });
    
    // Get recorded actions
    const { actions, serverUrl } = await chrome.storage.local.get(['actions', 'serverUrl']);
    
    if (actions && actions.length > 0) {
      statusText.textContent = `Saving ${actions.length} actions...`;
      
      try {
        // Send to backend
        const response = await fetch(`${serverUrl}/api/cases/recordings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: Date.now().toString(),
            url: tab.url,
            actions: actions
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          // Trigger AI generation
          await fetch(`${serverUrl}/api/cases/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: data.session_id })
          });
          
          statusText.textContent = 'Saved & AI Generation started!';
          setTimeout(() => updateUI(false), 2000);
        } else {
          statusText.textContent = 'Error saving recording';
        }
      } catch (error) {
        statusText.textContent = 'Connection error';
        console.error(error);
      }
    } else {
      statusText.textContent = 'No actions recorded';
      updateUI(false);
    }
  });

  function updateUI(isRecording) {
    if (isRecording) {
      startBtn.style.display = 'none';
      stopBtn.style.display = 'block';
      statusBox.classList.add('recording');
      statusText.textContent = 'Recording...';
    } else {
      startBtn.style.display = 'block';
      stopBtn.style.display = 'none';
      statusBox.classList.remove('recording');
      statusText.textContent = 'Ready to record';
    }
  }
});
