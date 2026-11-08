/**
 * TRASCO Popup UI Logic
 * Connects directly to background service worker and validates backend engine health.
 */

document.addEventListener('DOMContentLoaded', () => {
  const toggleProtection = document.getElementById('toggleProtection');
  const toggleAudio = document.getElementById('toggleAudio');
  const statusBadge = document.getElementById('statusBadge');
  const scanInput = document.getElementById('scanInput');
  const btnScan = document.getElementById('btnScan');
  const scanResult = document.getElementById('scanResult');
  const btnOpenDashboard = document.getElementById('btnOpenDashboard');
  const btnRetryEngine = document.getElementById('btnRetryEngine');
  const backendStatusDot = document.getElementById('backendStatusDot');
  const backendStatusText = document.getElementById('backendStatusText');

  // Verify Backend Engine Connectivity
  async function checkBackendHealth() {
    backendStatusDot.style.background = '#94a3b8';
    backendStatusDot.style.boxShadow = 'none';
    backendStatusText.textContent = 'Memeriksa Backend Engine...';

    try {
      const cfg = await chrome.storage.local.get(['backendUrl']);
      const baseUrl = cfg.backendUrl || 'http://localhost:8000';
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);

      const res = await fetch(`${baseUrl}/health`, {
        signal: controller.signal,
        headers: { 'X-Trasco-Source': 'Extension-Local' }
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        backendStatusDot.style.background = '#10B981';
        backendStatusDot.style.boxShadow = '0 0 8px rgba(16, 185, 129, 0.7)';
        backendStatusText.textContent = `Backend Online (v${data.version || '1.0.0'})`;
      } else {
        backendStatusDot.style.background = '#F59E0B';
        backendStatusDot.style.boxShadow = 'none';
        backendStatusText.textContent = `Backend Error (HTTP ${res.status})`;
      }
    } catch (err) {
      backendStatusDot.style.background = '#EF4444';
      backendStatusDot.style.boxShadow = '0 0 8px rgba(239, 68, 68, 0.6)';
      backendStatusText.textContent = 'Backend Offline (Aktifkan port 8000)';
    }
  }

  // Initial check & retry listener
  checkBackendHealth();
  if (btnRetryEngine) {
    btnRetryEngine.addEventListener('click', checkBackendHealth);
  }

  // Load stored preferences
  chrome.storage.local.get(['protectionEnabled', 'audioAlertEnabled'], (cfg) => {
    toggleProtection.checked = cfg.protectionEnabled !== false;
    toggleAudio.checked = cfg.audioAlertEnabled !== false;
    updateBadge(toggleProtection.checked);
  });

  // Toggles change
  toggleProtection.addEventListener('change', () => {
    const isEnabled = toggleProtection.checked;
    chrome.storage.local.set({ protectionEnabled: isEnabled });
    updateBadge(isEnabled);
  });

  toggleAudio.addEventListener('change', () => {
    chrome.storage.local.set({ audioAlertEnabled: toggleAudio.checked });
  });

  function updateBadge(enabled) {
    if (enabled) {
      statusBadge.innerHTML = '<span class="badge-dot"></span><span>AKTIF</span>';
      statusBadge.style.borderColor = '#10b981';
      statusBadge.style.color = '#6ee7b7';
      statusBadge.style.background = 'rgba(16, 185, 129, 0.15)';
    } else {
      statusBadge.innerHTML = '<span>NONAKTIF</span>';
      statusBadge.style.borderColor = '#64748b';
      statusBadge.style.color = '#94a3b8';
      statusBadge.style.background = 'rgba(100, 116, 139, 0.2)';
    }
  }

  // Quick Scan via Background Service Worker
  btnScan.addEventListener('click', async () => {
    const text = scanInput.value.trim();
    if (!text) {
      scanInput.focus();
      return;
    }

    btnScan.disabled = true;
    btnScan.innerHTML = '<span>⏳</span><span>Menganalisis...</span>';
    scanResult.style.display = 'none';

    try {
      const isUrl = text.startsWith('http://') || text.startsWith('https://') || text.includes('.com') || text.includes('.id') || text.includes('.xyz');
      const scanType = isUrl ? 'URL' : 'TEXT';

      // Send to background service worker
      chrome.runtime.sendMessage(
        {
          type: 'TRIGGER_SCAN',
          scanType,
          content: text
        },
        (response) => {
          btnScan.disabled = false;
          btnScan.innerHTML = '<span>⚡</span><span>Pindai dengan AI Engine</span>';

          if (response && response.success) {
            const data = response.data;
            scanResult.className = `result-box ${data.riskLevel}`;
            scanResult.style.display = 'block';

            // Safe DOM insertion (Anti-XSS)
            scanResult.textContent = '';
            const header = document.createElement('strong');
            header.textContent = `[${data.riskLevel} RISK - Skor: ${data.riskScore}/100]`;
            scanResult.appendChild(header);

            const br = document.createElement('br');
            scanResult.appendChild(br);

            const cat = document.createElement('span');
            cat.textContent = `Kategori: ${data.threatCategory.replace(/_/g, ' ')}`;
            scanResult.appendChild(cat);

            const summaryP = document.createElement('p');
            summaryP.style.marginTop = '4px';
            summaryP.textContent = data.summary;
            scanResult.appendChild(summaryP);
          } else {
            scanResult.className = 'result-box HIGH';
            scanResult.style.display = 'block';
            scanResult.textContent = 'Gagal memindai: ' + (response?.error || 'Tidak dapat terhubung ke Backend Engine.');
          }
        }
      );
    } catch (err) {
      btnScan.disabled = false;
      btnScan.innerHTML = '<span>⚡</span><span>Pindai dengan AI Engine</span>';
      scanResult.className = 'result-box HIGH';
      scanResult.style.display = 'block';
      scanResult.textContent = 'Error: ' + err.message;
    }
  });

  // Open Web Dashboard
  btnOpenDashboard.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:5173' });
  });

  // Test Voice Alert
  const btnTestVoice = document.getElementById('btnTestVoice');
  if (btnTestVoice) {
    btnTestVoice.addEventListener('click', () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const testUtterance = new SpeechSynthesisUtterance('Peringatan TRASCO aktif. Berselancar dengan aman.');
        testUtterance.lang = 'id-ID';
        testUtterance.rate = 1.05;
        window.speechSynthesis.speak(testUtterance);
      } else {
        alert('Browser Anda tidak mendukung Web Speech API.');
      }
    });
  }

  // Open Interactive Test Playground
  const btnOpenPlayground = document.getElementById('btnOpenPlayground');
  if (btnOpenPlayground) {
    btnOpenPlayground.addEventListener('click', () => {
      chrome.tabs.create({ url: chrome.runtime.getURL('demo_testpage.html') });
    });
  }
});
