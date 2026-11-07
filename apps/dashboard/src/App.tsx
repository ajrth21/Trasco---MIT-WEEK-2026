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

  const loadData = async () => {
    setLoading(true);
    try {
      const overview = await fetchSecurityOverview();
      setOverviewData(overview);
      if (overview.recentHistory) {
        setHistoryItems(overview.recentHistory);
      }
    } catch (err) {
      console.error('Failed to load dashboard data', err);
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

