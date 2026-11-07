/**
 * TRASCO AI Cyber Guardian - Content Script & Shadow DOM Isolated Avatar
 */

(function initTrascoGuardian() {
  if (document.getElementById('trasco-cyber-guardian-host')) {
    return; // Already initialized
  }

  // Create Host Element & Shadow Root
  const host = document.createElement('div');
  host.id = 'trasco-cyber-guardian-host';
  document.body.appendChild(host);
  const shadow = host.attachShadow({ mode: 'open' });

  // Inject Styles into Shadow DOM (Immune to external page CSS)
  const style = document.createElement('style');
  style.textContent = `
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    #trasco-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 2147483647; /* Maximum z-index */
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 12px;
      pointer-events: none;
    }

    .interactive {
      pointer-events: auto;
    }

    /* Floating Avatar Mascot Orb */
    .avatar-orb {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      background: #0f172a;
      border: 3px solid #06b6d4;
      box-shadow: 0 0 20px rgba(6, 182, 212, 0.4), 0 8px 16px rgba(0, 0, 0, 0.5);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      animation: floatAnim 3s ease-in-out infinite;
    }

    .avatar-orb:hover {
      transform: scale(1.08) translateY(-4px);
    }

    .avatar-orb.high-risk {
      border-color: #ef4444;
      box-shadow: 0 0 25px rgba(239, 68, 68, 0.7), 0 8px 20px rgba(0, 0, 0, 0.6);
      animation: pulseRisk 1s infinite alternate;
    }

    .avatar-orb.medium-risk {
      border-color: #f59e0b;
      box-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
    }

    .avatar-svg {
      width: 38px;
      height: 38px;
      transition: transform 0.2s;
    }

    /* Dialog / Warning Card */
    .speech-card {
      width: 350px;
      max-width: calc(100vw - 48px);
      background: rgba(15, 23, 42, 0.96);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(51, 65, 85, 0.8);
      border-radius: 16px;
      padding: 16px;
      color: #f8fafc;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
      display: none;
      flex-direction: column;
      gap: 12px;
      animation: slideUp 0.3s ease-out forwards;
    }

    .speech-card.active {
      display: flex;
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(51, 65, 85, 0.6);
      padding-bottom: 8px;
    }

    .brand-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #38bdf8;
    }

    .risk-badge {
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 9999px;
      text-transform: uppercase;
    }

    .badge-high {
      background: rgba(239, 68, 68, 0.2);
      color: #fca5a5;
      border: 1px solid #ef4444;
    }

    .badge-medium {
      background: rgba(245, 158, 11, 0.2);
      color: #fcd34d;
      border: 1px solid #f59e0b;
    }

    .badge-low {
      background: rgba(16, 185, 129, 0.2);
      color: #6ee7b7;
      border: 1px solid #10b981;
    }

    .card-body {
      font-size: 13px;
      line-height: 1.5;
      color: #cbd5e1;
    }

    .card-body strong {
      color: #ffffff;
    }

    .indicator-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: rgba(30, 41, 59, 0.6);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 12px;
    }

    .indicator-item {
      display: flex;
      align-items: flex-start;
      gap: 6px;
    }

    .indicator-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #ef4444;
      margin-top: 5px;
      flex-shrink: 0;
    }

    .card-actions {
      display: flex;
      gap: 8px;
      margin-top: 4px;
    }

    .btn {
      flex: 1;
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      text-align: center;
    }

    .btn-danger {
      background: #dc2626;
      color: #ffffff;
    }
    .btn-danger:hover {
      background: #b91c1c;
    }

    .btn-secondary {
      background: #334155;
      color: #e2e8f0;
    }
    .btn-secondary:hover {
      background: #475569;
    }

    .close-btn {
      background: none;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 16px;
      line-height: 1;
    }
    .close-btn:hover {
      color: #ffffff;
    }

    /* Animations */
    @keyframes floatAnim {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-6px); }
    }

    @keyframes pulseRisk {
      0% { transform: scale(1); filter: brightness(1); }
      100% { transform: scale(1.06); filter: brightness(1.2); }
    }

    @keyframes slideUp {
      from { opacity: 0; transform: translateY(12px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;
  shadow.appendChild(style);

  // Template HTML
  const container = document.createElement('div');
  container.id = 'trasco-container';
  container.innerHTML = `
    <div id="trasco-card" class="speech-card interactive">
      <div class="card-header">
        <div class="brand-title">
          <span>🛡️</span>
          <span>TRASCO AI GUARDIAN</span>
        </div>
        <div id="trasco-risk-badge" class="risk-badge badge-high">HIGH RISK</div>
        <button id="trasco-close-card" class="close-btn" title="Tutup">✕</button>
      </div>

      <div class="card-body">
        <p id="trasco-speech-text">Memindai aktivitas...</p>
      </div>

      <div id="trasco-indicators-box" class="indicator-list" style="display: none;">
        <!-- Dynamic indicators inserted here -->
      </div>

      <div class="card-actions">
        <button id="trasco-btn-primary" class="btn btn-danger">Hentikan Interaksi</button>
        <button id="trasco-btn-dismiss" class="btn btn-secondary">Abaikan</button>
      </div>
    </div>

    <div id="trasco-avatar-orb" class="avatar-orb interactive" title="TRASCO AI Cyber Guardian">
      <svg class="avatar-svg" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Shield Background -->
        <path d="M18 3L6 7V16C6 24 11 31 18 33C25 31 30 24 30 16V7L18 3Z" fill="#0EA5E9" fill-opacity="0.2" stroke="#06B6D4" stroke-width="2"/>
        <!-- Cyber Eyes -->
        <circle id="avatar-eye-left" cx="13" cy="16" r="2.5" fill="#38BDF8"/>
        <circle id="avatar-eye-right" cx="23" cy="16" r="2.5" fill="#38BDF8"/>
        <!-- Visor Core -->
        <rect id="avatar-core" x="11" y="22" width="14" height="2" rx="1" fill="#10B981"/>
      </svg>
    </div>
  `;
  shadow.appendChild(container);

  // Elements
  const orb = shadow.getElementById('trasco-avatar-orb');
  const card = shadow.getElementById('trasco-card');
  const speechText = shadow.getElementById('trasco-speech-text');
  const riskBadge = shadow.getElementById('trasco-risk-badge');
  const indicatorsBox = shadow.getElementById('trasco-indicators-box');
  const closeCardBtn = shadow.getElementById('trasco-close-card');
  const primaryBtn = shadow.getElementById('trasco-btn-primary');
  const dismissBtn = shadow.getElementById('trasco-btn-dismiss');
  const eyeLeft = shadow.getElementById('avatar-eye-left');
  const eyeRight = shadow.getElementById('avatar-eye-right');
  const avatarCore = shadow.getElementById('avatar-core');

  // Toggle card on avatar orb click
  orb.addEventListener('click', () => {
    card.classList.toggle('active');
  });

  closeCardBtn.addEventListener('click', () => {
    card.classList.remove('active');
  });

  dismissBtn.addEventListener('click', () => {
    card.classList.remove('active');
  });

  primaryBtn.addEventListener('click', () => {
    // If high risk, user can navigate back or close tab
    if (confirm('TRASCO menyarankan Anda meninggalkan halaman berisiko ini. Ingin kembali ke halaman aman?')) {
      window.history.back();
    }
    card.classList.remove('active');
  });

  // Text-To-Speech Helper
  function speakVoiceWarning(text) {
    if (!('speechSynthesis' in window)) return;
    chrome.storage.local.get(['audioAlertEnabled'], (cfg) => {
      if (cfg.audioAlertEnabled === false) return;

      window.speechSynthesis.cancel(); // Stop any pending speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'id-ID';
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    });
  }

  // Handle Messages from Background Service Worker
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'SCAN_START') {
      orb.classList.remove('high-risk', 'medium-risk');
      card.classList.add('active');
      speechText.textContent = `Memindai teks dengan AI: "${message.payload.snippet}"`;
      riskBadge.textContent = 'ANALYZING';
      riskBadge.className = 'risk-badge badge-medium';
      indicatorsBox.style.display = 'none';
      eyeLeft.setAttribute('fill', '#F59E0B');
      eyeRight.setAttribute('fill', '#F59E0B');
    } else if (message.type === 'SCAN_RESULT') {
      const data = message.payload;
      card.classList.add('active');

      // Update Badge
      riskBadge.textContent = `${data.riskLevel} RISK (${data.riskScore}/100)`;
      riskBadge.className = `risk-badge badge-${data.riskLevel.toLowerCase()}`;

      // Update Text & Mood
      speechText.innerHTML = `<strong>${data.summary}</strong>`;
      orb.classList.remove('high-risk', 'medium-risk');

      if (data.riskLevel === 'HIGH') {
        orb.classList.add('high-risk');
        eyeLeft.setAttribute('fill', '#EF4444');
        eyeRight.setAttribute('fill', '#EF4444');
        avatarCore.setAttribute('fill', '#EF4444');
        primaryBtn.textContent = 'Tutup Halaman Ini';
        primaryBtn.className = 'btn btn-danger';
        primaryBtn.style.display = 'block';
      } else if (data.riskLevel === 'MEDIUM') {
        orb.classList.add('medium-risk');
        eyeLeft.setAttribute('fill', '#F59E0B');
        eyeRight.setAttribute('fill', '#F59E0B');
        avatarCore.setAttribute('fill', '#F59E0B');
        primaryBtn.textContent = 'Waspada & Periksa';
        primaryBtn.className = 'btn btn-secondary';
        primaryBtn.style.display = 'block';
      } else {
        eyeLeft.setAttribute('fill', '#10B981');
        eyeRight.setAttribute('fill', '#10B981');
        avatarCore.setAttribute('fill', '#10B981');
        primaryBtn.style.display = 'none';
      }

      // Populate Indicators
      if (data.detectionIndicators && data.detectionIndicators.length > 0) {
        indicatorsBox.innerHTML = '';
        data.detectionIndicators.forEach((ind) => {
          const item = document.createElement('div');
          item.className = 'indicator-item';
          item.innerHTML = `
            <span class="indicator-dot" style="background: ${data.avatarGuidance.accentColor}"></span>
            <span><strong>${ind.indicator}:</strong> ${ind.explanation}</span>
          `;
          indicatorsBox.appendChild(item);
        });
        indicatorsBox.style.display = 'flex';
      } else {
        indicatorsBox.style.display = 'none';
      }

      // Audio alert
      if (data.avatarGuidance && data.avatarGuidance.speechText) {
        speakVoiceWarning(data.avatarGuidance.speechText);
      }
    } else if (message.type === 'SCAN_ERROR') {
      card.classList.add('active');
      speechText.textContent = message.error;
      riskBadge.textContent = 'ERROR';
      riskBadge.className = 'risk-badge badge-medium';
    }
  });

  console.log('[TRASCO] AI Cyber Guardian Avatar initialized in Shadow DOM.');
})();

