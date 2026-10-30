import React, { useState, useEffect, useCallback } from "react";
import {
  HeatmapResponse,
  HealthStatus,
  Concept,
  StudentSummary,
  HeatmapCell,
} from "../types/api";
import {
  Users,
  ArrowLeft,
  Activity,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Server,
  Zap,
  Sparkles,
  Play,
  Layers,
  HelpCircle,
} from "lucide-react";

interface TeacherProps {
  onNavigateStudent: () => void;
}

export const Teacher: React.FC<TeacherProps> = ({ onNavigateStudent }) => {
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCell, setSelectedCell] = useState<{
    student: StudentSummary;
    concept: Concept;
    cell: HeatmapCell;
  } | null>(null);
  const [simMessage, setSimMessage] = useState<string>("");

  const fetchHeatmap = useCallback(async () => {
    setIsLoading(true);
    try {
      const [resHeatmap, resHealth] = await Promise.all([
        fetch("/api/class/heatmap"),
        fetch("/api/health"),
      ]);
      if (resHeatmap.ok) {
        const data = await resHeatmap.json();
        setHeatmap(data);
      }
      if (resHealth.ok) {
        const healthData = await resHealth.json();
        setHealth(healthData);
      }
    } catch (err) {
      console.error("Error fetching teacher data:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHeatmap();
    const interval = setInterval(fetchHeatmap, 5000);
    return () => clearInterval(interval);
  }, [fetchHeatmap]);

  // Simulate a student telemetry profile across concepts for hackathon demonstration
  const triggerSimulation = async (
    personaName: string,
    state: "confused" | "hesitant" | "focused"
  ) => {
    setSimMessage(`Simulating telemetry for ${personaName} across all curriculum concepts...`);
    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona: personaName,
          profile: state,
        }),
      });

      if (res.ok) {
        setSimMessage(`Simulation recorded for ${personaName}! Heatmap refreshed.`);
        await fetchHeatmap();
      } else {
        // Fallback to single session
        const sessRes = await fetch("/api/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ profile: state }),
        });
        if (sessRes.ok) {
          const sess = await sessRes.json();
          await fetch("/api/events", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sess.session_id,
              question_id: sess.question.id,
              type: state === "confused" ? "lost" : "submit",
              features: {
                idle_time: state === "confused" ? 28.0 : state === "hesitant" ? 14.0 : 4.0,
                edit_count: state === "confused" ? 4 : state === "hesitant" ? 2 : 0,
                retries: state === "confused" ? 3 : state === "hesitant" ? 1 : 0,
                backspace_rate: state === "confused" ? 0.35 : 0.05,
                focus_lost_count: state === "confused" ? 2 : 0,
              },
              answer: state === "focused" ? sess.question.correct_answer : "incorrect answer",
            }),
          });
          setSimMessage(`Simulation recorded for ${personaName}. Heatmap refreshed!`);
          await fetchHeatmap();
        }
      }
    } catch (err) {
      setSimMessage(`Simulation error: ${err}`);
    }
  };

  // Helper: map confusion score to cell background color
  const getCellColor = (score: number) => {
    if (score >= 0.65) {
      return {
        bg: "bg-red-500 hover:bg-red-600 text-white shadow-red-500/20",
        label: "Confused",
      };
    }
    if (score >= 0.35) {
      return {
        bg: "bg-[#F25C1E] hover:bg-orange-600 text-white shadow-orange-500/20",
        label: "Hesitant",
      };
    }
    return {
      bg: "bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-500/20",
      label: "Calm",
    };
  };

  const students = heatmap?.students || [];
  const concepts = heatmap?.concepts || [];
  const cells = heatmap?.cells || [];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-6 py-4 sticky top-0 z-30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onNavigateStudent}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Student View</span>
          </button>
          <div className="h-5 w-px bg-slate-200 dark:bg-slate-700" />
          <div>
            <h1 className="font-extrabold text-slate-900 dark:text-white text-lg tracking-tight flex items-center gap-2">
              Teacher Analytics Heatmap
              <span
                className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: "rgba(106, 53, 216, 0.12)",
                  color: "#6A35D8",
                }}
              >
                Live Cohort Matrix
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Real-time cognitive load & concept confusion matrix
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchHeatmap}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </header>

      {/* Main Grid View */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Health & Fallback Status Banner */}
        {health && (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center font-black"
                style={{
                  backgroundColor: "rgba(106, 53, 216, 0.12)",
                  color: "#6A35D8",
                }}
              >
                <Server className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  System Health & Uptime Status
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      health.groq_ok
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-amber-50 text-amber-700 border border-amber-200"
                    }`}
                  >
                    {health.groq_ok ? (
                      <>
                        <CheckCircle className="w-3 h-3 text-emerald-500" />
                        Groq Online
                      </>
                    ) : (
                      <>
                        <Zap className="w-3 h-3 text-amber-500" />
                        Offline Bank Active
                      </>
                    )}
                  </span>
                </span>
                <p className="text-[11px] text-slate-400">
                  Mode: <strong className="text-slate-600 dark:text-slate-300 capitalize">{health.mode}</strong> | Primary Model: {health.models?.[0] || "llama-3.1-8b-instant"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-medium text-slate-600 dark:text-slate-300">
              <div className="bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
                <span className="text-slate-400 text-[10px] block">Cache Hits:</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {health.cache_hits}
                </span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
                <span className="text-slate-400 text-[10px] block">Offline Fallbacks Used:</span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {health.offline_used}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Live Simulation Trigger Controls for Hackathon Judges */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3 mb-2">
            <span
              className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5"
              style={{ color: "#6A35D8" }}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Hackathon Persona Simulation Controls
            </span>
            {simMessage && (
              <span className="text-xs text-slate-500 italic animate-fade-in font-medium">
                {simMessage}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mb-3">
            Inject realistic student telemetry to see the heatmap matrix update live:
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => triggerSimulation("Alex (High Hesitation)", "confused")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-50 hover:bg-red-100 text-red-700 text-xs font-bold border border-red-200 transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Simulate Confused Student</span>
            </button>
            <button
              onClick={() => triggerSimulation("Sam (Pauses & Edits)", "hesitant")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-orange-50 hover:bg-orange-100 text-orange-700 text-xs font-bold border border-orange-200 transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Simulate Hesitant Student</span>
            </button>
            <button
              onClick={() => triggerSimulation("Maya (Steady Cadence)", "focused")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-bold border border-emerald-200 transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Simulate Focused Student</span>
            </button>
          </div>
        </div>

        {/* The N x M Confusion Heatmap Grid */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-md p-6 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-base font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-[#6A35D8]" />
                Student vs Concept Confusion Matrix
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Cells colored by real-time confusion score. Click any cell to inspect the pedagogical diagnostic reasoning.
              </p>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs font-semibold">
              <div className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded bg-emerald-500 inline-block shadow-sm"></span>
                <span className="text-slate-600 dark:text-slate-300">Calm (0 - 35%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded bg-[#F25C1E] inline-block shadow-sm"></span>
                <span className="text-slate-600 dark:text-slate-300">Hesitant (35 - 65%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded bg-red-500 inline-block shadow-sm"></span>
                <span className="text-slate-600 dark:text-slate-300">Confused (&gt; 65%)</span>
              </div>
            </div>
          </div>

          {/* Matrix Table */}
          {students.length > 0 && concepts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="text-left font-bold text-xs uppercase tracking-wider text-slate-400 py-3 px-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40 rounded-tl-xl w-48">
                      Student
                    </th>
                    {concepts.map((concept) => (
                      <th
                        key={concept.id}
                        className="text-center font-bold text-xs text-slate-700 dark:text-slate-200 py-3 px-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40 min-w-[130px]"
                      >
                        <span className="block truncate max-w-[140px] mx-auto" title={concept.name}>
                          {concept.name}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {students.map((student, sIdx) => {
                    const rowCells = cells[sIdx] || [];
                    return (
                      <tr key={student.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 font-semibold text-xs text-slate-900 dark:text-white">
                          <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-[#6A35D8]" />
                            <span className="font-bold">{student.name}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 font-mono block pl-4">
                            ID: {student.id.slice(0, 10)}
                          </span>
                        </td>
                        {concepts.map((concept, cIdx) => {
                          const cell = rowCells[cIdx] || { confusion: 0.1, why: "" };
                          const confScore = Math.max(0.0, Math.min(1.0, cell.confusion));
                          const percentage = Math.round(confScore * 100);
                          const { bg } = getCellColor(confScore);
                          const isSelected =
                            selectedCell?.student.id === student.id &&
                            selectedCell?.concept.id === concept.id;

                          return (
                            <td key={concept.id} className="p-2 text-center">
                              <button
                                type="button"
                                onClick={() =>
                                  setSelectedCell({
                                    student,
                                    concept,
                                    cell,
                                  })
                                }
                                className={`w-full py-2.5 px-2 rounded-xl text-xs font-bold transition-all shadow-sm ${bg} ${
                                  isSelected
                                    ? "ring-4 ring-[#6A35D8] scale-105 z-10"
                                    : ""
                                }`}
                                title={`${percentage}% confusion - ${cell.why}`}
                              >
                                {percentage}%
                              </button>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[#6A35D8]" />
              <p className="text-xs">Loading class heatmap matrix...</p>
            </div>
          )}

          {/* Diagnostic Inspection Drawer for Selected Cell */}
          {selectedCell && (
            <div className="mt-6 p-4 rounded-2xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 animate-slide-up">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-[#6A35D8] flex items-center gap-1.5">
                  <Layers className="w-4 h-4" />
                  Diagnostic Telemetry Inspector
                </span>
                <button
                  onClick={() => setSelectedCell(null)}
                  className="text-xs text-slate-400 hover:text-slate-600 font-bold"
                >
                  ✕ Close
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px]">Student:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {selectedCell.student.name}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Concept:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {selectedCell.concept.name}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Confusion Score:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {Math.round(selectedCell.cell.confusion * 100)}% (
                    {selectedCell.cell.confusion >= 0.65
                      ? "Confused"
                      : selectedCell.cell.confusion >= 0.35
                      ? "Hesitant"
                      : "Calm"}
                    )
                  </span>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-purple-200 dark:border-purple-800 text-xs text-slate-700 dark:text-slate-300">
                <span className="font-bold block mb-1">Contributing Diagnostic Signals:</span>
                <p className="font-mono text-[11px] bg-white dark:bg-slate-900 p-2.5 rounded-xl border border-purple-100 dark:border-purple-900">
                  {selectedCell.cell.why || "Cadence optimal; no negative cognitive signals."}
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Teacher;
