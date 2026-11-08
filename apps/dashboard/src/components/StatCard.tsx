import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  icon: string;
  variant?: 'default' | 'danger' | 'warning' | 'success';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  variant = 'default'
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return 'border-rose-950/60 hover:border-rose-800/80 text-rose-400 bg-rose-950/60';
      case 'warning':
        return 'border-amber-950/60 hover:border-amber-800/80 text-amber-400 bg-amber-950/60';
      case 'success':
        return 'border-emerald-950/60 hover:border-emerald-800/80 text-emerald-400 bg-emerald-950/60';
      default:
        return 'border-slate-800 hover:border-slate-700 text-cyan-400 bg-slate-800';
    }
  };

  return (
    <div className={`bg-slate-900/80 border rounded-xl p-5 transition-all ${getVariantStyles().split(' ')[0]} ${getVariantStyles().split(' ')[1]}`}>
      <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
        <span>{title}</span>
        <span className={`p-2 rounded-lg text-sm ${getVariantStyles().split(' ').slice(2).join(' ')}`}>{icon}</span>
      </div>
      <div className="text-2xl font-bold text-white mt-3">{value}</div>
      <div className="text-xs text-slate-400 mt-1">{subtitle}</div>
    </div>
  );
};

