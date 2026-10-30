import React from 'react';
import { ConfusionData, ConfusionState } from '../types/api';
import { Sparkles, AlertCircle, HelpCircle, Activity } from 'lucide-react';

interface ConfusionMeterProps {
  data: ConfusionData;
  isWsConnected?: boolean;
}

export const ConfusionMeter: React.FC<ConfusionMeterProps> = ({ data, isWsConnected = false }) => {
  const { score, state, reasons } = data;
  const percentage = Math.round(score * 100);

  // Determine color scheme based on state
  const stateConfig: Record<
    ConfusionState,
    { label: string; bg: string; text: string; stroke: string; dot: string; icon: any }
  > = {
    focused: {
      label: 'Focused & Flowing',
      bg: 'bg-emerald-500/10 dark:bg-emerald-500/20',
      text: 'text-emerald-700 dark:text-emerald-400',
      stroke: '#10b981',
      dot: 'bg-emerald-500',
      icon: Sparkles,
    },
    hesitant: {
      label: 'Processing / Hesitant',
      bg: 'bg-amber-500/10 dark:bg-amber-500/20',
      text: 'text-amber-700 dark:text-amber-400',
      stroke: '#f59e0b',
      dot: 'bg-amber-500',
      icon: Activity,
    },
    confused: {
      label: 'Confusion Detected',
      bg: 'bg-rose-500/10 dark:bg-rose-500/20',
      text: 'text-rose-700 dark:text-rose-400',
      stroke: '#ef4444',
      dot: 'bg-rose-500',
      icon: AlertCircle,
    },
  };

  const currentCfg = stateConfig[state] || stateConfig.focused;
  const StateIcon = currentCfg.icon;

  // Arc calculation for semi-circle gauge (radius = 50, stroke = 10)
  const radius = 50;
  const circumference = Math.PI * radius; // 157.08
  const strokeDashoffset = circumference - (score * circumference);

  return (
    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-sm hover:shadow-md transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold tracking-wider uppercase text-slate-500 dark:text-slate-400">
            Cognitive State Meter
          </span>
          {isWsConnected && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-1.5 py-0.5 rounded-full font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Live WS
            </span>
          )}
        </div>
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${currentCfg.bg} ${currentCfg.text}`}>
          <span className={`w-2 h-2 rounded-full ${currentCfg.dot}`}></span>
          <StateIcon className="w-3.5 h-3.5" />
          <span>{currentCfg.label}</span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Semi-circle Gauge */}
        <div className="relative w-32 h-20 flex-shrink-0 flex items-end justify-center">
          <svg className="w-32 h-20 overflow-visible" viewBox="0 0 120 70">
            {/* Background Arc */}
            <path
              d="M 10 65 A 50 50 0 0 1 110 65"
              fill="none"
              stroke="currentColor"
              className="text-slate-200 dark:text-slate-800"
              strokeWidth="10"
              strokeLinecap="round"
            />
            {/* Value Arc */}
            <path
              d="M 10 65 A 50 50 0 0 1 110 65"
              fill="none"
              stroke={currentCfg.stroke}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-700 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
            <span className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              {percentage}%
            </span>
            <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500">
              Confusion
            </span>
          </div>
        </div>

        {/* Diagnostic Reasons Breakdown */}
        <div className="flex-1 min-w-0">
          <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1.5">
            Diagnostic Triggers:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {reasons && reasons.length > 0 ? (
              reasons.map((reason, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/50 dark:border-slate-700/50 animate-fade-in font-mono text-[11px]"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500"></span>
                  {reason}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-400 dark:text-slate-500 italic">
                Smooth interaction • No hesitation flags
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
