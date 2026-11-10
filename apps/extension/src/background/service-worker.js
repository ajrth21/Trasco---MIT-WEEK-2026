/**
 * TRASCO AI Cyber Guardian - Background Service Worker (Manifest V3)
 * Orchestrates threat detection, caching, context menus, and toolbar badge states.
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

  // Re-create context menus cleanly
  chrome.contextMenus.removeAll(() => {
    // Context menu for selected text
    chrome.contextMenus.create({
      id: 'trasco-scan-text',
      title: '🛡️ Periksa dengan TRASCO (AI Scam Check)',
      contexts: ['selection']
    });

    // Context menu for images (e.g. transfer slips, fake promos, scam posters)
    chrome.contextMenus.create({
      id: 'trasco-scan-image',
      title: '🔍 Periksa Gambar dengan TRASCO (AI Scam Check)',
      contexts: ['image']
    });
  });

  console.log('[TRASCO] Service Worker installed, context menus registered.');
});

// Update Extension Toolbar Badge Icon
function updateBadge(tabId, riskLevel) {
  if (!tabId || !chrome.action) return;

  if (riskLevel === 'HIGH') {
    chrome.action.setBadgeText({ tabId, text: '!' });
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#EF4444' }); // Red alert
  } else if (riskLevel === 'MEDIUM') {
    chrome.action.setBadgeText({ tabId, text: '?' });
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#F59E0B' }); // Warning amber
  } else if (riskLevel === 'LOW') {
    chrome.action.setBadgeText({ tabId, text: '✓' });
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#10B981' }); // Safe green
  } else {
    chrome.action.setBadgeText({ tabId, text: '' });
  }
}

// In-memory cache & debounce timer to eliminate request flooding and quota exhaustion
const domainScanCache = new Map(); // key: hostname, val: { result, expiresAt }
let navigationDebounceTimer = null;

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
      updateBadge(tab.id, result.riskLevel);

      chrome.tabs.sendMessage(tab.id, {
        type: 'SCAN_RESULT',
        payload: result
      });
    } catch (err) {
      console.error('[TRASCO] Scan error:', err);
      chrome.tabs.sendMessage(tab.id, {
        type: 'SCAN_ERROR',
        error: 'Gagal terhubung ke TRASCO Backend Engine. Pastikan server aktif.'
      });
    }
  } else if (info.menuItemId === 'trasco-scan-image' && info.srcUrl) {
    chrome.tabs.sendMessage(tab.id, {
      type: 'SCAN_START',
      payload: { snippet: 'Memeriksa potensi penipuan pada gambar...' }
    });

    try {
      const result = await analyzeContent('IMAGE', info.srcUrl, { sourceDomain: tab.url });
      updateBadge(tab.id, result.riskLevel);

      chrome.tabs.sendMessage(tab.id, {
        type: 'SCAN_RESULT',
        payload: result
      });
    } catch (err) {
      console.error('[TRASCO] Image scan error:', err);
      chrome.tabs.sendMessage(tab.id, {
        type: 'SCAN_ERROR',
        error: 'Gagal menganalisis gambar. Pastikan URL gambar dapat diakses.'
      });
    }
  }
});

// Tab Navigation Listener (Proactive URL Checking - Hardened with Debounce & Cache)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.startsWith('http')) {
    if (navigationDebounceTimer) clearTimeout(navigationDebounceTimer);

    navigationDebounceTimer = setTimeout(() => {
      chrome.storage.local.get(['protectionEnabled', 'backendUrl'], async (cfg) => {
        if (!cfg.protectionEnabled) return;

        try {
          const urlObj = new URL(tab.url);
          const hostname = urlObj.hostname;

          // Skip scanning local development or search engines by default
          if (['localhost', '127.0.0.1', 'google.com', 'www.google.com'].includes(hostname)) {
            updateBadge(tabId, 'LOW');
            return;
          }

          // Check in-memory cache (10 min TTL)
          const now = Date.now();
          if (domainScanCache.has(hostname)) {
            const cached = domainScanCache.get(hostname);
            if (cached.expiresAt > now) {
              updateBadge(tabId, cached.result.riskLevel);
              if (cached.result && cached.result.riskLevel !== 'LOW') {
                chrome.tabs.sendMessage(tabId, { type: 'SCAN_RESULT', payload: cached.result });
              }
              return;
            }
          }

          // Run passive heuristic scan (Does NOT consume Gemini API quota)
          const result = await analyzeContent('URL', tab.url, { 
            sourceDomain: hostname,
            mode: 'passive_heuristic' 
          });

          // Cache result
          domainScanCache.set(hostname, { result, expiresAt: now + (10 * 60 * 1000) });
          updateBadge(tabId, result.riskLevel);

          // Only trigger avatar visually if threat is detected (MEDIUM or HIGH)
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
    }, 400); // 400ms debounce
  }
});

// Update Badge on Tab Switching
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (!tab || !tab.url || !tab.url.startsWith('http')) {
      updateBadge(activeInfo.tabId, null);
      return;
    }
    const hostname = new URL(tab.url).hostname;
    if (domainScanCache.has(hostname)) {
      const cached = domainScanCache.get(hostname);
      if (cached && cached.result) {
        updateBadge(activeInfo.tabId, cached.result.riskLevel);
      }
    }
  } catch (e) {
    // Tab might be closed or special page
  }
});

// Core API communication with Security Handshake Header
async function analyzeContent(scanType, content, metadata = {}) {
  const cfg = await chrome.storage.local.get(['backendUrl']);
  const baseUrl = cfg.backendUrl || 'http://localhost:8000';
  const endpoint = scanType === 'IMAGE' ? '/api/v1/detect/analyze-image' : '/api/v1/detect/analyze';

  const res = await fetch(`${baseUrl}${endpoint}`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'X-Trasco-Source': 'Extension-Local'
    },
    body: JSON.stringify({
      scanType,
      content,
      metadata: {
        mode: metadata.mode || 'active_deep',
        ...metadata
      }
    })
  });

  if (!res.ok) {
    throw new Error(`Server returned HTTP ${res.status}`);
  }

  return await res.json();
}

// Safe tab notification helper for MV3 Service Worker (uses lastFocusedWindow instead of currentWindow)
async function broadcastToActiveTab(type, payload) {
  try {
    const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    if (tabs && tabs.length > 0 && tabs[0].id) {
      if (payload && payload.riskLevel) {
        updateBadge(tabs[0].id, payload.riskLevel);
      }
      await chrome.tabs.sendMessage(tabs[0].id, { type, payload }).catch(() => {});
    }
  } catch (e) {
    // Tab broadcast is best-effort; ignore errors in service worker background
  }
}

// Runtime Message Dispatcher
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'TRIGGER_SCAN') {
    analyzeContent(message.scanType, message.content, message.metadata)
      .then(res => {
        if (sender.tab && sender.tab.id) {
          updateBadge(sender.tab.id, res.riskLevel);
        }
        sendResponse({ success: true, data: res });
      })
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // Keep message channel open for async response
  }

  if (message.type === 'RUN_IMAGE_SCAN') {
    const { content, mimeType, fileName } = message;
    (async () => {
      let responsePayload = null;
      try {
        const cfg = await chrome.storage.local.get(['backendUrl']);
        const baseUrl = cfg.backendUrl || 'http://localhost:8000';
        const res = await fetch(`${baseUrl}/api/v1/detect/analyze-image`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Trasco-Source': 'Extension-Local'
          },
          body: JSON.stringify({
            scanType: 'IMAGE',
            content: content,
            mimeType: mimeType || 'image/jpeg',
            fileName: fileName || null,
            metadata: { fileName: fileName || null }
          })
        });

        const data = await res.json();
        responsePayload = { success: res.ok && data.success, data: data };
        await broadcastToActiveTab('SCAN_RESULT', data);
      } catch (err) {
        console.error('[TRASCO] Image scan error:', err);
        const failClosedFallback = {
          success: false,
          status: 'ANALYSIS_UNAVAILABLE',
          scanId: null,
          riskLevel: 'UNKNOWN',
          riskScore: null,
          threatCategory: null,
          confidenceScore: 0.0,
          detectionIndicators: [],
          recommendedActions: ['Verifikasi keaslian gambar dan informasi melalui kontak resmi institusi terkait.'],
          avatarGuidance: {
            mood: 'CAUTION_ALERT',
            speechText: 'Gagal terhubung ke Backend Engine. Verifikasi informasi secara manual.',
            accentColor: '#F59E0B',
            recommendedActionPrimary: 'Periksa Manual',
            recommendedActionSecondary: 'Pastikan Backend Berjalan'
          },
          error: {
            code: 'VISION_SERVICE_UNAVAILABLE',
            message: err.message || 'Network connection failed'
          }
        };

        responsePayload = { success: false, data: failClosedFallback, error: err.message };
        await broadcastToActiveTab('SCAN_RESULT', failClosedFallback);
      } finally {
        try {
          sendResponse(responsePayload);
        } catch (e) {
          console.warn('[TRASCO] sendResponse port error:', e);
        }
      }
    })();
    return true; // Keep message port open for async response
  }
});
