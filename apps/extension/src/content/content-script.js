/**
 * TRASCO AI Cyber Guardian - Content Script & Shadow DOM Isolated Avatar
 * Provides non-intrusive, proactive cybersecurity warnings and voice guidance.
 * Immune to host page CSS bleeding and 100% Anti-DOM-XSS hardened.
 */

(function initTrascoGuardian() {
  if (document.getElementById('trasco-cyber-guardian-host')) {
    return; // Already initialized in this tab
  }

  // Create Host Element & Shadow Root (Isolated Sandbox)
  const host = document.createElement('div');
  host.id = 'trasco-cyber-guardian-host';
  document.body.appendChild(host);
  const shadow = host.attachShadow({ mode: 'closed' });

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
      z-index: 2147483647; /* Highest z-index */
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
      user-select: none;
    }

    .avatar-orb:hover {
      transform: scale(1.08) translateY(-4px);
      box-shadow: 0 0 25px rgba(6, 182, 212, 0.6), 0 12px 20px rgba(0, 0, 0, 0.6);
    }

    .avatar-orb.high-risk {
      border-color: #ef4444;
      box-shadow: 0 0 30px rgba(239, 68, 68, 0.7), 0 8px 20px rgba(0, 0, 0, 0.6);
      animation: pulseRisk 0.9s infinite alternate;
    }

    .avatar-orb.medium-risk {
      border-color: #f59e0b;
      box-shadow: 0 0 22px rgba(245, 158, 11, 0.5);
      animation: floatAnim 2.5s ease-in-out infinite;
    }

    .avatar-orb.analyzing {
      border-color: #38bdf8;
      box-shadow: 0 0 25px rgba(56, 189, 248, 0.7);
      animation: pulseAnalyzing 1s ease-in-out infinite alternate;
    }

    .avatar-svg {
      width: 38px;
      height: 38px;
      transition: transform 0.2s;
    }

    /* Dialog / Warning Card */
    .speech-card {
      width: 360px;
      max-width: calc(100vw - 48px);
      background: rgba(15, 23, 42, 0.97);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(51, 65, 85, 0.85);
      border-radius: 18px;
      padding: 16px;
      color: #f8fafc;
      box-shadow: 0 20px 30px -5px rgba(0, 0, 0, 0.6), 0 10px 15px -5px rgba(0, 0, 0, 0.5);
      display: none;
      flex-direction: column;
      gap: 12px;
      animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    .speech-card.active {
      display: flex;
    }

    .speech-card.high-risk-border {
      border-color: rgba(239, 68, 68, 0.6);
      box-shadow: 0 0 20px rgba(239, 68, 68, 0.25), 0 20px 30px -5px rgba(0, 0, 0, 0.6);
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(51, 65, 85, 0.6);
      padding-bottom: 8px;
      gap: 6px;
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

    .header-actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .risk-badge {
      font-size: 10px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
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

    .icon-btn {
      background: rgba(51, 65, 85, 0.4);
      border: 1px solid rgba(100, 116, 139, 0.3);
      color: #94a3b8;
      cursor: pointer;
      font-size: 12px;
      width: 24px;
      height: 24px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }

    .icon-btn:hover {
      background: #334155;
      color: #ffffff;
    }

    .card-body {
      font-size: 13px;
      line-height: 1.5;
      color: #cbd5e1;
    }

    .card-body strong {
      color: #ffffff;
      display: block;
      margin-bottom: 2px;
    }

    .indicator-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: rgba(30, 41, 59, 0.65);
      border: 1px solid rgba(51, 65, 85, 0.5);
      padding: 8px 12px;
      border-radius: 10px;
      font-size: 11px;
    }

    .indicator-item {
      display: flex;
      align-items: flex-start;
      gap: 8px;
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
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .btn-danger {
      background: #dc2626;
      color: #ffffff;
    }
    .btn-danger:hover {
      background: #b91c1c;
    }

    .btn-info {
      background: rgba(14, 165, 233, 0.2);
      border: 1px solid #0ea5e9;
      color: #38bdf8;
    }
    .btn-info:hover {
      background: rgba(14, 165, 233, 0.35);
    }

    .btn-secondary {
      background: #334155;
      color: #e2e8f0;
    }
    .btn-secondary:hover {
      background: #475569;
    }

    /* Keyframe Animations */
    @keyframes floatAnim {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-6px); }
    }

    @keyframes pulseRisk {
      0% { transform: scale(1); filter: brightness(1); }
      100% { transform: scale(1.08); filter: brightness(1.2); }
    }

    @keyframes pulseAnalyzing {
      0% { transform: scale(1); filter: brightness(1); }
      100% { transform: scale(1.05); filter: brightness(1.2); }
    }

    @keyframes slideUp {
      from { opacity: 0; transform: translateY(16px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;
  shadow.appendChild(style);

  // Template Container HTML
  const container = document.createElement('div');
  container.id = 'trasco-container';
  container.innerHTML = `
    <div id="trasco-card" class="speech-card interactive">
      <div class="card-header">
        <div class="brand-title">
          <span>🛡️</span>
          <span>TRASCO AI GUARDIAN</span>
        </div>
        <div class="header-actions">
          <div id="trasco-risk-badge" class="risk-badge badge-high">HIGH RISK</div>
          <button id="trasco-btn-audio" class="icon-btn" title="Dengarkan Peringatan Suara">🔊</button>
          <button id="trasco-close-card" class="icon-btn" title="Tutup">✕</button>
        </div>
      </div>

      <div class="card-body">
        <p id="trasco-speech-text">Memindai aktivitas...</p>
      </div>

      <div id="trasco-indicators-box" class="indicator-list" style="display: none;">
        <!-- Dynamic indicators inserted safely here -->
      </div>

      <div class="card-actions">
        <button id="trasco-btn-primary" class="btn btn-danger">Tinggalkan Halaman</button>
        <button id="trasco-btn-dashboard" class="btn btn-info">Buka Dashboard</button>
        <button id="trasco-btn-dismiss" class="btn btn-secondary">Abaikan</button>
      </div>
    </div>

    <div id="trasco-avatar-orb" class="avatar-orb interactive" title="TRASCO AI Cyber Guardian">
      <svg class="avatar-svg" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Shield Background -->
        <path id="avatar-shield" d="M18 3L6 7V16C6 24 11 31 18 33C25 31 30 24 30 16V7L18 3Z" fill="#0EA5E9" fill-opacity="0.25" stroke="#06B6D4" stroke-width="2"/>
        <!-- Cyber Eyes -->
        <circle id="avatar-eye-left" cx="13" cy="16" r="2.5" fill="#38BDF8"/>
        <circle id="avatar-eye-right" cx="23" cy="16" r="2.5" fill="#38BDF8"/>
        <!-- Visor Core -->
        <rect id="avatar-core" x="11" y="22" width="14" height="2.5" rx="1" fill="#10B981"/>
      </svg>
    </div>
  `;
  shadow.appendChild(container);

  // Cached DOM Elements
  const orb = shadow.getElementById('trasco-avatar-orb');
  const card = shadow.getElementById('trasco-card');
  const speechText = shadow.getElementById('trasco-speech-text');
  const riskBadge = shadow.getElementById('trasco-risk-badge');
  const indicatorsBox = shadow.getElementById('trasco-indicators-box');
  const audioBtn = shadow.getElementById('trasco-btn-audio');
  const closeCardBtn = shadow.getElementById('trasco-close-card');
  const primaryBtn = shadow.getElementById('trasco-btn-primary');
  const dashboardBtn = shadow.getElementById('trasco-btn-dashboard');
  const dismissBtn = shadow.getElementById('trasco-btn-dismiss');
  const avatarShield = shadow.getElementById('avatar-shield');
  const eyeLeft = shadow.getElementById('avatar-eye-left');
  const eyeRight = shadow.getElementById('avatar-eye-right');
  const avatarCore = shadow.getElementById('avatar-core');

  let currentVoiceWarning = 'Status aman. TRASCO terus menjaga keamanan berselancar Anda.';

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
    if (confirm('TRASCO menyarankan Anda meninggalkan halaman berisiko tinggi ini. Ingin kembali ke halaman sebelumnya?')) {
      window.history.back();
    }
    card.classList.remove('active');
  });

  dashboardBtn.addEventListener('click', () => {
    chrome.storage.local.get(['backendUrl'], (cfg) => {
      const url = 'http://localhost:5173';
      window.open(url, '_blank');
    });
  });

  // Audio Playback Button (User-gesture driven - 100% compliant with browser autoplay policies)
  audioBtn.addEventListener('click', () => {
    speakVoiceWarning(currentVoiceWarning);
  });

  // Text-To-Speech Synthesis Helper
  function speakVoiceWarning(text) {
    if (!('speechSynthesis' in window)) return;
    chrome.storage.local.get(['audioAlertEnabled'], (cfg) => {
      if (cfg.audioAlertEnabled === false) return;

      window.speechSynthesis.cancel(); // Cancel pending speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'id-ID';
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    });
  }

  // Handle Messages from Background Service Worker
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'SCAN_START') {
      orb.className = 'avatar-orb interactive analyzing';
      card.classList.add('active');
      card.classList.remove('high-risk-border');
      speechText.textContent = `Memindai konten dengan TRASCO AI: "${message.payload.snippet}"`;
      riskBadge.textContent = 'ANALYZING';
      riskBadge.className = 'risk-badge badge-medium';
      indicatorsBox.style.display = 'none';
      eyeLeft.setAttribute('fill', '#38BDF8');
      eyeRight.setAttribute('fill', '#38BDF8');
      avatarCore.setAttribute('fill', '#38BDF8');
      if (typeof sendResponse === 'function') sendResponse({ received: true });
    } else if (message.type === 'SCAN_RESULT') {
      const data = message.payload || {};
      card.classList.add('active');

      // Fail-closed status evaluation
      const isFailedOrUnknown = !data.success || data.status !== 'COMPLETED' || data.riskLevel === 'UNKNOWN';
      const isHighRisk = data.riskLevel === 'HIGH';
      const isMediumRisk = data.riskLevel === 'MEDIUM' || isFailedOrUnknown;
      const isLowRisk = data.riskLevel === 'LOW' && data.success && data.status === 'COMPLETED';

      // Update Badge (Never show undefined/null/NaN)
      const scoreText = (data.riskScore !== null && data.riskScore !== undefined) ? `${data.riskScore}/100` : 'Verifikasi Manual';
      riskBadge.textContent = `${data.riskLevel || 'UNKNOWN'} RISK (${scoreText})`;
      riskBadge.className = `risk-badge badge-${isHighRisk ? 'high' : (isLowRisk ? 'low' : 'medium')}`;

      // Update Text Safely (Anti-DOM-XSS Hardened)
      speechText.textContent = '';
      const summaryStrong = document.createElement('strong');
      summaryStrong.textContent = data.summary || (isFailedOrUnknown ? 'Pemeriksaan keamanan tidak selesai. Lakukan verifikasi manual ke pihak resmi.' : 'Aktivitas terverifikasi aman.');
      speechText.appendChild(summaryStrong);

      orb.className = 'avatar-orb interactive';

      if (isHighRisk) {
        orb.classList.add('high-risk');
        card.classList.add('high-risk-border');
        avatarShield.setAttribute('stroke', '#EF4444');
        avatarShield.setAttribute('fill', '#EF4444');
        avatarShield.setAttribute('fill-opacity', '0.35');
        eyeLeft.setAttribute('fill', '#EF4444');
        eyeRight.setAttribute('fill', '#EF4444');
        avatarCore.setAttribute('fill', '#EF4444');
        primaryBtn.textContent = (data.avatarGuidance && data.avatarGuidance.recommendedActionPrimary) || 'Tutup Halaman Ini';
        primaryBtn.className = 'btn btn-danger';
        primaryBtn.style.display = 'inline-flex';
      } else if (isMediumRisk) {
        orb.classList.add('medium-risk');
        card.classList.remove('high-risk-border');
        avatarShield.setAttribute('stroke', '#F59E0B');
        avatarShield.setAttribute('fill', '#F59E0B');
        avatarShield.setAttribute('fill-opacity', '0.25');
        eyeLeft.setAttribute('fill', '#F59E0B');
        eyeRight.setAttribute('fill', '#F59E0B');
        avatarCore.setAttribute('fill', '#F59E0B');
        primaryBtn.textContent = (data.avatarGuidance && data.avatarGuidance.recommendedActionPrimary) || 'Waspada & Periksa';
        primaryBtn.className = 'btn btn-secondary';
        primaryBtn.style.display = 'inline-flex';
      } else {
        // Strict verified LOW risk branch only
        card.classList.remove('high-risk-border');
        avatarShield.setAttribute('stroke', '#06B6D4');
        avatarShield.setAttribute('fill', '#0EA5E9');
        avatarShield.setAttribute('fill-opacity', '0.2');
        eyeLeft.setAttribute('fill', '#10B981');
        eyeRight.setAttribute('fill', '#10B981');
        avatarCore.setAttribute('fill', '#10B981');
        primaryBtn.style.display = 'none';
      }

      if (typeof sendResponse === 'function') sendResponse({ received: true });

      // Populate Indicators Safely without innerHTML
      if (data.detectionIndicators && data.detectionIndicators.length > 0) {
        indicatorsBox.textContent = '';
        data.detectionIndicators.forEach((ind) => {
          const item = document.createElement('div');
          item.className = 'indicator-item';

          const dot = document.createElement('span');
          dot.className = 'indicator-dot';
          dot.style.background = (data.avatarGuidance && data.avatarGuidance.accentColor) ? data.avatarGuidance.accentColor : '#ef4444';

          const textSpan = document.createElement('span');
          const titleStrong = document.createElement('strong');
          titleStrong.textContent = (ind.indicator || '') + ': ';
          titleStrong.style.display = 'inline';
          const explText = document.createTextNode(ind.explanation || '');

          textSpan.appendChild(titleStrong);
          textSpan.appendChild(explText);

          item.appendChild(dot);
          item.appendChild(textSpan);
          indicatorsBox.appendChild(item);
        });
        indicatorsBox.style.display = 'flex';
      } else {
        indicatorsBox.style.display = 'none';
      }

      // Store and trigger Voice Warning
      if (data.avatarGuidance && data.avatarGuidance.speechText) {
        currentVoiceWarning = data.avatarGuidance.speechText;
        speakVoiceWarning(currentVoiceWarning);
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
