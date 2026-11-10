import React from 'react';
import { SecurityOverviewData } from '../types';
import { StatCard, ThreatRadar } from '../components';

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

      {/* 4 Modular Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Pemindaian"
          value={riskBreakdown.totalScans}
          subtitle="Aktivitas URL, Teks, & Gambar"
          icon="🔍"
          variant="default"
        />
        <StatCard
          title="Ancaman Kritis Dicegah"
          value={riskBreakdown.highRiskCount}
          subtitle="Skema OTP & lowongan fiktif"
          icon="🚨"
          variant="danger"
        />
        <StatCard
          title="Peringatan Waspada"
          value={riskBreakdown.mediumRiskCount}
          subtitle="Indikasi rekayasa sosial"
          icon="⚠️"
          variant="warning"
        />
        <StatCard
          title="Aktivitas Aman"
          value={riskBreakdown.lowRiskCount}
          subtitle="Terverifikasi kredibel"
          icon="✅"
          variant="success"
        />
      </div>

      {/* Two Column Layout: Threat Distribution & Weekly Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Threat Distribution Component */}
        <ThreatRadar distribution={threatDistribution} />

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
                  <div className="w-full max-w-[36px] h-36 bg-slate-800 rounded-t-lg relative overflow-hidden flex items-end">
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
