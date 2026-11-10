import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Overview } from './pages/Overview';
import { History } from './pages/History';
import { Simulator } from './pages/Simulator';
import { fetchSecurityOverview, fetchFullHistory } from './services/api';
import { SecurityOverviewData, ScanHistoryItem } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'overview' | 'history' | 'simulator'>('overview');
  const [overviewData, setOverviewData] = useState<SecurityOverviewData | null>(null);
  const [historyItems, setHistoryItems] = useState<ScanHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const overview = await fetchSecurityOverview();
      setOverviewData(overview);
      if (overview.recentHistory) {
        setHistoryItems(overview.recentHistory);
      }
    } catch (err: any) {
      console.error('Failed to load dashboard data', err);
      setErrorMsg(err.message || 'Gagal terhubung ke backend engine port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-[#0B0F19] flex flex-col text-slate-100">
      <Navbar currentTab={currentTab} onSelectTab={setCurrentTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-base">🚨</span>
              <span><strong>Backend Offline / Error:</strong> {errorMsg}. Pastikan TRASCO backend aktif pada port 8000.</span>
            </div>
            <button onClick={loadData} className="px-3 py-1 bg-rose-900/60 hover:bg-rose-800 text-white rounded-lg font-semibold transition-all">
              Coba Lagi
            </button>
          </div>
        )}
        {currentTab === 'overview' && (
          <Overview
            data={overviewData}
            onOpenSimulator={() => setCurrentTab('simulator')}
          />
        )}

        {currentTab === 'history' && (
          <History
            items={historyItems}
            onRefresh={loadData}
          />
        )}

        {currentTab === 'simulator' && <Simulator />}
      </main>

      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-cyan-400 font-bold">TRASCO</span>
            <span>—</span>
            <span>Trap & Scope Cybersecurity Ecosystem</span>
          </div>
          <p>Didesain untuk Hackathon Web Development (Cybersecurity Track) MIT UNMUL 2026</p>
        </div>
      </footer>
    </div>
  );
};

