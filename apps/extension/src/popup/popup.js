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

          if (chrome.runtime.lastError) {
            console.warn('[TRASCO] Runtime message error:', chrome.runtime.lastError.message);
            scanResult.className = 'result-box HIGH';
            scanResult.style.display = 'block';
            scanResult.textContent = 'Gagal memindai: Tidak dapat terhubung ke Backend Engine (Port 8000). Pastikan server backend sedang berjalan.';
            return;
          }

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

  // --- TASK-06 & TASK-07: Image Scam Detection UI Logic ---
  const imageDropzone = document.getElementById('imageDropzone');
  const imageFileInput = document.getElementById('imageFileInput');
  const imagePreview = document.getElementById('imagePreview');
  const dropzonePrompt = document.getElementById('dropzonePrompt');
  const imageFileInfo = document.getElementById('imageFileInfo');
  const imageFileName = document.getElementById('imageFileName');
  const btnRemoveImage = document.getElementById('btnRemoveImage');
  const btnScanImage = document.getElementById('btnScanImage');
  const imageScanResult = document.getElementById('imageScanResult');

  let selectedImageDataUrl = null;
  let selectedMimeType = null;
  let selectedFileName = null;

  function resetImageSelection() {
    selectedImageDataUrl = null;
    selectedMimeType = null;
    selectedFileName = null;
    imageFileInput.value = '';
    imagePreview.src = '';
    imagePreview.style.display = 'none';
    dropzonePrompt.style.display = 'block';
    imageFileInfo.style.display = 'none';
    imageFileName.textContent = '';
    btnScanImage.disabled = true;
    btnScanImage.style.opacity = '0.5';
    imageScanResult.style.display = 'none';
  }

  function handleImageFile(file) {
    if (!file) return;

    // Reset previous messages
    imageScanResult.style.display = 'none';

    // 1. Client-Side Size Guard (<= 5 MiB)
    const MAX_BYTES = 5 * 1024 * 1024;
    if (file.size > MAX_BYTES) {
      imageScanResult.className = 'result-box MEDIUM';
      imageScanResult.style.display = 'block';
      imageScanResult.textContent = `Ukuran file melebihi 5 MiB (${(file.size / (1024 * 1024)).toFixed(2)} MiB). Gunakan citra berukuran lebih kecil.`;
      resetImageSelection();
      return;
    }

    // 2. Client-Side MIME Allowlist
    const validMimes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validMimes.includes(file.type)) {
      imageScanResult.className = 'result-box MEDIUM';
      imageScanResult.style.display = 'block';
      imageScanResult.textContent = `Format file '${file.type || 'unknown'}' tidak didukung. Harap gunakan JPEG, PNG, atau WebP.`;
      resetImageSelection();
      return;
    }

    selectedMimeType = file.type;
    selectedFileName = file.name;

    // 3. Read via FileReader
    const reader = new FileReader();
    reader.onload = (e) => {
      selectedImageDataUrl = e.target.result;
      imagePreview.src = selectedImageDataUrl;
      imagePreview.style.display = 'block';
      dropzonePrompt.style.display = 'none';

      imageFileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      imageFileInfo.style.display = 'flex';

      btnScanImage.disabled = false;
      btnScanImage.style.opacity = '1.0';
    };

    reader.onerror = () => {
      imageScanResult.className = 'result-box MEDIUM';
      imageScanResult.style.display = 'block';
      imageScanResult.textContent = 'Gagal membaca file gambar dari perangkat Anda.';
      resetImageSelection();
    };

    reader.readAsDataURL(file);
  }

  if (imageDropzone && imageFileInput) {
    imageDropzone.addEventListener('click', () => {
      if (!selectedImageDataUrl) {
        imageFileInput.click();
      }
    });

    imageFileInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) handleImageFile(file);
    });

    imageDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      imageDropzone.classList.add('dragover');
    });

    imageDropzone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      imageDropzone.classList.remove('dragover');
    });

    imageDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      imageDropzone.classList.remove('dragover');
      const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (file) handleImageFile(file);
    });
  }

  if (btnRemoveImage) {
    btnRemoveImage.addEventListener('click', (e) => {
      e.stopPropagation();
      resetImageSelection();
    });
  }

  if (btnScanImage) {
    btnScanImage.addEventListener('click', () => {
      if (!selectedImageDataUrl) return;

      btnScanImage.disabled = true;
      btnScanImage.innerHTML = '<span>⏳</span><span>Menganalisis Bukti Transfer...</span>';
      imageScanResult.style.display = 'none';

      chrome.runtime.sendMessage(
        {
          type: 'RUN_IMAGE_SCAN',
          content: selectedImageDataUrl,
          mimeType: selectedMimeType,
          fileName: selectedFileName
        },
        (response) => {
          btnScanImage.disabled = false;
          btnScanImage.innerHTML = '<span>🔍</span><span>Pindai Bukti Transfer</span>';

          if (chrome.runtime.lastError) {
            console.warn('[TRASCO] Runtime message error:', chrome.runtime.lastError.message);
            imageScanResult.className = 'result-box MEDIUM';
            imageScanResult.style.display = 'block';
            imageScanResult.textContent = 'Gagal memindai: Tidak dapat terhubung ke Backend Engine (Port 8000). Pastikan server backend sedang berjalan.';
            return;
          }

          const data = response && response.data;
          if (data) {
            const isHigh = data.riskLevel === 'HIGH';
            const isLow = data.riskLevel === 'LOW' && data.success && data.status === 'COMPLETED';
            const riskClass = isHigh ? 'HIGH' : (isLow ? 'LOW' : 'MEDIUM');

            imageScanResult.className = `result-box ${riskClass}`;
            imageScanResult.style.display = 'block';

            // Safe DOM insertion (Anti-XSS)
            imageScanResult.textContent = '';
            const header = document.createElement('strong');
            const scoreText = (data.riskScore !== null && data.riskScore !== undefined) ? `${data.riskScore}/100` : 'Verifikasi Manual';
            header.textContent = `[${data.riskLevel || 'UNKNOWN'} RISK - Skor: ${scoreText}]`;
            imageScanResult.appendChild(header);

            const br1 = document.createElement('br');
            imageScanResult.appendChild(br1);

            const cat = document.createElement('span');
            cat.textContent = `Kategori: ${(data.threatCategory || 'PERIKSA_MANUAL').replace(/_/g, ' ')}`;
            imageScanResult.appendChild(cat);

            const summaryP = document.createElement('p');
            summaryP.style.marginTop = '4px';
            summaryP.textContent = data.summary || 'Pemeriksaan keamanan selesai.';
            imageScanResult.appendChild(summaryP);

            if (data.error && data.error.message) {
              const errP = document.createElement('p');
              errP.style.fontSize = '10px';
              errP.style.marginTop = '4px';
              errP.style.opacity = '0.85';
              errP.textContent = `Catatan Keamanan: ${data.error.message}`;
              imageScanResult.appendChild(errP);
            }
          } else {
            imageScanResult.className = 'result-box MEDIUM';
            imageScanResult.style.display = 'block';
            imageScanResult.textContent = 'Gagal memindai: ' + (response?.error || 'Tidak dapat terhubung ke Backend Engine.');
          }
        }
      );
    });
  }

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
