import React, { useState, useEffect, useCallback } from "react";
import {
  Concept,
  Question,
  EventResponse,
  ConfusionData,
  TutorData,
} from "../types/api";
import { useSignals } from "../hooks/useSignals";
import { useSpeech } from "../hooks/useSpeech";
import { ConfusionMeter } from "../components/ConfusionMeter";
import { A11yBar } from "../components/A11yBar";
import { TutorBubble } from "../components/TutorBubble";
import {
  HelpCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  XCircle,
  Compass,
  BarChart3,
  Sparkles,
  RefreshCw,
  RotateCcw,
} from "lucide-react";

// Celebration visual on correct answer
const triggerCelebration = () => {
  try {
    const el = document.createElement("div");
    el.className = "fixed inset-0 pointer-events-none z-50 flex items-center justify-center";
    el.innerHTML = '<div class="text-6xl animate-bounce">🎉 ✨ 🌟</div>';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1600);
  } catch (e) {
    // Ignore DOM error in headless mode
  }
};

interface StudentProps {
  onNavigateTeacher: () => void;
}

export const Student: React.FC<StudentProps> = ({ onNavigateTeacher }) => {
  const [sessionId, setSessionId] = useState<string>("");
  const [concept, setConcept] = useState<Concept | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [selectedOption, setSelectedOption] = useState<string>("");
  const [numericAnswer, setNumericAnswer] = useState<string>("");
  const [lastSubmittedAnswer, setLastSubmittedAnswer] = useState<string>("");

  // Real-time confusion and mastery state
  const [confusion, setConfusion] = useState<ConfusionData>({
    score: 0.05,
    state: "calm",
    reasons: [],
  });
  const [mastery, setMastery] = useState<Record<string, number>>({});
  const [tutorData, setTutorData] = useState<TutorData | null>(null);
  const [actionWhy, setActionWhy] = useState<any>(null);
  const [submissionStatus, setSubmissionStatus] = useState<
    "unsubmitted" | "correct" | "incorrect"
  >("unsubmitted");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingNext, setIsLoadingNext] = useState(false);
  const [isWsConnected, setIsWsConnected] = useState(false);
  const [currentStyle, setCurrentStyle] = useState<
    "visual" | "analogy" | "step_by_step" | "simple_language"
  >("visual");

  // Text to Speech hook
  const {
    speak,
    cancel: cancelSpeech,
    isSpeaking,
    rate: speechRate,
    setRate: setSpeechRate,
  } = useSpeech(1.0);

  // Background tick callback
  const handleTickResponse = useCallback((res: EventResponse) => {
    if (res && res.confusion) {
      setConfusion(res.confusion);
      if (res.mastery) setMastery(res.mastery);
      if (res.tutor) setTutorData(res.tutor);
      if (res.action?.style && res.action.style !== "none") {
        const norm = res.action.style === "worked" ? "step_by_step" : res.action.style;
        setCurrentStyle(norm as any);
      }
      if (res.action?.why) setActionWhy(res.action.why);
    }
  }, []);

  // Telemetry signals hook
  const {
    getFeatures,
    recordEdit,
    recordOptionSwitch,
    recordHint,
    recordLost,
    recordClick,
    resetForNewQuestion,
  } = useSignals(sessionId, question?.id || "", handleTickResponse);

  // Initialize session on mount
  const initSession = useCallback(async () => {
    try {
      const res = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile: "live" }),
      });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        setConcept(data.concept);
        setQuestion(data.question);
        setSelectedOption("");
        setNumericAnswer("");
        setLastSubmittedAnswer("");
        setSubmissionStatus("unsubmitted");
        setTutorData(null);
        setActionWhy(null);
        resetForNewQuestion();
      }
    } catch (err) {
      console.error("Failed to initialize session:", err);
    }
  }, [resetForNewQuestion]);

  useEffect(() => {
    initSession();
  }, [initSession]);

  // WebSocket for 2-second real-time confusion updates
  useEffect(() => {
    if (!sessionId) return;
    const isHttps = typeof window !== "undefined" && window.location.protocol === "https:";
    const host = typeof window !== "undefined" ? window.location.host : "localhost:8000";
    const wsUrl = `${isHttps ? "wss:" : "ws:"}//${host}/ws/${sessionId}`;

    let socket: WebSocket;
    try {
      socket = new WebSocket(wsUrl);
      socket.onopen = () => setIsWsConnected(true);
      socket.onclose = () => setIsWsConnected(false);
      socket.onerror = () => setIsWsConnected(false);
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload && typeof payload.score === "number") {
            setConfusion((prev) => ({
              ...prev,
              score: payload.score,
              state: payload.state || prev.state,
            }));
          }
        } catch (e) {
          // ignore
        }
      };
    } catch (e) {
      setIsWsConnected(false);
    }

    return () => {
      if (socket) socket.close();
    };
  }, [sessionId]);

  // Send Event helper
  const sendEvent = async (
    type: "tick" | "submit" | "hint" | "lost",
    answer?: string
  ) => {
    if (!sessionId || !question) return null;

    try {
      const features = getFeatures();
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const res = await fetch("/api/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: question.id,
          type,
          features,
          answer,
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data: EventResponse = await res.json();
        setConfusion(data.confusion);
        if (data.mastery) setMastery(data.mastery);
        if (data.tutor) {
          setTutorData(data.tutor);
          if (data.action?.style && data.action.style !== "none") {
            const norm = data.action.style === "worked" ? "step_by_step" : data.action.style;
            setCurrentStyle(norm as any);
          }
        }
        if (data.action?.why) setActionWhy(data.action.why);
        return data;
      }
    } catch (err) {
      console.error("Error submitting event:", err);
    }
    return null;
  };

  // Submit Answer with robust loading state and answer matching
  const handleSubmitAnswer = async () => {
    const answer =
      question?.type === "numeric" ? numericAnswer : selectedOption;
    if (!answer || isSubmitting) return;

    setIsSubmitting(true);
    setLastSubmittedAnswer(answer);
    try {
      const data = await sendEvent("submit", answer);
      const correct = question?.correct_answer?.trim().toLowerCase() || "";
      const studentAns = answer.trim().toLowerCase();
      
      // Match exactly or contained in either direction
      const isCorrect =
        correct === studentAns ||
        (correct.length > 0 && studentAns.includes(correct)) ||
        (studentAns.length > 0 && correct.includes(studentAns));

      if (isCorrect) {
        setSubmissionStatus("correct");
        triggerCelebration();
      } else {
        setSubmissionStatus("incorrect");
      }
    } catch (err) {
      console.error("Error during submission:", err);
      // Fallback local check
      const correct = question?.correct_answer?.trim().toLowerCase() || "";
      const studentAns = answer.trim().toLowerCase();
      const isCorrect = correct === studentAns || (correct.length > 0 && studentAns.includes(correct));
      setSubmissionStatus(isCorrect ? "correct" : "incorrect");
      if (isCorrect) triggerCelebration();
    } finally {
      setIsSubmitting(false);
    }
  };

  // Option selection handler that clears old error states when a different option is chosen
  const handleSelectOption = (opt: string) => {
    if (opt === selectedOption) return;
    setSelectedOption(opt);
    if (opt !== lastSubmittedAnswer) {
      setSubmissionStatus("unsubmitted");
    }
    // If student already submitted once and got it wrong, changing choice to try again is a RETRY!
    // If student hasn't submitted yet, changing choice is an answer EDIT / REVISION!
    if (lastSubmittedAnswer) {
      recordOptionSwitch();
    } else {
      recordEdit();
    }
  };

  // Hint tapped
  const handleHintClick = async () => {
    recordHint();
    await sendEvent("hint");
  };

  // "I'm Lost" button tapped
  const handleLostClick = async () => {
    recordLost();
    await sendEvent("lost");
  };

  // Next Question chosen by policy
  const handleNextQuestion = async () => {
    if (!sessionId || isLoadingNext) return;
    setIsLoadingNext(true);
    try {
      const res = await fetch(`/api/question/next?session_id=${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setQuestion(data.question);
        setSelectedOption("");
        setNumericAnswer("");
        setLastSubmittedAnswer("");
        setSubmissionStatus("unsubmitted");
        setTutorData(null);
        setActionWhy(null);
        resetForNewQuestion();
      }
    } catch (err) {
      console.error("Failed to get next question:", err);
    } finally {
      setIsLoadingNext(false);
    }
  };

  // Request alternate explanation style
  const handleStyleChange = async (
    style: "visual" | "analogy" | "step_by_step" | "simple_language"
  ) => {
    setCurrentStyle(style);
    try {
      const res = await fetch("/api/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          style,
          level: 1,
          question_id: question?.id,
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
      console.error("Failed to change explanation style:", err);
    }
  };

  const currentMastery = concept ? mastery[concept.id] ?? 0.2 : 0.2;
  const currentAnswer = question?.type === "numeric" ? numericAnswer : selectedOption;

  return (
    <div
      className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans"
      onClick={recordClick}
    >
      {/* Accessibility Bar with Lexend & Read Aloud toggles */}
      <A11yBar
        speechRate={speechRate}
        onSpeechRateChange={setSpeechRate}
        isSpeaking={isSpeaking}
        onStopSpeech={cancelSpeech}
      />

      {/* Main Header */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-6 py-3.5 sticky top-0 z-30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl text-white flex items-center justify-center font-black shadow-md"
            style={{ backgroundColor: "#6A35D8" }}
          >
            CP
          </div>
          <div>
            <h1 className="font-extrabold text-slate-900 dark:text-white text-lg tracking-tight flex items-center gap-2">
              ClearPath
              <span
                className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: "rgba(106, 53, 216, 0.12)",
                  color: "#6A35D8",
                }}
              >
                Adaptive Tutor
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Confusion-Aware Adaptive Learning
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onNavigateTeacher}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs border border-slate-200 dark:border-slate-700 transition-colors"
          >
            <BarChart3 className="w-4 h-4 text-[#6A35D8]" />
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

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Confusion Meter & Question Card (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* 5-segment vertical bar ConfusionMeter */}
          <ConfusionMeter
            sessionId={sessionId}
            data={confusion}
            isWsConnected={isWsConnected}
          />

          {/* Target Concept and BKT Mastery Card */}
          {concept && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span
                  className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5"
                  style={{ color: "#6A35D8" }}
                >
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
                  className="h-2 rounded-full transition-all duration-700 ease-out"
                  style={{
                    backgroundColor: "#6A35D8",
                    width: `${Math.round(currentMastery * 100)}%`,
                  }}
                />
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

              {/* Multiple Choice Options - Clean accessible cards */}
              {question.type === "multiple_choice" && question.options && (
                <div className="space-y-3 mb-6" role="radiogroup">
                  {question.options.map((opt, i) => {
                    const isSelected = selectedOption === opt;
                    const isWrongAttempt =
                      submissionStatus === "incorrect" && lastSubmittedAnswer === opt;
                    const isCorrectAttempt =
                      submissionStatus === "correct" && isSelected;

                    let borderClass =
                      "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300";
                    if (isCorrectAttempt) {
                      borderClass =
                        "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-100 font-semibold shadow-sm";
                    } else if (isWrongAttempt) {
                      borderClass =
                        "border-rose-400 bg-rose-50 dark:bg-rose-950/40 text-rose-900 dark:text-rose-100 font-semibold shadow-sm";
                    } else if (isSelected) {
                      borderClass =
                        "border-[#6A35D8] bg-[#f5f3ff] dark:bg-purple-950/40 text-slate-900 dark:text-white font-semibold shadow-sm";
                    }

                    return (
                      <div
                        key={i}
                        role="radio"
                        aria-checked={isSelected}
                        tabIndex={0}
                        onClick={() => handleSelectOption(opt)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            handleSelectOption(opt);
                          }
                        }}
                        className={`flex items-center gap-3 p-3.5 rounded-xl border-2 cursor-pointer transition-all ${borderClass}`}
                      >
                        {isCorrectAttempt ? (
                          <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        ) : isWrongAttempt ? (
                          <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                        ) : (
                          <div
                            className={`w-4 h-4 rounded-full border-2 flex items-center justify-center transition-colors flex-shrink-0 ${
                              isSelected ? "border-[#6A35D8]" : "border-slate-400"
                            }`}
                          >
                            {isSelected && (
                              <div className="w-2 h-2 rounded-full bg-[#6A35D8]" />
                            )}
                          </div>
                        )}
                        <span className="text-sm select-none">{opt}</span>
                        {isWrongAttempt && (
                          <span className="ml-auto text-[10px] font-bold text-rose-600 uppercase tracking-wide px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-900/40">
                            Incorrect Attempt
                          </span>
                        )}
                        {isCorrectAttempt && (
                          <span className="ml-auto text-[10px] font-bold text-emerald-600 uppercase tracking-wide px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/40">
                            Correct!
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Numeric Input */}
              {question.type === "numeric" && (
                <div className="mb-6">
                  <input
                    type="text"
                    value={numericAnswer}
                    onChange={(e) => {
                      setNumericAnswer(e.target.value);
                      setSubmissionStatus("unsubmitted");
                      recordEdit();
                    }}
                    placeholder="Enter numerical answer..."
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-mono text-base focus:outline-none focus:border-[#6A35D8]"
                  />
                </div>
              )}

              {/* Feedback messages */}
              {submissionStatus === "correct" && (
                <div className="flex items-center gap-2.5 p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 mb-5 animate-fade-in">
                  <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-500" />
                  <span className="text-sm font-semibold">
                    Excellent work! That is correct.
                  </span>
                </div>
              )}
              {submissionStatus === "incorrect" && (
                <div className="flex items-center gap-2.5 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 mb-5 animate-fade-in">
                  <XCircle className="w-5 h-5 flex-shrink-0 text-rose-500" />
                  <span className="text-sm font-semibold">
                    Not quite right. Review the tutor's guidance on the right, pick another answer, or skip to the next question.
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
                  {/* If incorrect, give option to skip to next question so student is not permanently blocked */}
                  {submissionStatus === "incorrect" && (
                    <button
                      onClick={handleNextQuestion}
                      disabled={isLoadingNext}
                      className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 font-semibold text-xs border border-slate-200 dark:border-slate-700 transition-colors shadow-sm"
                    >
                      {isLoadingNext ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <RotateCcw className="w-3.5 h-3.5" />
                      )}
                      <span>Skip Question</span>
                    </button>
                  )}

                  {submissionStatus === "correct" ? (
                    <button
                      onClick={handleNextQuestion}
                      disabled={isLoadingNext}
                      className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md transition-all scale-105"
                    >
                      {isLoadingNext ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Loading Next...</span>
                        </>
                      ) : (
                        <>
                          <span>Next Question</span>
                          <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  ) : (
                    <button
                      onClick={handleSubmitAnswer}
                      disabled={
                        !currentAnswer ||
                        isSubmitting ||
                        (submissionStatus === "incorrect" &&
                          selectedOption === lastSubmittedAnswer)
                      }
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-white font-bold text-sm shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-95"
                      style={{ backgroundColor: "#6A35D8" }}
                    >
                      {isSubmitting ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Checking...</span>
                        </>
                      ) : submissionStatus === "incorrect" &&
                        selectedOption === lastSubmittedAnswer ? (
                        <span>Choose Another Option</span>
                      ) : (
                        <span>Submit Answer</span>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-12 text-center border border-slate-200 dark:border-slate-800">
              <RefreshCw
                className="w-8 h-8 animate-spin mx-auto mb-3"
                style={{ color: "#6A35D8" }}
              />
              <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                Loading session question...
              </p>
            </div>
          )}
        </div>

        {/* Right Column: TutorBubble (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {tutorData ? (
            <TutorBubble
              tutor={tutorData}
              sessionId={sessionId}
              conceptId={concept?.id}
              questionId={question?.id}
              currentStyle={currentStyle}
              onStyleSelect={handleStyleChange}
              onSpeak={speak}
              isSpeaking={isSpeaking}
              onCancelSpeech={cancelSpeech}
            />
          ) : (
            <div className="bg-white/80 dark:bg-slate-900/80 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 p-8 text-center backdrop-blur-sm">
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3"
                style={{
                  backgroundColor: "rgba(106, 53, 216, 0.1)",
                  color: "#6A35D8",
                }}
              >
                <Sparkles className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-slate-800 dark:text-slate-200 text-sm mb-1">
                Tutor in Passive Standby
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
                ClearPath observes your timing and interaction cadence passively. If you hesitate, pause, or click "I'm Lost", multimodal pedagogical scaffolding activates automatically.
              </p>
              <button
                onClick={() => handleStyleChange("visual")}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 text-xs font-semibold transition-colors"
              >
                <span>Trigger Tutor Explanation</span>
              </button>
            </div>
          )}

          {/* Action Why Diagnostic Card */}
          {actionWhy && (
            <div className="bg-slate-100 dark:bg-slate-900/60 rounded-xl p-3.5 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400">
              <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                Pedagogical Decision Engine:
              </span>
              <p className="mb-2 italic text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                "{typeof actionWhy === "object" ? actionWhy.decision : String(actionWhy)}"
              </p>
              {actionWhy.signals && actionWhy.signals.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {actionWhy.signals.map((sig: string, idx: number) => (
                    <span
                      key={idx}
                      className="bg-white dark:bg-slate-800 px-2 py-0.5 rounded text-[10px] font-mono border"
                    >
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

export default Student;
