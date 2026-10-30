import React, { useEffect, useRef, useState } from "react";
import { ConfusionData, ConfusionState } from "../types/api";
import { Activity, Wifi, WifiOff } from "lucide-react";

interface ConfusionMeterProps {
  sessionId?: string;
  data?: ConfusionData;
  score?: number;
  state?: ConfusionState;
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
  isWsConnected: propIsWsConnected,
}) => {
  const [internalData, setInternalData] = useState<{ score: number; state: string }>({
    score: propScore ?? propData?.score ?? 0.05,
    state: propState ?? propData?.state ?? "calm",
  });
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync with prop updates if provided
  useEffect(() => {
    if (propData) {
      setInternalData({
        score: propData.score,
        state: propData.state,
      });
    } else if (propScore !== undefined) {
      setInternalData((prev) => ({
        ...prev,
        score: propScore,
        state: propState ?? prev.state,
      }));
    }
  }, [propData, propScore, propState]);

  // Connect live WebSocket if sessionId is provided
  useEffect(() => {
    if (!sessionId) return;

    function connect() {
      const isHttps = typeof window !== "undefined" && window.location.protocol === "https:";
      const host = typeof window !== "undefined" ? window.location.host : "localhost:8000";
      const wsProtocol = isHttps ? "wss:" : "ws:";
      
      // Use local vite proxy or direct connection
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
            if (payload && typeof payload.score === "number") {
              setInternalData({
                score: Math.max(0.0, Math.min(1.0, payload.score)),
                state: payload.state || "calm",
              });
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
  const currentState = internalData.state;
  const percentage = Math.round(currentScore * 100);
  const isConnected = propIsWsConnected !== undefined ? propIsWsConnected : wsConnected;

  // Format state label
  const stateLabel =
    currentState === "calm" || currentState === "focused"
      ? "Calm & Focused"
      : currentState === "hesitant" || currentState === "mild" || currentState === "uncertain"
      ? "Hesitant"
      : "Confused";

  const stateColor =
    currentScore >= 0.65
      ? "text-red-500 bg-red-50 dark:bg-red-950/60 border-red-200 dark:border-red-900"
      : currentScore >= 0.35
      ? "text-[#F25C1E] bg-orange-50 dark:bg-orange-950/60 border-orange-200 dark:border-orange-900"
      : "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-900";

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#6A35D8]/10 text-[#6A35D8] flex items-center justify-center font-bold">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Live Confusion Meter
            </h3>
            <p className="text-[10px] text-slate-400">Passive Telemetry Detection</p>
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
            // A segment is filled if score reaches or exceeds threshold
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
                {/* Tooltip on hover */}
                <div className="absolute left-12 whitespace-nowrap bg-slate-900 text-white text-[10px] font-semibold px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-20">
                  {seg.label} (≥ {Math.round(seg.threshold * 100)}%)
                </div>
              </div>
            );
          })}
        </div>

        {/* Status Metrics */}
        <div className="flex-1 space-y-2.5">
          <div>
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              {percentage}%
            </span>
            <span className="text-xs text-slate-400 font-medium ml-1">confusion</span>
          </div>

          <div>
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border capitalize ${stateColor}`}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor:
                    currentScore >= 0.65
                      ? "#ef4444"
                      : currentScore >= 0.35
                      ? "#F25C1E"
                      : "#22c55e",
                }}
              />
              {stateLabel}
            </span>
          </div>

          <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
            {currentScore >= 0.65
              ? "High hesitation detected. Multimodal intervention prepared."
              : currentScore >= 0.35
              ? "Moderate pauses observed. Monitoring response cadence."
              : "Steady interaction cadence. Cognitive load is optimal."}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ConfusionMeter;
