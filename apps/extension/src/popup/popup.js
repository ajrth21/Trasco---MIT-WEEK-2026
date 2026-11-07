/**
 * TRASCO Popup UI Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const toggleProtection = document.getElementById('toggleProtection');
  const toggleAudio = document.getElementById('toggleAudio');
  const statusBadge = document.getElementById('statusBadge');
  const scanInput = document.getElementById('scanInput');
  const btnScan = document.getElementById('btnScan');
  const scanResult = document.getElementById('scanResult');
  const btnOpenDashboard = document.getElementById('btnOpenDashboard');

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

  // Quick Scan
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
      const isUrl = text.startsWith('http://') || text.startsWith('https://') || text.includes('.com') || text.includes('.id');
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
          btnScan.innerHTML = '<span>⚡</span><span>Pindai dengan AI</span>';

          if (response && response.success) {
            const data = response.data;
            scanResult.className = `result-box ${data.riskLevel}`;
            scanResult.style.display = 'block';
            scanResult.innerHTML = `
              <strong>[${data.riskLevel} RISK - Skor: ${data.riskScore}/100]</strong><br>
              <strong>Kategori:</strong> ${data.threatCategory.replace(/_/g, ' ')}<br>
              <p style="margin-top: 4px;">${data.summary}</p>
            `;
          } else {
            scanResult.className = 'result-box HIGH';
            scanResult.style.display = 'block';
            scanResult.textContent = 'Gagal memindai: ' + (response?.error || 'Tidak dapat terhubung ke server');
          }
        }
      );
    } catch (err) {
      btnScan.disabled = false;
      btnScan.innerHTML = '<span>⚡</span><span>Pindai dengan AI</span>';
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
        const testUtterance = new SpeechSynthesisUtterance('Halo! TRASCO Cyber Guardian aktif menjaga aktivitas digital Anda.');
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

