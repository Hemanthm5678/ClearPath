import React, { useState } from 'react';
import { TutorData } from '../types/api';
import { 
  Bot, 
  Volume2, 
  VolumeX, 
  Eye, 
  Lightbulb, 
  ListOrdered, 
  Smile, 
  Send, 
  CheckCircle2, 
  XCircle,
  Database,
  CloudLightning,
  Sparkles
} from 'lucide-react';

interface TutorBubbleProps {
  tutor: TutorData;
  sessionId: string;
  conceptId?: string;
  onStyleSelect: (style: 'visual' | 'analogy' | 'step_by_step' | 'simple_language') => void;
  currentStyle: string;
  onSpeak: (text: string) => void;
  isSpeaking: boolean;
  onCancelSpeech: () => void;
}

export const TutorBubble: React.FC<TutorBubbleProps> = ({
  tutor,
  sessionId,
  conceptId,
  onStyleSelect,
  currentStyle,
  onSpeak,
  isSpeaking,
  onCancelSpeech,
}) => {
  const [checkAnswerInput, setCheckAnswerInput] = useState('');
  const [checkStatus, setCheckStatus] = useState<'idle' | 'correct' | 'try_again'>('idle');

  // Follow-up chat state
  const [chatMessage, setChatMessage] = useState('');
  const [chatReplies, setChatReplies] = useState<Array<{ sender: 'user' | 'tutor'; text: string }>>([]);
  const [isSendingChat, setIsSendingChat] = useState(false);

  const handleCheckAnswer = (e: React.FormEvent) => {
    e.preventDefault();
    if (!checkAnswerInput.trim()) return;

    // Simple heuristic validation for demo
    const clean = checkAnswerInput.trim().toLowerCase();
    if (clean.includes('3/4') || clean.includes('numerator') || clean.includes('whole') || clean.includes('denominator') || clean.includes('yes') || clean.includes('no') || clean.includes('equal') || clean.includes('same')) {
      setCheckStatus('correct');
    } else {
      setCheckStatus('try_again');
    }
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim() || isSendingChat) return;

    const userText = chatMessage;
    setChatMessage('');
    setChatReplies((prev) => [...prev, { sender: 'user', text: userText }]);
    setIsSendingChat(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: userText,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setChatReplies((prev) => [...prev, { sender: 'tutor', text: data.reply }]);
        onSpeak(data.reply);
      }
    } catch (err) {
      setChatReplies((prev) => [
        ...prev,
        {
          sender: 'tutor',
          text: 'Remember: look closely at the numerator (parts you have) versus denominator (total parts in the whole).',
        },
      ]);
    } finally {
      setIsSendingChat(false);
    }
  };

  // Source badge config
  const sourceBadges = {
    groq: {
      label: 'Groq LLaMA 3.3',
      bg: 'bg-indigo-50 dark:bg-indigo-950/60',
      text: 'text-indigo-600 dark:text-indigo-400',
      icon: CloudLightning,
    },
    cache: {
      label: 'Fast Cache Hit',
      bg: 'bg-emerald-50 dark:bg-emerald-950/60',
      text: 'text-emerald-600 dark:text-emerald-400',
      icon: Sparkles,
    },
    offline_bank: {
      label: 'Guaranteed Offline Bank',
      bg: 'bg-amber-50 dark:bg-amber-950/60',
      text: 'text-amber-600 dark:text-amber-400',
      icon: Database,
    },
  };

  const sourceConfig = sourceBadges[tutor.source] || sourceBadges.offline_bank;
  const SourceIcon = sourceConfig.icon;

  return (
    <div className="bg-gradient-to-b from-white to-indigo-50/40 dark:from-slate-900 dark:to-slate-900/90 rounded-2xl border-2 border-brand-200 dark:border-brand-900/50 p-6 shadow-xl relative overflow-hidden animate-slide-up">
      {/* Top Banner & Source Badge */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500 text-white flex items-center justify-center shadow-md shadow-brand-500/20">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white text-base flex items-center gap-2">
              ClearPath Adaptive Tutor
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Personalized scaffolding based on real-time cognitive cues
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Source Badge */}
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${sourceConfig.bg} ${sourceConfig.text} border border-current/20`}>
            <SourceIcon className="w-3.5 h-3.5" />
            {sourceConfig.label}
          </span>

          {/* Text to Speech Button */}
          <button
            onClick={() => {
              if (isSpeaking) {
                onCancelSpeech();
              } else {
                onSpeak(`${tutor.explanation}. Check question: ${tutor.check_question}`);
              }
            }}
            className={`p-2 rounded-xl flex items-center gap-1.5 text-xs font-semibold transition-all ${
              isSpeaking
                ? 'bg-rose-500 text-white shadow-md shadow-rose-500/30 animate-pulse'
                : 'bg-brand-50 dark:bg-brand-950/50 text-brand-700 dark:text-brand-300 hover:bg-brand-100 dark:hover:bg-brand-900'
            }`}
            title={isSpeaking ? 'Stop Voice' : 'Listen with Audio'}
          >
            {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            <span>{isSpeaking ? 'Stop Voice' : 'Read Aloud'}</span>
          </button>
        </div>
      </div>

      {/* Style Modality Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Modality:
        </span>
        {[
          { id: 'visual', label: 'Visual Diagram', icon: Eye },
          { id: 'analogy', label: 'Real-world Analogy', icon: Lightbulb },
          { id: 'step_by_step', label: 'Step-by-Step', icon: ListOrdered },
          { id: 'simple_language', label: 'Simple Terms', icon: Smile },
        ].map((tab) => {
          const TabIcon = tab.icon;
          const isActive = currentStyle === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onStyleSelect(tab.id as any)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-brand-500 text-white shadow-md shadow-brand-500/25 scale-105'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700'
              }`}
            >
              <TabIcon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Primary Tutor Explanation */}
      <div className="bg-white dark:bg-slate-800/90 rounded-xl p-4 border border-brand-100 dark:border-brand-900/30 mb-4 shadow-sm">
        <p className="text-slate-800 dark:text-slate-200 text-sm leading-relaxed whitespace-pre-line font-medium">
          {tutor.explanation}
        </p>
      </div>

      {/* Interactive Visual Canvas / Diagram representation */}
      {tutor.visual_description && (
        <div className="bg-slate-900 text-white rounded-xl p-4 mb-4 border border-slate-800 shadow-inner">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-400 flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5" />
              Mental Model Visualizer
            </span>
          </div>

          <p className="text-xs text-slate-300 mb-3 italic">
            "{tutor.visual_description}"
          </p>

          {/* Dynamic Interactive SVG Graphics for Fractions */}
          <div className="bg-slate-950/80 rounded-lg p-3 flex flex-wrap items-center justify-center gap-4">
            {/* 3 Pizzas Cut into Quarters */}
            {[1, 2, 3].map((pizzaNum) => (
              <div key={pizzaNum} className="flex flex-col items-center gap-1">
                <svg className="w-16 h-16 drop-shadow-md" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="#f59e0b" stroke="#d97706" strokeWidth="4" />
                  {/* 4 Quadrant Slices */}
                  <line x1="50" y1="5" x2="50" y2="95" stroke="#78350f" strokeWidth="2.5" />
                  <line x1="5" y1="50" x2="95" y2="50" stroke="#78350f" strokeWidth="2.5" />
                  {/* Pepperoni dots */}
                  <circle cx="30" cy="30" r="4" fill="#dc2626" />
                  <circle cx="70" cy="30" r="4" fill="#dc2626" />
                  <circle cx="30" cy="70" r="4" fill="#dc2626" />
                  <circle cx="70" cy="70" r="4" fill="#dc2626" />
                </svg>
                <span className="text-[11px] font-bold text-slate-400">Pizza #{pizzaNum}</span>
              </div>
            ))}
          </div>
          <div className="mt-2 text-center text-[11px] font-mono text-emerald-400">
            3 pizzas × 4 slices each = 12 slices total ÷ 4 friends = 3 slices each (3/4 of a pizza)
          </div>
        </div>
      )}

      {/* Comprehension Check Question */}
      {tutor.check_question && (
        <div className="bg-brand-500/10 dark:bg-brand-950/40 rounded-xl p-4 border border-brand-500/20 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-2 h-2 rounded-full bg-brand-500"></span>
            <span className="text-xs font-bold uppercase tracking-wider text-brand-700 dark:text-brand-300">
              Quick Check Question
            </span>
          </div>
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-3">
            {tutor.check_question}
          </p>

          <form onSubmit={handleCheckAnswer} className="flex items-center gap-2">
            <input
              type="text"
              value={checkAnswerInput}
              onChange={(e) => setCheckAnswerInput(e.target.value)}
              placeholder="Type your brief answer here..."
              className="flex-1 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-900 dark:text-white"
            />
            <button
              type="submit"
              className="px-4 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs transition-colors"
            >
              Verify
            </button>
          </form>

          {checkStatus === 'correct' && (
            <div className="flex items-center gap-2 mt-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 animate-fade-in">
              <CheckCircle2 className="w-4 h-4" />
              <span>Spot on! You’ve got the core concept nailed.</span>
            </div>
          )}
          {checkStatus === 'try_again' && (
            <div className="flex items-center gap-2 mt-2 text-xs font-semibold text-amber-600 dark:text-amber-400 animate-fade-in">
              <XCircle className="w-4 h-4" />
              <span>Good try! Think of how 3 items divide into 4 equal shares (3/4).</span>
            </div>
          )}
        </div>
      )}

      {/* Follow-up Chat with Tutor */}
      <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800">
        <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-2">
          Ask a Follow-Up Question
        </span>

        {chatReplies.length > 0 && (
          <div className="space-y-2 mb-3 max-h-40 overflow-y-auto pr-1">
            {chatReplies.map((c, i) => (
              <div
                key={i}
                className={`text-xs p-2.5 rounded-xl ${
                  c.sender === 'user'
                    ? 'bg-brand-500 text-white ml-6 text-right'
                    : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 mr-6 border border-slate-200 dark:border-slate-700'
                }`}
              >
                {c.text}
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSendChat} className="flex items-center gap-2">
          <input
            type="text"
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            placeholder="Still unsure? Type: 'Why isn't it 4/3?' or anything else..."
            className="flex-1 px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-900 dark:text-white"
          />
          <button
            type="submit"
            disabled={isSendingChat || !chatMessage.trim()}
            className="p-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white disabled:opacity-50 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
