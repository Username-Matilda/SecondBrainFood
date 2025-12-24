// Tab Capture - Popup Logic
// Captures URL, title, note, AND page content at source

const CAPTURE_SERVER = 'http://localhost:7777/capture';

const titleEl = document.getElementById('pageTitle');
const noteInput = document.getElementById('noteInput');
const errorMessage = document.getElementById('errorMessage');

let currentTab = null;

// On load: get current tab info
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  currentTab = tabs[0];
  titleEl.textContent = currentTab.title || currentTab.url;
});

noteInput.addEventListener('keydown', async (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    await captureAndClose();
  }
  if (e.key === 'Escape') {
    window.close();
  }
});

// Extract readable content from page
async function extractPageContent(tabId) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        // Try to get article/main content first, fall back to body
        const selectors = [
          'article',
          '[role="main"]',
          'main',
          '.post-content',
          '.entry-content',
          '.article-content',
          '#content',
          '.content'
        ];
        
        let contentEl = null;
        for (const sel of selectors) {
          contentEl = document.querySelector(sel);
          if (contentEl && contentEl.innerText.trim().length > 200) break;
        }
        
        // Fall back to body, excluding nav/footer/sidebar noise
        if (!contentEl || contentEl.innerText.trim().length < 200) {
          // Clone body and remove noise
          const clone = document.body.cloneNode(true);
          const noise = clone.querySelectorAll('nav, footer, aside, header, script, style, noscript, [role="navigation"], [role="banner"], .sidebar, .comments');
          noise.forEach(el => el.remove());
          return clone.innerText.trim();
        }
        
        return contentEl.innerText.trim();
      }
    });
    
    return results[0]?.result || '';
  } catch (err) {
    console.warn('Content extraction failed:', err);
    return ''; // Non-fatal: server will fetch later
  }
}

async function captureAndClose() {
  console.log('captureAndClose called, currentTab:', currentTab);
  if (!currentTab) {
    console.error('No tab yet');
    return;
  }
  
  // Show loading state
  document.body.classList.add('loading');
  
  // Extract content from page
  const content = await extractPageContent(currentTab.id);
  
  const payload = {
    url: currentTab.url,
    title: currentTab.title || '',
    note: noteInput.value.trim(),
    content: content, // New: page content captured at source
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

    document.body.classList.remove('loading');
    document.body.classList.add('success');

    setTimeout(() => {
      chrome.tabs.remove(currentTab.id);
      window.close();
    }, 400);

  } catch (err) {
    console.error('Capture failed:', err);
    document.body.classList.remove('loading');
    document.body.classList.add('error');
    errorMessage.textContent = 'Could not connect to capture server. Is it running?';
  }
}
