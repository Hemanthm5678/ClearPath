import React, { useState, useEffect } from 'react';
import { 
  Type, 
  Contrast, 
  Volume2, 
  Sun, 
  Moon, 
  ShieldCheck, 
  Sparkles,
  ZoomIn
} from 'lucide-react';

interface A11yBarProps {
  speechRate: number;
  onSpeechRateChange: (rate: number) => void;
}

export const A11yBar: React.FC<A11yBarProps> = ({ speechRate, onSpeechRateChange }) => {
  const [isDyslexic, setIsDyslexic] = useState(false);
  const [isHighContrast, setIsHighContrast] = useState(false);
  const [isLargeText, setIsLargeText] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Toggle Dyslexic Font
  const toggleDyslexic = () => {
    const next = !isDyslexic;
    setIsDyslexic(next);
    if (next) {
      document.body.classList.add('font-dyslexic');
    } else {
      document.body.classList.remove('font-dyslexic');
    }
  };

  // Toggle High Contrast
  const toggleContrast = () => {
    const next = !isHighContrast;
    setIsHighContrast(next);
    if (next) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }
  };

  // Toggle Large Text
  const toggleLargeText = () => {
    const next = !isLargeText;
    setIsLargeText(next);
    if (next) {
      document.body.classList.add('text-lg-mode');
    } else {
      document.body.classList.remove('text-lg-mode');
    }
  };

  // Toggle Dark Mode
  const toggleDark = () => {
    const next = !isDarkMode;
    setIsDarkMode(next);
    if (next) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs">
      {/* Privacy guarantee badge */}
      <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400 font-medium">
        <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
        <span className="hidden sm:inline">Privacy First:</span>
        <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-[11px] font-mono text-slate-700 dark:text-slate-300">
          No Camera • No Mic • Only Timing & Counts
        </span>
      </div>

      {/* Accessibility Controls */}
      <div className="flex items-center gap-2">
        {/* Dyslexia font button */}
        <button
          onClick={toggleDyslexic}
          title="Toggle Dyslexia-friendly Font"
          className={`px-2.5 py-1 rounded-lg border font-medium flex items-center gap-1.5 transition-colors ${
            isDyslexic 
              ? 'bg-brand-500 text-white border-brand-600' 
              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200'
          }`}
        >
          <Type className="w-3.5 h-3.5" />
          <span>Dyslexia Font</span>
        </button>

        {/* High contrast button */}
        <button
          onClick={toggleContrast}
          title="Toggle High Contrast"
          className={`px-2.5 py-1 rounded-lg border font-medium flex items-center gap-1.5 transition-colors ${
            isHighContrast 
              ? 'bg-brand-500 text-white border-brand-600' 
              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200'
          }`}
        >
          <Contrast className="w-3.5 h-3.5" />
          <span>Contrast</span>
        </button>

        {/* Larger Text button */}
        <button
          onClick={toggleLargeText}
          title="Toggle Larger Text"
          className={`px-2.5 py-1 rounded-lg border font-medium flex items-center gap-1.5 transition-colors ${
            isLargeText 
              ? 'bg-brand-500 text-white border-brand-600' 
              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200'
          }`}
        >
          <ZoomIn className="w-3.5 h-3.5" />
          <span>Text+</span>
        </button>

        {/* Speech Rate Selector */}
        <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-700">
          <Volume2 className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-[11px] text-slate-500">Voice:</span>
          <select
            value={speechRate}
            onChange={(e) => onSpeechRateChange(parseFloat(e.target.value))}
            className="bg-transparent text-slate-700 dark:text-slate-200 text-xs font-medium focus:outline-none cursor-pointer"
          >
            <option value={0.8} className="dark:bg-slate-900">0.8x (Gentle)</option>
            <option value={1.0} className="dark:bg-slate-900">1.0x (Normal)</option>
            <option value={1.2} className="dark:bg-slate-900">1.2x (Fast)</option>
          </select>
        </div>

        {/* Dark Mode Toggle */}
        <button
          onClick={toggleDark}
          title="Toggle Dark Mode"
          className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          {isDarkMode ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-slate-600" />}
        </button>
      </div>
    </div>
  );
};
