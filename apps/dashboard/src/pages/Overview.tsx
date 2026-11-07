import React from 'react';
import { SecurityOverviewData } from '../types';

interface OverviewProps {
  data: SecurityOverviewData | null;
  onOpenSimulator: () => void;
}

export const Overview: React.FC<OverviewProps> = ({ data, onOpenSimulator }) => {
  if (!data) {
    return (
      <div className="py-24 text-center text-slate-400">
        <div className="animate-spin text-4xl mb-4">🛡️</div>
        Memuat data analitik keamanan...
      </div>
    );
  }

  const { securityHygieneScore, riskBreakdown, threatDistribution, weeklyTrends, keyAdvice } = data;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner: Hygiene Score & Quick Call-To-Action */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 p-6 sm:p-8 shadow-xl">
        <div className="absolute right-0 top-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
        <div className="flex flex-col lg:flex-row items-center justify-between gap-6 relative z-10">
          <div className="flex flex-col sm:flex-row items-center gap-6">
            {/* Score Ring */}
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="#1e293b"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke={securityHygieneScore >= 80 ? '#10b981' : securityHygieneScore >= 60 ? '#f59e0b' : '#ef4444'}
                  strokeWidth="8"
                  strokeDasharray="251.2"
                  strokeDashoffset={251.2 - (251.2 * securityHygieneScore) / 100}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="text-3xl font-extrabold text-white">{securityHygieneScore}</span>
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Skor Higienis</span>
              </div>
            </div>

            <div className="text-center sm:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 mb-2">
                <span>🛡️</span>
                Status Keamanan: {securityHygieneScore >= 80 ? 'SANGAT TERLINDUNGI' : 'PERLU PERHATIAN'}
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-white">
                Personal Scam Shield Aktif
              </h2>
              <p className="text-sm text-slate-400 max-w-lg mt-1">
                AI Cyber Guardian terus memantau transaksi, URL berisiko, dan manipulasi sosial untuk melindungi Anda dari jebakan digital penipuan.
              </p>
            </div>
          </div>

          <button
            onClick={onOpenSimulator}
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold text-sm bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white shadow-lg shadow-cyan-500/25 transition-all flex items-center justify-center gap-2"
          >
            <span>⚡ Uji Penipuan di Simulator</span>
          </button>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Total Pemindaian</span>
            <span className="p-2 rounded-lg bg-slate-800 text-cyan-400">🔍</span>
          </div>
          <div className="text-2xl font-bold text-white mt-3">{riskBreakdown.totalScans}</div>
          <div className="text-xs text-slate-400 mt-1">Aktivitas URL, Teks, & Gambar</div>
        </div>

        <div className="bg-slate-900/80 border border-rose-950/60 rounded-xl p-5 hover:border-rose-800/80 transition-all">
          <div className="flex items-center justify-between text-rose-400 text-xs font-semibold uppercase tracking-wider">
            <span>Ancaman Kritis Dicegah</span>
            <span className="p-2 rounded-lg bg-rose-950/60 text-rose-400">🚨</span>
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-3">{riskBreakdown.highRiskCount}</div>
          <div className="text-xs text-slate-400 mt-1">Skema OTP & lowongan fiktif</div>
        </div>

        <div className="bg-slate-900/80 border border-amber-950/60 rounded-xl p-5 hover:border-amber-800/80 transition-all">
          <div className="flex items-center justify-between text-amber-400 text-xs font-semibold uppercase tracking-wider">
            <span>Peringatan Waspada</span>
            <span className="p-2 rounded-lg bg-amber-950/60 text-amber-400">⚠️</span>
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-3">{riskBreakdown.mediumRiskCount}</div>
          <div className="text-xs text-slate-400 mt-1">Indikasi rekayasa sosial</div>
        </div>

        <div className="bg-slate-900/80 border border-emerald-950/60 rounded-xl p-5 hover:border-emerald-800/80 transition-all">
          <div className="flex items-center justify-between text-emerald-400 text-xs font-semibold uppercase tracking-wider">
            <span>Aktivitas Aman</span>
            <span className="p-2 rounded-lg bg-emerald-950/60 text-emerald-400">✅</span>
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-3">{riskBreakdown.lowRiskCount}</div>
          <div className="text-xs text-slate-400 mt-1">Terverifikasi kredibel</div>
        </div>
      </div>

      {/* Two Column Layout: Threat Distribution & Weekly Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Threat Distribution */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2">
            <span>🎯</span> Distribusi Kategori Ancaman
          </h3>
          <p className="text-xs text-slate-400 mb-6">Pola klasifikasi ancaman siber yang teridentifikasi</p>

          <div className="space-y-4">
            {threatDistribution.map((item, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-300">{item.category}</span>
                  <span className="text-slate-400">{item.count} deteksi ({item.percentage}%)</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      item.category === 'SAFE'
                        ? 'bg-emerald-500'
                        : item.category.includes('JOB') || item.category.includes('OTP')
                        ? 'bg-rose-500'
                        : 'bg-amber-500'
                    }`}
                    style={{ width: `${item.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly Trend Chart */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2">
            <span>📈</span> Tren Pemindaian Mingguan
          </h3>
          <p className="text-xs text-slate-400 mb-6">Aktivitas deteksi 7 hari terakhir</p>

          <div className="h-48 flex items-end justify-between gap-2 pt-6">
            {weeklyTrends.map((trend, i) => {
              const maxScans = Math.max(...weeklyTrends.map((t) => t.scans), 6);
              const heightPct = Math.max(15, (trend.scans / maxScans) * 100);

              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                  <div className="text-[10px] text-cyan-300 font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                    {trend.scans} scan
                  </div>
                  <div className="w-full max-w-[36px] bg-slate-800 rounded-t-lg relative overflow-hidden flex items-end">
                    <div
                      className="w-full bg-gradient-to-t from-cyan-600 to-sky-400 rounded-t-lg transition-all duration-500"
                      style={{ height: `${heightPct}%` }}
                    ></div>
                    {trend.threatsPrevented > 0 && (
                      <div className="absolute top-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-rose-400 animate-ping"></div>
                    )}
                  </div>
                  <span className="text-xs font-semibold text-slate-400">{trend.date}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Key Personalized Security Advice */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <span>💡</span> Rekomendasi Mitigasi Keamanan Utama
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {keyAdvice.map((advice, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-800/40 border border-slate-800/60 flex items-start gap-3"
            >
              <div className="w-7 h-7 rounded-lg bg-cyan-950/80 border border-cyan-800 text-cyan-400 flex items-center justify-center flex-shrink-0 text-sm font-bold">
                {idx + 1}
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{advice}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

