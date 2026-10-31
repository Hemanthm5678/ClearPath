import React, { useState, useRef, useEffect } from "react";
import { TutorData } from "../types/api";
import { VisualDiagram } from "./VisualDiagram";
import {
  Send,
  Volume2,
  VolumeX,
  Layers,
  BookOpen,
  ListOrdered,
  Smile,
  HelpCircle,
  Cpu,
  Bot,
  Lightbulb,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface TutorBubbleProps {
  tutor?: TutorData | null;
  explanation?: string;
  source?: string;
  sessionId: string;
  conceptId?: string;
  questionId?: string;
  currentStyle?: string;
  onStyleSelect?: (style: "visual" | "analogy" | "step_by_step" | "simple_language") => void;
  onSpeak?: (text: string) => void;
  isSpeaking?: boolean;
  onCancelSpeech?: () => void;
  onReply?: (reply: string) => void;
}

interface ChatMessage {
  id: string;
  role: "tutor" | "student";
  text: string;
  source?: string;
}

export const TutorBubble: React.FC<TutorBubbleProps> = ({
  tutor,
  explanation: propExplanation,
  source: propSource,
  sessionId,
  conceptId,
  questionId,
  currentStyle = "visual",
  onStyleSelect,
  onSpeak,
  isSpeaking = false,
  onCancelSpeech,
  onReply,
}) => {
  // Normalize style ('worked' -> 'step_by_step')
  const activeStyle = currentStyle === "worked" ? "step_by_step" : (currentStyle || "visual");

  const activeExplanation = tutor?.explanation || propExplanation || "";
  const activeSource = tutor?.source || propSource || "offline_bank";
  const checkQuestion = tutor?.check_question;
  const visualDescription = tutor?.visual_description;

  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showCheckAnswer, setShowCheckAnswer] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Initialize or reset chat when active explanation or question changes
  useEffect(() => {
    setShowCheckAnswer(false);
    if (activeExplanation) {
      setChatHistory([
        {
          id: `initial_tutor_${questionId || "curr"}_${activeStyle}_${Date.now()}`,
          role: "tutor",
          text: activeExplanation,
          source: activeSource,
        },
      ]);
    } else {
      setChatHistory([]);
    }
  }, [questionId, activeStyle, activeExplanation, activeSource]);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, isLoading]);

  // Handle follow-up chat submit
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const msg = inputMessage.trim();
    if (!msg || isLoading || !sessionId) return;

    const userMsgId = `user_${Date.now()}`;
    setChatHistory((prev) => [
      ...prev,
      { id: userMsgId, role: "student", text: msg },
    ]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: msg,
          question_id: questionId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const replyText =
          data.reply || "Good thinking! Try to consider how many parts fit into the whole.";
        const replySource = data.source || "offline_bank";

        setChatHistory((prev) => [
          ...prev,
          {
            id: `tutor_${Date.now()}`,
            role: "tutor",
            text: replyText,
            source: replySource,
          },
        ]);

        if (onReply) onReply(replyText);
      } else {
        setChatHistory((prev) => [
          ...prev,
          {
            id: `tutor_err_${Date.now()}`,
            role: "tutor",
            text: "I had a moment of trouble retrieving that. Could you try rephrasing your question?",
            source: "offline_bank",
          },
        ]);
      }
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        {
          id: `tutor_err_${Date.now()}`,
          role: "tutor",
          text: "I'm currently running in offline fallback mode. Keep going, you're doing great!",
          source: "offline_bank",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReadAloud = (textToRead: string) => {
    if (isSpeaking && onCancelSpeech) {
      onCancelSpeech();
    } else if (onSpeak) {
      onSpeak(textToRead);
    }
  };

  const modalities = [
    {
      id: "visual",
      label: "Visual Diagram",
      icon: Layers,
      description: "Interactive visual diagrams & models",
    },
    {
      id: "analogy",
      label: "Analogy",
      icon: BookOpen,
      description: "Real-world stories & relatable comparisons",
    },
    {
      id: "step_by_step",
      label: "Step-by-Step",
      icon: ListOrdered,
      description: "Logical sequence & calculation procedures",
    },
    {
      id: "simple_language",
      label: "Simple Language",
      icon: Smile,
      description: "Plain English, easy words & rules of thumb",
    },
  ] as const;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-md overflow-hidden flex flex-col">
      {/* Header with Modality Selector */}
      <div className="bg-slate-50 dark:bg-slate-950/60 p-3.5 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#6A35D8] text-white flex items-center justify-center shadow-sm shadow-[#6A35D8]/30">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                Adaptive AI Tutor
                <span className="text-[10px] font-semibold text-[#6A35D8] bg-[#6A35D8]/10 px-2 py-0.5 rounded-full">
                  Multimodal Scaffolding
                </span>
              </h3>
            </div>
          </div>

          {/* Read Aloud button for active explanation */}
          {activeExplanation && (
            <button
              type="button"
              onClick={() => handleReadAloud(activeExplanation)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold transition-all ${
                isSpeaking
                  ? "bg-[#F25C1E] text-white animate-pulse shadow-sm shadow-[#F25C1E]/30"
                  : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-100 border border-slate-200 dark:border-slate-700"
              }`}
              title={isSpeaking ? "Stop reading aloud" : "Read explanation aloud"}
            >
              {isSpeaking ? (
                <>
                  <VolumeX className="w-3.5 h-3.5" />
                  <span>Stop</span>
                </>
              ) : (
                <>
                  <Volume2 className="w-3.5 h-3.5 text-[#6A35D8]" />
                  <span>Read Aloud</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Modality switcher pills with clear active highlighting */}
        {onStyleSelect && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 pt-1">
            {modalities.map((m) => {
              const Icon = m.icon;
              const isActive = activeStyle === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => onStyleSelect(m.id)}
                  title={m.description}
                  className={`flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-xl text-[11px] font-bold transition-all ${
                    isActive
                      ? "bg-[#6A35D8] text-white shadow-md shadow-[#6A35D8]/30 scale-[1.02]"
                      : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 hover:text-slate-900"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate">{m.label}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Main Conversation & Messages Area */}
      <div className="p-4 space-y-3.5 max-h-[460px] overflow-y-auto">
        {chatHistory.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === "tutor" ? "items-start" : "items-end"
            }`}
          >
            <div
              className={`max-w-[95%] w-full rounded-2xl px-4 py-3.5 text-sm leading-relaxed ${
                msg.role === "tutor"
                  ? "bg-[#f5f3ff] dark:bg-purple-950/40 text-slate-800 dark:text-slate-100 rounded-tl-sm border border-purple-100 dark:border-purple-900/50 shadow-sm"
                  : "bg-[#fff7ed] dark:bg-orange-950/40 text-slate-900 dark:text-slate-100 rounded-tr-sm border border-orange-200 dark:border-orange-900/50"
              }`}
            >
              {/* Specialized Features Header per Modality */}
              {msg.id.startsWith("initial_tutor") && (
                <div className="mb-2.5 pb-2 border-b border-purple-200/60 dark:border-purple-800/60 flex items-center justify-between text-xs">
                  <span className="font-extrabold text-[#6A35D8] dark:text-purple-300 flex items-center gap-1.5">
                    {activeStyle === "visual" && <Layers className="w-3.5 h-3.5" />}
                    {activeStyle === "analogy" && <BookOpen className="w-3.5 h-3.5" />}
                    {activeStyle === "step_by_step" && <ListOrdered className="w-3.5 h-3.5" />}
                    {activeStyle === "simple_language" && <Smile className="w-3.5 h-3.5" />}
                    <span className="capitalize">
                      {activeStyle === "step_by_step" ? "Step-by-Step Procedure" : `${activeStyle} Scaffold`}
                    </span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    Targeted Guidance
                  </span>
                </div>
              )}

              {/* 1. VISUAL DIAGRAM MODALITY: Render tailored SVG Model */}
              {msg.id.startsWith("initial_tutor") && activeStyle === "visual" && (
                <div className="my-2.5 animate-fade-in">
                  <VisualDiagram questionId={questionId} conceptId={conceptId} />
                </div>
              )}

              {/* 2. ANALOGY MODALITY: Metaphor Storytelling Card */}
              {msg.id.startsWith("initial_tutor") && activeStyle === "analogy" && (
                <div className="my-2.5 p-3 rounded-xl bg-orange-50/70 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-900/60 text-xs">
                  <div className="flex items-center gap-1.5 text-[#F25C1E] font-bold mb-1">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Real-World Intuition & Analogy</span>
                  </div>
                  <p className="text-slate-600 dark:text-slate-300 leading-normal">
                    Connecting abstract symbols and operations to concrete physical mental models.
                  </p>
                </div>
              )}

              {/* 3. STEP-BY-STEP MODALITY: Structured Problem-Solving Sequence */}
              {msg.id.startsWith("initial_tutor") && activeStyle === "step_by_step" && (
                <div className="my-2.5 p-3 rounded-xl bg-purple-100/50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-xs">
                  <div className="flex items-center gap-1.5 text-[#6A35D8] font-bold mb-2">
                    <ListOrdered className="w-3.5 h-3.5" />
                    <span>Structured Execution Trace</span>
                  </div>
                  <div className="grid grid-cols-3 gap-1.5 text-center text-[10px] font-bold">
                    <div className="bg-white dark:bg-slate-900 p-1.5 rounded-lg border border-purple-200">
                      1. Parse Input
                    </div>
                    <div className="bg-white dark:bg-slate-900 p-1.5 rounded-lg border border-purple-200">
                      2. Apply Logic
                    </div>
                    <div className="bg-white dark:bg-slate-900 p-1.5 rounded-lg border border-purple-200">
                      3. Verify Output
                    </div>
                  </div>
                </div>
              )}

              {/* 4. SIMPLE LANGUAGE MODALITY: Rule of Thumb Banner */}
              {msg.id.startsWith("initial_tutor") && activeStyle === "simple_language" && (
                <div className="my-2.5 p-3 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-xs">
                  <div className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-300 font-bold mb-1">
                    <Smile className="w-3.5 h-3.5" />
                    <span>Plain English / Rule of Thumb</span>
                  </div>
                  <p className="text-emerald-900 dark:text-emerald-200 font-medium">
                    "Break it down into simple terms: focus on the core rule and solve one step at a time."
                  </p>
                </div>
              )}

              {/* Core Text Body */}
              <p className="whitespace-pre-line text-slate-800 dark:text-slate-100 text-sm leading-relaxed">
                {msg.text}
              </p>

              {/* Visual description callout if tutor explanation has visual details */}
              {msg.id.startsWith("initial_tutor") && visualDescription && activeStyle !== "visual" && (
                <div className="mt-3 p-2.5 bg-white/80 dark:bg-slate-900/80 rounded-xl border border-purple-200 dark:border-purple-800 text-xs text-slate-600 dark:text-slate-300 flex items-start gap-2">
                  <Layers className="w-4 h-4 text-[#6A35D8] flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-slate-700 dark:text-slate-200 block text-[11px]">
                      Mental Model Diagram:
                    </span>
                    <span>{visualDescription}</span>
                  </div>
                </div>
              )}

              {/* Interactive Check Question Feature */}
              {msg.id.startsWith("initial_tutor") && checkQuestion && (
                <div className="mt-3 p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-900 dark:text-emerald-200">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 font-bold text-emerald-800 dark:text-emerald-300">
                      <HelpCircle className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                      <span>Comprehension Check:</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowCheckAnswer(!showCheckAnswer)}
                      className="text-[10px] font-bold text-emerald-700 hover:text-emerald-900 dark:text-emerald-400 flex items-center gap-0.5"
                    >
                      <span>{showCheckAnswer ? "Hide Reflection" : "Check Understanding"}</span>
                      {showCheckAnswer ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                  </div>
                  <p className="mt-1 font-medium">{checkQuestion}</p>

                  {showCheckAnswer && (
                    <div className="mt-2 pt-2 border-t border-emerald-200 dark:border-emerald-800/60 text-[11px] text-emerald-800 dark:text-emerald-300 animate-fade-in flex items-start gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                      <span>
                        Think through how the parts relate to the whole. You can type your answer in the box below to ask the tutor!
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Source Badge & Inline Listen */}
              {msg.source && (
                <div className="mt-2.5 pt-2 border-t border-purple-100/60 dark:border-purple-900/40 flex items-center justify-between text-[10px] text-slate-400">
                  <span className="inline-flex items-center gap-1 font-mono">
                    <Cpu className="w-3 h-3 text-[#6A35D8]" />
                    Source: {msg.source}
                  </span>
                  {msg.role === "tutor" && (
                    <button
                      type="button"
                      onClick={() => handleReadAloud(msg.text)}
                      className="hover:text-slate-700 dark:hover:text-slate-200 text-[10px] font-medium flex items-center gap-1 ml-2 text-slate-500"
                    >
                      <Volume2 className="w-3 h-3 text-[#6A35D8]" />
                      Listen
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading Thinking Indicator */}
        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-slate-500 italic p-2 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-[#6A35D8]"></span>
            <span>Tutor is formulating pedagogical response...</span>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input area for student follow-up questions (marked with data-chat-input to avoid polluting problem edits) */}
      <form
        onSubmit={handleSendMessage}
        className="p-3 bg-slate-50 dark:bg-slate-950/60 border-t border-slate-200 dark:border-slate-800 flex items-center gap-2"
      >
        <input
          type="text"
          data-chat-input="true"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask a follow-up question or ask for another example..."
          disabled={isLoading}
          className="flex-1 px-3.5 py-2 rounded-xl text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-[#6A35D8] text-slate-900 dark:text-white"
        />
        <button
          type="submit"
          disabled={isLoading || !inputMessage.trim()}
          className="px-3.5 py-2 rounded-xl text-white text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-95 shadow-sm shadow-[#6A35D8]/25 flex items-center gap-1.5"
          style={{ backgroundColor: "#6A35D8" }}
        >
          <Send className="w-3.5 h-3.5" />
          <span>Reply</span>
        </button>
      </form>
    </div>
  );
};

export default TutorBubble;
