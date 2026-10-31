import React, { useEffect, useRef, useState } from "react";
import { ConfusionData, ConfusionState, CognitiveState } from "../types/api";
import { Activity, Wifi, WifiOff, Clock, ShieldAlert, Sparkles, Brain } from "lucide-react";

interface ConfusionMeterProps {
  sessionId?: string;
  data?: ConfusionData;
  score?: number;
  state?: ConfusionState;
  cognitiveState?: CognitiveState;
  studentPaceFactor?: number;
  cooldownSeconds?: number;
  isWsConnected?: boolean;
}

interface SegmentDef {
  label: string;
  color: string;
  activeColor: string;
  threshold: number;
}

// 5 segments: Red at top (confused), Green at bottom (calm)
const SEGMENTS: SegmentDef[] = [
  { label: "Lost / Severe", color: "bg-red-500", activeColor: "#ef4444", threshold: 0.8 },
  { label: "Confused", color: "bg-[#F25C1E]", activeColor: "#F25C1E", threshold: 0.6 },
  { label: "Uncertain", color: "bg-amber-400", activeColor: "#eab308", threshold: 0.4 },
  { label: "Mild Hesitation", color: "bg-lime-500", activeColor: "#84cc16", threshold: 0.2 },
  { label: "Calm / Focused", color: "bg-emerald-500", activeColor: "#22c55e", threshold: 0.0 },
];

