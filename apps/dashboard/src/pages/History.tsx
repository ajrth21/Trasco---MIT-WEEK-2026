import React, { useState } from 'react';
import { ScanHistoryItem } from '../types';

interface HistoryProps {
  items: ScanHistoryItem[];
  onRefresh: () => void;
}

export const History: React.FC<HistoryProps> = ({ items, onRefresh }) => {
  const [filter, setFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN'>('ALL');
  const [selectedItem, setSelectedItem] = useState<ScanHistoryItem | null>(null);

  const filteredItems = items.filter((item) => {
    if (filter === 'ALL') return true;
    return item.riskLevel === filter;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>🗂️</span> Riwayat & Log Forensik Ancaman
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Rekam jejak setiap URL, percakapan teks, dan gambar yang dipindai oleh TRASCO
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
            {(['ALL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilter(lvl)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  filter === lvl
                    ? lvl === 'HIGH'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : lvl === 'MEDIUM'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : lvl === 'LOW'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : lvl === 'UNKNOWN'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
          <button
            onClick={onRefresh}
            className="p-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-300 hover:text-white hover:border-slate-700 transition-all text-xs"
            title="Refresh Data"
          >
            🔄
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Tipe Scan</th>
                <th className="py-3.5 px-4">Konten / Snippet Target</th>
                <th className="py-3.5 px-4">Kategori Ancaman</th>
                <th className="py-3.5 px-4">Risk Level</th>
                <th className="py-3.5 px-4">Waktu</th>
                <th className="py-3.5 px-4 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Tidak ada log pemindaian yang cocok dengan filter saat ini.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-semibold">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
                        {item.scanType}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 max-w-xs truncate font-mono text-slate-300">
                      {item.sanitizedSnippet}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      {item.threatCategory || 'PERIKSA MANUAL'}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-bold text-[10px] ${
                          item.riskLevel === 'HIGH'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                            : item.riskLevel === 'MEDIUM' || item.riskLevel === 'UNKNOWN' || item.riskScore === null
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            item.riskLevel === 'HIGH'
                              ? 'bg-rose-400'
                              : item.riskLevel === 'MEDIUM' || item.riskLevel === 'UNKNOWN' || item.riskScore === null
                              ? 'bg-amber-400'
                              : 'bg-emerald-400'
                          }`}
                        ></span>
                        {item.riskLevel} ({item.riskScore === null ? 'Verifikasi Manual' : item.riskScore})
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {item.createdAt}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => setSelectedItem(item)}
                        className="px-2.5 py-1 rounded bg-slate-800 text-cyan-300 hover:bg-slate-700 border border-slate-700 transition-all font-semibold text-[11px]"
                      >
                        Detail
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Inspector */}
      {selectedItem && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedItem(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-lg font-bold"
            >
              ✕
            </button>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">🛡️</span>
              <h3 className="text-lg font-bold text-white">Rincian Forensik Deteksi</h3>
            </div>

            <div className="space-y-4 text-xs text-slate-300">
              <div>
                <span className="text-slate-500 font-semibold uppercase tracking-wider block mb-1">
                  Target Snippet
                </span>
                <div className="p-3 bg-slate-950 rounded-lg font-mono text-cyan-300 break-words border border-slate-800">
                  {selectedItem.sanitizedSnippet}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-slate-500 font-semibold uppercase tracking-wider block mb-1">
                    Klasifikasi
                  </span>
                  <div className="font-semibold text-slate-200">                  {selectedItem.threatCategory || 'PERIKSA MANUAL'}</div>
                </div>
                <div>
                  <span className="text-slate-500 font-semibold uppercase tracking-wider block mb-1">
                    Tingkat Risiko
                  </span>
                  <div className="font-bold text-rose-400">
                    {selectedItem.riskLevel} ({selectedItem.riskScore === null ? 'Verifikasi Manual' : `${selectedItem.riskScore}/100`})
                  </div>
                </div>
              </div>

              <div className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-lg">
                <p className="text-rose-300 leading-relaxed">
                  Aktivitas ini ditandai karena memenuhi pola ancaman siber berbahaya. Jangan membagikan informasi kredensial atau mentransfer dana apa pun.
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-all"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
