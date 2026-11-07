/**
 * TRASCO AI Cyber Guardian - Background Service Worker (Manifest V3)
 */

const DEFAULT_CONFIG = {
  protectionEnabled: true,
  audioAlertEnabled: true,
  avatarEnabled: true,
  backendUrl: 'http://localhost:8000'
};

// Initialize settings and context menus on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(DEFAULT_CONFIG, (stored) => {
    chrome.storage.local.set(stored);
  });

  // Context menu for selected text
  chrome.contextMenus.create({
    id: 'trasco-scan-text',
    title: '🛡️ Periksa dengan TRASCO (AI Scam Check)',
    contexts: ['selection']
  });

  // Context menu for images (e.g. transfer slips, fake promos)
  chrome.contextMenus.create({
    id: 'trasco-scan-image',
    title: '🔍 Verifikasi Bukti Transfer dengan TRASCO',
    contexts: ['image']
  });

  console.log('[TRASCO] Service Worker installed and context menus registered.');
});

// Context Menu Click Handler
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab || !tab.id) return;

  if (info.menuItemId === 'trasco-scan-text' && info.selectionText) {
    // Notify content script that analysis has started
    chrome.tabs.sendMessage(tab.id, {
      type: 'SCAN_START',
      payload: { snippet: info.selectionText.substring(0, 60) + '...' }
    });

    try {
      const result = await analyzeContent('TEXT', info.selectionText, { sourceDomain: tab.url });
      chrome.tabs.sendMessage(tab.id, {
        type: 'SCAN_RESULT',
        payload: result
      });
    } catch (err) {
      console.error('[TRASCO] Scan error:', err);
      chrome.tabs.sendMessage(tab.id, {
        type: 'SCAN_ERROR',
        error: 'Gagal terhubung ke TRASCO Backend Engine.'
      });
    }
  } else if (info.menuItemId === 'trasco-scan-image' && info.srcUrl) {
    chrome.tabs.sendMessage(tab.id, {
      type: 'SCAN_START',
      payload: { snippet: 'Memverifikasi bukti transfer...' }
    });

    try {
      const result = await analyzeContent('IMAGE', info.srcUrl, { sourceDomain: tab.url });
      chrome.tabs.sendMessage(tab.id, {
        type: 'SCAN_RESULT',
        payload: result
      });
    } catch (err) {
      console.error('[TRASCO] Image scan error:', err);
    }
  }
});

// Tab Navigation Listener (Proactive URL Checking)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.startsWith('http')) {
    chrome.storage.local.get(['protectionEnabled', 'backendUrl'], async (cfg) => {
      if (!cfg.protectionEnabled) return;

      try {
        const urlObj = new URL(tab.url);
        // Skip scanning local development or search engines by default
        if (['localhost', '127.0.0.1', 'google.com', 'www.google.com'].includes(urlObj.hostname)) {
          return;
        }

        const result = await analyzeContent('URL', tab.url, { sourceDomain: urlObj.hostname });
        // Only trigger avatar if threat is detected (MEDIUM or HIGH)
        if (result && result.riskLevel !== 'LOW') {
          chrome.tabs.sendMessage(tabId, {
            type: 'SCAN_RESULT',
            payload: result
          });
        }
      } catch (e) {
        // Silent fail for background proactive scans to preserve smooth browsing
      }
    });
  }
});

// Core API communication
async function analyzeContent(scanType, content, metadata = {}) {
  const cfg = await chrome.storage.local.get(['backendUrl']);
  const baseUrl = cfg.backendUrl || 'http://localhost:8000';
  const endpoint = scanType === 'IMAGE' ? '/api/v1/detect/analyze-image' : '/api/v1/detect/analyze';

  const res = await fetch(`${baseUrl}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scanType,
      content,
      metadata
    })
  });

  if (!res.ok) {
    throw new Error(`Server returned HTTP ${res.status}`);
  }

  return await res.json();
}

// Runtime Message Dispatcher
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'TRIGGER_SCAN') {
    analyzeContent(message.scanType, message.content, message.metadata)
      .then(res => sendResponse({ success: true, data: res }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // Keep message channel open for async response
  }
});

