import React, { useState } from "react";
import { Volume2, VolumeX, Type, Eye, Sparkles } from "lucide-react";
import { DarkModeToggle } from "./DarkModeToggle";

interface A11yBarProps {
  onReadAloud?: (enabled: boolean) => void;
  speechRate?: number;
  onSpeechRateChange?: (rate: number) => void;
  isSpeaking?: boolean;
  onStopSpeech?: () => void;
}

export const A11yBar: React.FC<A11yBarProps> = ({
  onReadAloud,
  speechRate = 1.0,
  onSpeechRateChange,
  isSpeaking = false,
  onStopSpeech,
}) => {
  const [lexendActive, setLexendActive] = useState<boolean>(false);
  const [readAloudActive, setReadAloudActive] = useState<boolean>(false);
  const [highContrastActive, setHighContrastActive] = useState<boolean>(false);

  const toggleLexend = () => {
    const next = !lexendActive;
    setLexendActive(next);
    if (typeof document !== "undefined") {
      if (next) {
        document.body.classList.add("font-lexend");
      } else {
        document.body.classList.remove("font-lexend");
      }
    }
  };

  const toggleReadAloud = () => {
    const next = !readAloudActive;
    setReadAloudActive(next);
    if (onReadAloud) {
      onReadAloud(next);
    }
    if (!next && onStopSpeech) {
      onStopSpeech();
    }
  };

  const toggleHighContrast = () => {
    const next = !highContrastActive;
    setHighContrastActive(next);
    if (typeof document !== "undefined") {
      if (next) {
        document.body.classList.add("high-contrast");
      } else {
        document.body.classList.remove("high-contrast");
      }
    }
  };

  return (
    <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
      {/* Title / Badge */}
      <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 font-medium">
        <Sparkles className="w-3.5 h-3.5 text-[#6A35D8]" />
        <span className="font-semibold text-slate-700 dark:text-slate-300">
          Accessibility Suite
        </span>
      </div>

      {/* Main Toggles Row */}
      <div className="flex flex-wrap items-center gap-2.5">
        {/* Toggle 1: Lexend font (dyslexia friendly) */}
        <button
          type="button"
          onClick={toggleLexend}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full font-semibold transition-all shadow-sm ${
            lexendActive
              ? "text-white shadow-[#6A35D8]/20 scale-105"
              : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700"
          }`}
          style={{
            backgroundColor: lexendActive ? "#6A35D8" : undefined,
          }}
          aria-pressed={lexendActive}
          title="Toggle Lexend font (dyslexia friendly)"
        >
          <Type className="w-3.5 h-3.5" />
          <span>Lexend Font (Dyslexia Friendly)</span>
          <span
            className={`w-2 h-2 rounded-full ${
              lexendActive ? "bg-white" : "bg-slate-300 dark:bg-slate-600"
            }`}
          />
        </button>

        {/* Toggle 2: Read Aloud (Web Speech API) */}
        <button
          type="button"
          onClick={toggleReadAloud}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full font-semibold transition-all shadow-sm ${
            readAloudActive
              ? "text-white shadow-[#F25C1E]/20 scale-105"
              : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700"
          }`}
          style={{
            backgroundColor: readAloudActive ? "#F25C1E" : undefined,
          }}
          aria-pressed={readAloudActive}
          title="Toggle Read Aloud using Web Speech API"
        >
          {isSpeaking ? (
            <Volume2 className="w-3.5 h-3.5 animate-pulse text-white" />
          ) : readAloudActive ? (
            <Volume2 className="w-3.5 h-3.5" />
          ) : (
            <VolumeX className="w-3.5 h-3.5" />
          )}
          <span>Read Aloud</span>
          <span
            className={`w-2 h-2 rounded-full ${
              readAloudActive
                ? isSpeaking
                  ? "bg-white animate-ping"
                  : "bg-white"
                : "bg-slate-300 dark:bg-slate-600"
            }`}
          />
        </button>

        {/* Speed Selector (if onSpeechRateChange provided) */}
        {onSpeechRateChange && (
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 rounded-full px-2 py-1 border border-slate-200 dark:border-slate-700">
            <span className="text-[10px] text-slate-400 font-medium ml-1">Speed:</span>
            {[0.8, 1.0, 1.2].map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => onSpeechRateChange(r)}
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold transition-colors ${
                  speechRate === r
                    ? "bg-[#6A35D8] text-white"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                }`}
              >
                {r}x
              </button>
            ))}
          </div>
        )}

        {/* High Contrast Toggle */}
        <button
          type="button"
          onClick={toggleHighContrast}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full font-medium transition-all ${
            highContrastActive
              ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 border border-slate-200 dark:border-slate-700"
          }`}
          title="Toggle High Contrast Mode"
        >
          <Eye className="w-3.5 h-3.5" />
          <span className="text-[11px]">Contrast</span>
        </button>

        {/* Theme Dark Mode Toggle */}
        <DarkModeToggle showLabel={true} />
      </div>
    </div>
  );
};

export default A11yBar;
