import React from 'react';
import { ThreatDistribution } from '../types';

interface ThreatRadarProps {
  distribution: ThreatDistribution[];
}

export const ThreatRadar: React.FC<ThreatRadarProps> = ({ distribution }) => {
  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6">
      <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2">
        <span>🎯</span> Distribusi Kategori Ancaman
      </h3>
      <p className="text-xs text-slate-400 mb-6">Pola klasifikasi ancaman siber yang teridentifikasi</p>

      <div className="space-y-4">
        {distribution.map((item, idx) => (
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
  );
};

