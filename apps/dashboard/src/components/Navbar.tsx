import React from 'react';

interface NavbarProps {
  currentTab: 'overview' | 'history' | 'simulator';
  onSelectTab: (tab: 'overview' | 'history' | 'simulator') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-500 p-0.5 shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <span className="text-xl">🛡️</span>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-emerald-400">
                TRASCO
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300">
                Cyber Shield
              </span>
            </div>
            <p className="text-xs text-slate-400">Personal Scam Insight & Threat Analytics</p>
          </div>
        </div>

        <nav className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => onSelectTab('overview')}
            className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              currentTab === 'overview'
                ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-inner'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            📊 Security Overview
          </button>
          <button
            onClick={() => onSelectTab('history')}
            className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              currentTab === 'history'
                ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-inner'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            🗂️ Riwayat Pemindaian
          </button>
          <button
            onClick={() => onSelectTab('simulator')}
            className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
              currentTab === 'simulator'
                ? 'bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-200 border border-cyan-400/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            ⚡ Live Scam Simulator
          </button>
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            Guardian Online
          </div>
        </div>
      </div>
    </header>
  );
};