export const ConfusionMeter: React.FC<ConfusionMeterProps> = ({
  sessionId,
  data: propData,
  score: propScore,
  state: propState,
  cognitiveState: propCogState,
  studentPaceFactor: propPace,
  cooldownSeconds: propCooldown,
  isWsConnected: propIsWsConnected,
}) => {
  const [internalData, setInternalData] = useState<{
    score: number;
    state: string;
    cognitiveState: CognitiveState;
    studentPaceFactor: number;
    cooldownSeconds: number;
  }>({
    score: propScore ?? propData?.score ?? 0.05,
    state: propState ?? propData?.state ?? "calm",
    cognitiveState: propCogState ?? "FOCUSED",
    studentPaceFactor: propPace ?? 1.0,
    cooldownSeconds: propCooldown ?? 0,
  });
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync with prop updates if provided
  useEffect(() => {
    setInternalData((prev) => ({
      score: propScore ?? propData?.score ?? prev.score,
      state: propState ?? propData?.state ?? prev.state,
      cognitiveState: propCogState ?? prev.cognitiveState,
      studentPaceFactor: propPace ?? prev.studentPaceFactor,
      cooldownSeconds: propCooldown ?? prev.cooldownSeconds,
    }));
  }, [propData, propScore, propState, propCogState, propPace, propCooldown]);

  // Connect live WebSocket if sessionId is provided
  useEffect(() => {
    if (!sessionId) return;

    function connect() {
      const isHttps = typeof window !== "undefined" && window.location.protocol === "https:";
      const host = typeof window !== "undefined" ? window.location.host : "localhost:8000";
      const wsProtocol = isHttps ? "wss:" : "ws:";
      const wsUrl = `${wsProtocol}//${host}/ws/${sessionId}`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);
            if (payload) {
              setInternalData((prev) => ({
                score: typeof payload.score === "number" ? Math.max(0.0, Math.min(1.0, payload.score)) : prev.score,
                state: payload.state || prev.state,
                cognitiveState: (payload.cognitive_state as CognitiveState) || prev.cognitiveState,
                studentPaceFactor: payload.student_pace_factor ?? prev.studentPaceFactor,
                cooldownSeconds: payload.cooldown_seconds ?? prev.cooldownSeconds,
              }));
            }
          } catch (e) {
            // Ignore parse errors
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeoutRef.current = setTimeout(connect, 2000);
        };

        ws.onerror = () => {
          setWsConnected(false);
          ws.close();
        };
      } catch (err) {
        setWsConnected(false);
      }
    }

    connect();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [sessionId]);

  const currentScore = internalData.score;
  const currentCogState = internalData.cognitiveState;
  const paceFactor = internalData.studentPaceFactor;
  const cooldownSecs = internalData.cooldownSeconds;
  const percentage = Math.round(currentScore * 100);
  const isConnected = propIsWsConnected !== undefined ? propIsWsConnected : wsConnected;

  // Cognitive State badge styling and description
  const getCognitiveStateDisplay = () => {
    switch (currentCogState) {
      case "GAMING":
        return {
          label: "Gaming Detected",
          tag: "Hint Cooldown Active",
          color: "text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/60 border-purple-200 dark:border-purple-800",
          dotColor: "#9333ea",
          desc: "Rapid hint tapping detected. 10s cooldown enforced with self-check prompt.",
          icon: <ShieldAlert className="w-3.5 h-3.5 text-purple-600" />,
        };
      case "BORED":
        return {
          label: "Under-Engaged / Bored",
          tag: "Rapid Streak Challenge",
          color: "text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 border-amber-200 dark:border-amber-800",
          dotColor: "#d97706",
          desc: "Hasty answering in < 28% of expected time. Rapid streak booster triggered.",
          icon: <Sparkles className="w-3.5 h-3.5 text-amber-600" />,
        };
      case "NATURALLY_SLOW":
        return {
          label: "Deliberate Thinker",
          tag: "Uninterrupted Cadence",
          color: "text-cyan-800 dark:text-cyan-300 bg-cyan-50 dark:bg-cyan-950/60 border-cyan-200 dark:border-cyan-800",
          dotColor: "#0891b2",
          desc: "Response time aligns with personal deliberate baseline. Popups suppressed.",
          icon: <Clock className="w-3.5 h-3.5 text-cyan-600" />,
        };
      case "CONFUSED":
        return {
          label: "Stuck / Confused",
          tag: "Socratic Scaffolding",
          color: "text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/60 border-rose-200 dark:border-rose-800",
          dotColor: "#ef4444",
          desc: "High hesitation ratio detected. Step-by-step Socratic explanation dispatched.",
          icon: <Brain className="w-3.5 h-3.5 text-rose-600" />,
        };
      default:
        return {
          label: "Focused & Steady",
          tag: "Optimal Cadence",
          color: "text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-800",
          dotColor: "#10b981",
          desc: "Optimal response cadence and accurate progression. Cognitive load minimal.",
          icon: <Activity className="w-3.5 h-3.5 text-emerald-600" />,
        };
    }
  };

  const cogDisplay = getCognitiveStateDisplay();

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#6A35D8]/10 text-[#6A35D8] flex items-center justify-center font-bold">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Live Cognitive & Telemetry Meter
            </h3>
            <p className="text-[10px] text-slate-400">Non-Intrusive Cadence & Persona-Normalized Detection</p>
          </div>
        </div>

        {/* Live WebSocket status indicator */}
        <div
          className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
            isConnected
              ? "bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-950/50 dark:border-emerald-800"
              : "bg-slate-50 text-slate-500 border-slate-200 dark:bg-slate-800 dark:border-slate-700"
          }`}
          title={isConnected ? "WebSocket connected: live 2s updates" : "WebSocket offline (polling)"}
        >
          {isConnected ? (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
              <Wifi className="w-3 h-3" />
              <span>Live (2s)</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3 h-3" />
              <span>Offline</span>
            </>
          )}
        </div>
      </div>

      <div className="flex items-center gap-5">
        {/* 5-segment vertical bar: Red at top, Green at bottom */}
        <div
          className="flex flex-col gap-1.5 justify-between py-1"
          style={{ height: 160, width: 44 }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          {SEGMENTS.map((seg, idx) => {
            const isFilled = currentScore >= seg.threshold;

            return (
              <div
                key={idx}
                className="group relative flex-1 rounded-lg transition-all duration-500 ease-out flex items-center justify-center"
                style={{
                  backgroundColor: isFilled ? seg.activeColor : "#e2e8f0",
                  boxShadow: isFilled
                    ? `0 0 10px ${seg.activeColor}55, inset 0 1px 1px rgba(255,255,255,0.4)`
                    : "none",
                  transform: isFilled ? "scale(1.03)" : "scale(1)",
                }}
              >
                <div className="absolute left-12 whitespace-nowrap bg-slate-900 text-white text-[10px] font-semibold px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-20">
                  {seg.label} (≥ {Math.round(seg.threshold * 100)}%)
                </div>
              </div>
            );
          })}
        </div>

        {/* Status Metrics */}
        <div className="flex-1 space-y-2.5">
          <div className="flex items-baseline justify-between flex-wrap gap-1">
            <div>
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {percentage}%
              </span>
              <span className="text-xs text-slate-400 font-medium ml-1">confusion score</span>
            </div>
            {/* Personal Pace Factor Badge */}
            <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              Personal Pace: <strong>{paceFactor.toFixed(1)}x</strong> {paceFactor >= 1.3 ? "(Deliberate)" : "(Steady)"}
            </span>
          </div>

          {/* Cognitive State Badge */}
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border ${cogDisplay.color}`}
            >
              {cogDisplay.icon}
              <span>{cogDisplay.label}</span>
            </span>

            {cooldownSecs > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-bold bg-purple-100 text-purple-700 border border-purple-300 animate-pulse">
                <ShieldAlert className="w-3 h-3" />
                <span>Cooldown: {cooldownSecs}s</span>
              </span>
            )}
          </div>

          <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
            {cogDisplay.desc}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ConfusionMeter;
