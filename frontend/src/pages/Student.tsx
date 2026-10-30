import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Concept, 
  Question, 
  EventResponse, 
  ConfusionData, 
  TutorData 
} from '../types/api';

// Lightweight visual celebration effect
const triggerCelebration = () => {
  try {
    const el = document.createElement('div');
    el.className = 'fixed inset-0 pointer-events-none z-50 flex items-center justify-center';
    el.innerHTML = '<div class="text-6xl animate-bounce">🎉 ✨ 🌟</div>';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1500);
  } catch (e) {}
};
import { useSignals } from '../hooks/useSignals';
import { useSpeech } from '../hooks/useSpeech';
import { ConfusionMeter } from '../components/ConfusionMeter';
import { A11yBar } from '../components/A11yBar';
import { TutorBubble } from '../components/TutorBubble';
import { 
  HelpCircle, 
  AlertTriangle, 
  ArrowRight, 
  CheckCircle, 
  XCircle, 
  Compass, 
  GraduationCap, 
  BarChart3, 
  RotateCcw,
  Sparkles,
  RefreshCw
} from 'lucide-react';

interface StudentProps {
  onNavigateTeacher: () => void;
}

export const Student: React.FC<StudentProps> = ({ onNavigateTeacher }) => {
  const [sessionId, setSessionId] = useState<string>('');
  const [concept, setConcept] = useState<Concept | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [numericAnswer, setNumericAnswer] = useState<string>('');
  
  // Real-time confusion and mastery state
  const [confusion, setConfusion] = useState<ConfusionData>({
    score: 0.05,
    state: 'focused',
    reasons: [],
  });
  const [mastery, setMastery] = useState<Record<string, number>>({});
  const [tutorData, setTutorData] = useState<TutorData | null>(null);
  const [actionWhy, setActionWhy] = useState<any>(null);
  const [submissionStatus, setSubmissionStatus] = useState<'unsubmitted' | 'correct' | 'incorrect'>('unsubmitted');
  const [isLoadingNext, setIsLoadingNext] = useState(false);
  const [isWsConnected, setIsWsConnected] = useState(false);
  const [currentStyle, setCurrentStyle] = useState<'visual' | 'analogy' | 'step_by_step' | 'simple_language'>('visual');

  // Text to Speech hook
  const { speak, cancel: cancelSpeech, isSpeaking, rate: speechRate, setRate: setSpeechRate } = useSpeech(1.0);

  // Background tick handler
  const handleTickResponse = useCallback((res: EventResponse) => {
    if (res && res.confusion) {
      setConfusion(res.confusion);
      if (res.mastery) setMastery(res.mastery);
      if (res.tutor) setTutorData(res.tutor);
      if (res.action?.why) setActionWhy(res.action.why);
    }
  }, []);

  // Telemetry signals hook
  const {
    dwellTimeMs,
    pauseDurationMs,
    getFeatures,
    recordEdit,
    recordOptionSwitch,
    recordHint,
    recordLost,
    recordClick,
    resetForNewQuestion,
  } = useSignals(sessionId, question?.id || '', handleTickResponse);

  // Initialize session on mount
  const initSession = useCallback(async () => {
    try {
      const res = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: 'live' }),
      });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        setConcept(data.concept);
        setQuestion(data.question);
        setSelectedOption('');
        setNumericAnswer('');
        setSubmissionStatus('unsubmitted');
        setTutorData(null);
        resetForNewQuestion();
      }
    } catch (err) {
      console.error('Failed to initialize session:', err);
    }
  }, [resetForNewQuestion]);

  useEffect(() => {
    initSession();
  }, [initSession]);

  // WebSocket for 2-second real-time confusion updates
  useEffect(() => {
    if (!sessionId) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    
    let socket: WebSocket;
    try {
      socket = new WebSocket(wsUrl);
      socket.onopen = () => setIsWsConnected(true);
      socket.onclose = () => setIsWsConnected(false);
      socket.onerror = () => setIsWsConnected(false);
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload && typeof payload.score === 'number') {
            setConfusion((prev) => ({
              ...prev,
              score: payload.score,
              state: payload.state,
            }));
          }
        } catch (e) {}
      };
    } catch (e) {
      setIsWsConnected(false);
    }

    return () => {
      if (socket) socket.close();
    };
  }, [sessionId]);

  // Send Event helper
  const sendEvent = async (type: 'tick' | 'submit' | 'hint' | 'lost', answer?: string) => {
    if (!sessionId || !question) return;

    try {
      const features = getFeatures();
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: question.id,
          type,
          features,
          answer,
        }),
      });

      if (res.ok) {
        const data: EventResponse = await res.json();
        setConfusion(data.confusion);
        if (data.mastery) setMastery(data.mastery);
        if (data.tutor) {
          setTutorData(data.tutor);
          if (data.action?.style && data.action.style !== 'none') {
            setCurrentStyle(data.action.style as any);
          }
        }
        if (data.action?.why) setActionWhy(data.action.why);
        return data;
      }
    } catch (err) {
      console.error('Error submitting event:', err);
    }
    return null;
  };

  // Submit Answer
  const handleSubmitAnswer = async () => {
    const answer = question?.type === 'numeric' ? numericAnswer : selectedOption;
    if (!answer) return;

    const data = await sendEvent('submit', answer);
    const isCorrect = answer.trim().toLowerCase() === question?.correct_answer.trim().toLowerCase();

    if (isCorrect) {
      setSubmissionStatus('correct');
      triggerCelebration();
    } else {
      setSubmissionStatus('incorrect');
    }
  };

  // Hint tapped
  const handleHintClick = async () => {
    recordHint();
    const data = await sendEvent('hint');
  };

  // "I'm Lost" button tapped
  const handleLostClick = async () => {
    recordLost();
    const data = await sendEvent('lost');
  };

  // Next Question chosen by policy
  const handleNextQuestion = async () => {
    if (!sessionId) return;
    setIsLoadingNext(true);
    try {
      const res = await fetch(`/api/question/next?session_id=${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setQuestion(data.question);
        setSelectedOption('');
        setNumericAnswer('');
        setSubmissionStatus('unsubmitted');
        setTutorData(null);
        setActionWhy(null);
        resetForNewQuestion();
      }
    } catch (err) {
      console.error('Failed to get next question:', err);
    } finally {
      setIsLoadingNext(false);
    }
  };

  // Request alternate explanation style
  const handleStyleChange = async (style: 'visual' | 'analogy' | 'step_by_step' | 'simple_language') => {
    setCurrentStyle(style);
    try {
      const res = await fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          style,
          level: 1,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setTutorData({
          explanation: data.explanation,
          check_question: data.check_question,
          visual_description: data.visual_description,
          source: data.source,
        });
      }
    } catch (err) {
      console.error('Failed to change explanation style:', err);
    }
  };

  const currentMastery = concept ? (mastery[concept.id] ?? 0.20) : 0.20;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col" onClick={recordClick}>
      {/* Top Accessibility Bar */}
      <A11yBar speechRate={speechRate} onSpeechRateChange={setSpeechRate} />

      {/* Main Header */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-6 py-3.5 sticky top-0 z-30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-brand-600 text-white flex items-center justify-center font-black shadow-md shadow-brand-500/25">
            CP
          </div>
          <div>
            <h1 className="font-extrabold text-slate-900 dark:text-white text-lg tracking-tight flex items-center gap-2">
              ClearPath
              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-brand-100 dark:bg-brand-950 text-brand-700 dark:text-brand-300">
                Hackathon Demo
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Confusion-Aware Adaptive Tutor
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onNavigateTeacher}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs border border-slate-200 dark:border-slate-700 transition-colors"
          >
            <BarChart3 className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <span>Teacher Heatmap</span>
          </button>
          <button
            onClick={initSession}
            title="Reset Session"
            className="p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Learning Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Cognitive State & Active Question (8 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Real-time Confusion Meter */}
          <ConfusionMeter data={confusion} isWsConnected={isWsConnected} />

          {/* Active Concept and BKT Mastery Card */}
          {concept && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5" />
                  Target Concept
                </span>
                <span className="text-xs font-bold text-slate-600 dark:text-slate-300">
                  Mastery: {Math.round(currentMastery * 100)}%
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white mb-1">
                {concept.name}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                {concept.description}
              </p>
              {/* Animated Progress Bar */}
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-brand-500 h-2 rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${Math.round(currentMastery * 100)}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Active Question Card */}
          {question ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-md relative overflow-hidden">
              <div className="flex items-center justify-between gap-2 mb-4">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  Difficulty: {question.difficulty}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  ID: {question.id}
                </span>
              </div>

              {/* Question Text */}
              <p className="text-lg font-bold text-slate-900 dark:text-white leading-relaxed mb-6">
                {question.prompt}
              </p>

              {/* Multiple Choice Options */}
              {question.type === 'multiple_choice' && question.options && (
                <div className="space-y-3 mb-6">
                  {question.options.map((opt, i) => {
                    const isSelected = selectedOption === opt;
                    return (
                      <label
                        key={i}
                        className={`flex items-center gap-3 p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                          isSelected
                            ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/40 text-brand-900 dark:text-brand-100 font-semibold shadow-sm'
                            : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300'
                        }`}
                        onClick={() => {
                          if (selectedOption !== opt) {
                            setSelectedOption(opt);
                            recordOptionSwitch();
                          }
                        }}
                      >
                        <input
                          type="radio"
                          name="question-option"
                          checked={isSelected}
                          onChange={() => {}}
                          className="w-4 h-4 text-brand-600 focus:ring-brand-500"
                        />
                        <span className="text-sm">{opt}</span>
                      </label>
                    );
                  })}
                </div>
              )}

              {/* Numeric Input if question type is numeric */}
              {question.type === 'numeric' && (
                <div className="mb-6">
                  <input
                    type="text"
                    value={numericAnswer}
                    onChange={(e) => {
                      setNumericAnswer(e.target.value);
                      recordEdit();
                    }}
                    placeholder="Enter numerical answer..."
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-mono text-base focus:outline-none focus:border-brand-500"
                  />
                </div>
              )}

              {/* Answer submission feedback */}
              {submissionStatus === 'correct' && (
                <div className="flex items-center gap-2.5 p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 mb-5 animate-fade-in">
                  <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-500" />
                  <span className="text-sm font-semibold">
                    Excellent work! That is correct.
                  </span>
                </div>
              )}
              {submissionStatus === 'incorrect' && (
                <div className="flex items-center gap-2.5 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 mb-5 animate-fade-in">
                  <XCircle className="w-5 h-5 flex-shrink-0 text-rose-500" />
                  <span className="text-sm font-semibold">
                    Not quite. Take a moment to inspect the tutor guidance on the right!
                  </span>
                </div>
              )}

              {/* Action Buttons Row */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleHintClick}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 hover:bg-amber-100 font-semibold text-xs border border-amber-200 dark:border-amber-800 transition-colors"
                  >
                    <HelpCircle className="w-4 h-4" />
                    <span>Get a Hint</span>
                  </button>

                  <button
                    onClick={handleLostClick}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 hover:bg-rose-100 font-semibold text-xs border border-rose-200 dark:border-rose-800 transition-colors"
                  >
                    <AlertTriangle className="w-4 h-4" />
                    <span>I'm Lost</span>
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  {submissionStatus === 'correct' ? (
                    <button
                      onClick={handleNextQuestion}
                      disabled={isLoadingNext}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md shadow-emerald-600/30 transition-all scale-105"
                    >
                      <span>Next Question</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={handleSubmitAnswer}
                      disabled={!selectedOption && !numericAnswer}
                      className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-bold text-sm shadow-md shadow-brand-600/30 transition-all"
                    >
                      Submit Answer
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-12 text-center border border-slate-200 dark:border-slate-800">
              <RefreshCw className="w-8 h-8 text-brand-500 animate-spin mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                Loading question...
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Adaptive Tutor Intervention Drawer (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {tutorData ? (
            <TutorBubble
              tutor={tutorData}
              sessionId={sessionId}
              conceptId={concept?.id}
              currentStyle={currentStyle}
              onStyleSelect={handleStyleChange}
              onSpeak={speak}
              isSpeaking={isSpeaking}
              onCancelSpeech={cancelSpeech}
            />
          ) : (
            <div className="bg-white/80 dark:bg-slate-900/80 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8 text-center backdrop-blur-sm">
              <div className="w-12 h-12 rounded-2xl bg-brand-50 dark:bg-brand-950/60 text-brand-500 flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-slate-800 dark:text-slate-200 text-sm mb-1">
                Tutor in Passive Standby
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
                ClearPath observes your timing and interaction cadence passively. If you hesitate, pause over 20s, or tap "I'm Lost", multimodal scaffolding activates automatically.
              </p>
              <button
                onClick={() => handleStyleChange('visual')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 text-xs font-semibold transition-colors"
              >
                <span>Trigger Tutor Demo</span>
              </button>
            </div>
          )}

          {/* Action Why Diagnostic Card */}
          {actionWhy && (
            <div className="bg-slate-100 dark:bg-slate-900/60 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400">
              <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                Pedagogical Policy Decision:
              </span>
              <p className="mb-2 italic text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                "{actionWhy.decision}"
              </p>
              {actionWhy.signals && actionWhy.signals.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {actionWhy.signals.map((sig: string, idx: number) => (
                    <span key={idx} className="bg-white dark:bg-slate-800 px-2 py-0.5 rounded text-[10px] font-mono border">
                      {sig}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
