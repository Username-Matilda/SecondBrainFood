// Tab Capture - Popup Logic
// The popup's job: get tab info, accept optional note, send to server, close tab

const CAPTURE_SERVER = 'http://localhost:7777/capture';

// Elements
const titleEl = document.getElementById('pageTitle');
const noteInput = document.getElementById('noteInput');
const errorMessage = document.getElementById('errorMessage');

// State
let currentTab = null;

// On load: get current tab info
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  currentTab = tabs[0];
  titleEl.textContent = currentTab.title || currentTab.url;
});

// Enter key triggers capture
noteInput.addEventListener('keydown', async (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    await captureAndClose();
  }
  if (e.key === 'Escape') {
    window.close();
  }
});

async function captureAndClose() {
  if (!currentTab) return;
  
  const payload = {
    url: currentTab.url,
    title: currentTab.title || '',
    note: noteInput.value.trim(),
    captured_at: new Date().toISOString()
  };
  
  try {
    const response = await fetch(CAPTURE_SERVER, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }
    
    // Success: show confirmation, then close tab
    document.body.classList.add('success');
    
    // Brief pause to show success, then close
    setTimeout(() => {
      chrome.tabs.remove(currentTab.id);
      window.close();
    }, 400);
    
  } catch (err) {
    console.error('Capture failed:', err);
    document.body.classList.add('error');
    errorMessage.textContent = 'Could not connect to capture server. Is it running?';
  }
}
