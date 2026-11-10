import React, { useState } from 'react';
import { scanContent } from '../services/api';
import { AnalyzeResponse } from '../types';

export const Simulator: React.FC = () => {
  const [scanType, setScanType] = useState<'TEXT' | 'URL'>('TEXT');
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const PRESET_SAMPLES = [
    {
      label: '🚨 Scam Kerja Like Video & Deposit',
      type: 'TEXT' as const,
      content:
        'Selamat siang kak! Kami dari agensi digital membuka lowongan kerja freelance like video TikTok. Komisi 500rb per hari langsung cair! Syarat cukup transfer biaya deposit jaminan 50rb ke Rek BCA 8820129381 dan kirimkan kode OTP yang masuk ke nomor WA Anda.'
    },
    {
      label: '🎣 Phishing Domain Bank BCA Palsu',
      type: 'URL' as const,
      content: 'https://klikbca-verifikasi-gebyar-hadiah.xyz/login'
    },
    {
      label: '🔑 Pencurian Kode OTP via CS Palsu',
      type: 'TEXT' as const,
      content:
        'Pemberitahuan Resmi: Akun DANA Anda terindikasi login mencurigakan. Segera kirimkan 6 digit kode OTP rahasia yang baru saja kami kirimkan melalui SMS dalam waktu 5 menit atau rekening akan diblokir permanen.'
    },
    {
      label: '📦 Modus Undangan/Paket APK',
      type: 'TEXT' as const,
      content:
        'Halo paket atas nama Anda tertahan di gudang J&T. Silakan klik dan instal file resi paket ini untuk konfirmasi: Resi_Paket_JNT_Express.apk'
    },
    {
      label: '✅ Website Resmi BCA (Aman)',
      type: 'URL' as const,
      content: 'https://www.klikbca.com'
    },
    {
      label: '✅ Pesan Chat Normal (Aman)',
      type: 'TEXT' as const,
      content: 'Hai selamat pagi, apakah besok kita jadi rapat koordinasi proyek jam 9 di kantor?'
    }
  ];

  const handleRunScan = async (overrideContent?: string, overrideType?: 'TEXT' | 'URL') => {
    const textToScan = overrideContent || inputText;
    const typeToScan = overrideType || scanType;

    if (!textToScan.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await scanContent(typeToScan, textToScan);
      setResult(res);

      // Play audio TTS demo if available
      if ('speechSynthesis' in window && res.avatarGuidance?.speechText) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(res.avatarGuidance.speechText);
        utterance.lang = 'id-ID';
        window.speechSynthesis.speak(utterance);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Gagal menghubungi backend TRASCO');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
          <span>⚡</span> Live Threat Detection & Avatar Simulator
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Uji coba langsung keandalan TRASCO AI Detection Engine dan saksikan reaksi intervensi Cyber Guardian secara real-time.
        </p>
      </div>

      {/* Preset Quick Test Buttons */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
          Pilih Skenario Kasus Uji Cepat:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {PRESET_SAMPLES.map((sample, idx) => (
            <button
              key={idx}
              onClick={() => {
                setScanType(sample.type);
                setInputText(sample.content);
                handleRunScan(sample.content, sample.type);
              }}
              className="p-3 text-left rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-800/80 transition-all text-xs font-medium text-slate-200 flex flex-col justify-between group"
            >
              <span className="font-semibold text-white group-hover:text-cyan-300">
                {sample.label}
              </span>
              <span className="text-[11px] text-slate-400 truncate mt-1">
                {sample.content}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setScanType('TEXT')}
              className={`px-3 py-1 rounded-md transition-all ${
                scanType === 'TEXT' ? 'bg-cyan-500 text-white' : 'text-slate-400'
              }`}
            >
              💬 Teks Pesan / Chat
            </button>
            <button
              onClick={() => setScanType('URL')}
              className={`px-3 py-1 rounded-md transition-all ${
                scanType === 'URL' ? 'bg-cyan-500 text-white' : 'text-slate-400'
              }`}
            >
              🔗 Tautan / URL
            </button>
          </div>

          <span className="text-[11px] text-slate-400">
            Engine: Hybrid (Heuristic + Gemini AI)
          </span>
        </div>

        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={
            scanType === 'TEXT'
              ? 'Ketik atau tempel teks pesan penawaran kerja, SMS berhadiah, atau chat mencurigakan di sini...'
              : 'Masukkan URL yang ingin dianalisis, contoh: https://klikbca-palsu.xyz/login'
          }
          rows={4}
          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-all font-mono"
        ></textarea>

        <div className="flex justify-end">
          <button
            onClick={() => handleRunScan()}
            disabled={loading || !inputText.trim()}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 disabled:opacity-50 text-white font-bold text-xs sm:text-sm shadow-lg shadow-cyan-500/20 transition-all flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="animate-spin">🌀</span>
                <span>Menganalisis Ancaman...</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>Jalankan Pemindaian AI</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
          ⚠️ {error}
        </div>
      )}

      {/* Real-Time Detection Result & Avatar Presentation */}
      {result && (
        <div
          className={`rounded-2xl border p-6 sm:p-8 shadow-2xl transition-all animate-fadeIn ${
            result.riskLevel === 'HIGH'
              ? 'bg-gradient-to-b from-rose-950/20 to-slate-900 border-rose-900/60'
              : result.riskLevel === 'MEDIUM' || result.status !== 'COMPLETED'
              ? 'bg-gradient-to-b from-amber-950/20 to-slate-900 border-amber-900/60'
              : 'bg-gradient-to-b from-emerald-950/20 to-slate-900 border-emerald-900/60'
          }`}
        >
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-slate-800">
            {/* Guardian Avatar Reaction */}
            <div className="flex items-center gap-4">
              <div
                className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shadow-lg ${
                  result.riskLevel === 'HIGH'
                    ? 'bg-rose-500/20 border-2 border-rose-500 text-rose-400 shadow-rose-500/20 animate-bounce'
                    : result.riskLevel === 'MEDIUM' || result.status !== 'COMPLETED'
                    ? 'bg-amber-500/20 border-2 border-amber-500 text-amber-400 shadow-amber-500/20'
                    : 'bg-emerald-500/20 border-2 border-emerald-500 text-emerald-400 shadow-emerald-500/20'
                }`}
              >
                {result.riskLevel === 'HIGH' ? '🛡️' : result.riskLevel === 'MEDIUM' || result.status !== 'COMPLETED' ? '⚠️' : '🤖'}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${
                      result.riskLevel === 'HIGH'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                        : result.riskLevel === 'MEDIUM' || result.status !== 'COMPLETED'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    }`}
                  >
                    {result.riskLevel} RISK • SKOR: {result.riskScore === null ? 'Verifikasi Manual' : `${result.riskScore}/100`}
                  </span>
                  <span className="text-xs text-slate-400">
                    Kategori: {(result.threatCategory || 'PERIKSA MANUAL').replace(/_/g, ' ')}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mt-1">
                  Intervensi AI Avatar: "{result.avatarGuidance.speechText}"
                </h3>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[11px] text-slate-400 block">Waktu Analisis</span>
              <span className="text-xs font-mono text-cyan-300 font-semibold">
                {result.latencyMs === null || result.latencyMs === undefined ? '—' : `${result.latencyMs} ms`}
              </span>
            </div>
          </div>

          {result.status !== 'COMPLETED' && (
            <div className="mt-4 p-3 rounded-lg bg-amber-950/30 border border-amber-900/50 text-xs text-amber-200">
              <strong>Analisis belum selesai.</strong> {result.summary}
              {result.error?.message && <span> {result.error.message}</span>}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            {/* Indicators */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Bukti & Indikator Deteksi ({result.detectionIndicators.length})
              </h4>
              {result.detectionIndicators.length === 0 ? (
                <p className="text-xs text-slate-400 italic">
                  Tidak ditemukan indikator berbahaya pada input ini.
                </p>
              ) : (
                <div className="space-y-2">
                  {result.detectionIndicators.map((ind, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white">{ind.indicator}</span>
                        <span className="text-[10px] uppercase font-bold text-rose-400">
                          {ind.severity}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px]">{ind.explanation}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recommendations */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Rekomendasi Tindakan Pengguna
              </h4>
              <div className="space-y-2">
                {result.recommendedActions.map((action, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs flex items-start gap-2.5"
                  >
                    <span className="text-cyan-400 font-bold">✓</span>
                    <span className="text-slate-300 leading-relaxed">{action}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
