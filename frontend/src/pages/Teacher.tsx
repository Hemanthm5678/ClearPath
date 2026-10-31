import React, { useState, useEffect, useCallback } from "react";
import {
  HeatmapResponse,
  HealthStatus,
  Concept,
  StudentSummary,
  HeatmapCell,
  CognitiveState,
  User,
} from "../types/api";
import { DarkModeToggle } from "../components/DarkModeToggle";
import { AddQuestionModal } from "../components/AddQuestionModal";
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
  Clock,
  ShieldAlert,
  Brain,
  PlusCircle,
} from "lucide-react";

interface TeacherProps {
  currentUser?: User | null;
  onLogout?: () => void;
  onNavigateStudent: () => void;
}

export const Teacher: React.FC<TeacherProps> = ({
  currentUser,
  onLogout,
  onNavigateStudent,
}) => {
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCell, setSelectedCell] = useState<{
    student: StudentSummary;
    concept: Concept;
    cell: HeatmapCell;
  } | null>(null);
  const [simMessage, setSimMessage] = useState<string>("");
  const [showAddQuestionModal, setShowAddQuestionModal] = useState<boolean>(false);

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
    profile: "confused" | "bored" | "gaming" | "naturally_slow" | "focused"
  ) => {
    setSimMessage(`Simulating telemetry for ${personaName}...`);
    try {
      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          persona: personaName,
          profile,
        }),
      });

      if (res.ok) {
        setSimMessage(`Simulation recorded for ${personaName}! Heatmap refreshed.`);
        await fetchHeatmap();
      } else {
        setSimMessage(`Simulation endpoint responded with status ${res.status}`);
      }
    } catch (err) {
      setSimMessage(`Simulation error: ${err}`);
    }
  };

  // Helper: map Cognitive State to cell background color & badge
  // Color-coded by state:
  // Green: FOCUSED
  // Blue/Teal: NATURALLY_SLOW (No intervention needed)
  // Yellow/Amber: BORED
  // Purple: GAMING
  // Red: CONFUSED
  const getCellColor = (cell: HeatmapCell) => {
    const cog = cell.cognitive_state?.toUpperCase();
    const score = cell.confusion;

    if (cog === "GAMING") {
      return {
        bg: "bg-purple-600 hover:bg-purple-700 text-white shadow-purple-600/30",
        label: "GAMING",
        badgeClass: "bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-950/60 dark:border-purple-800",
      };
    }
    if (cog === "BORED") {
      return {
        bg: "bg-amber-500 hover:bg-amber-600 text-white shadow-amber-500/30",
        label: "BORED",
        badgeClass: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/60 dark:border-amber-800",
      };
    }
    if (cog === "NATURALLY_SLOW") {
      return {
        bg: "bg-cyan-600 hover:bg-cyan-700 text-white shadow-cyan-600/30",
        label: "NATURALLY SLOW",
        badgeClass: "bg-cyan-100 text-cyan-800 border-cyan-300 dark:bg-cyan-950/60 dark:border-cyan-800",
      };
    }
    if (cog === "CONFUSED" || score >= 0.65) {
      return {
        bg: "bg-red-500 hover:bg-red-600 text-white shadow-red-500/30",
        label: "CONFUSED",
        badgeClass: "bg-red-100 text-red-700 border-red-300 dark:bg-red-950/60 dark:border-red-800",
      };
    }
    return {
      bg: "bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-500/30",
      label: "FOCUSED",
      badgeClass: "bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-950/60 dark:border-emerald-800",
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
              Cognitive State & Closed-Loop Telemetry Verification
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <DarkModeToggle showLabel={false} />

          {currentUser && (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-orange-50 dark:bg-orange-950/50 border border-orange-200/60 dark:border-orange-800/40 text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="font-bold text-[#F25C1E] dark:text-orange-300">
                  {currentUser.name}
                </span>
                <span className="text-[10px] text-slate-400 capitalize">
                  ({currentUser.role})
                </span>
              </div>
              {onLogout && (
                <button
                  onClick={onLogout}
                  title="Switch Account or Role"
                  className="text-[11px] font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 underline"
                >
                  Switch
                </button>
              )}
            </div>
          )}

          <button
            onClick={() => setShowAddQuestionModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#6A35D8] hover:bg-[#562ab3] text-white text-xs font-bold shadow-md shadow-purple-500/20 transition-all hover:scale-105 active:scale-95"
            title="Author a new MCQ with AI Tutor auto-scaffolding"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>+ Add New Question</span>
          </button>

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
      <main className="flex-1 max-w-[1720px] w-full mx-auto px-4 sm:px-8 py-6 space-y-6">
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
          <div className="flex items-center justify-between gap-3 mb-2 flex-wrap">
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
            Inject realistic student telemetry across 5 Cognitive States to see the heatmap update live:
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => triggerSimulation("Alex (High Confusion)", "confused")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-50 hover:bg-red-100 text-red-700 text-xs font-bold border border-red-200 transition-colors"
            >
              <Brain className="w-3.5 h-3.5" />
              <span>Simulate Confused</span>
            </button>
            <button
              onClick={() => triggerSimulation("Taylor (Bored / Guessing)", "bored")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-bold border border-amber-200 transition-colors"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Simulate Bored / Guessing</span>
            </button>
            <button
              onClick={() => triggerSimulation("Casey (Hint Gaming)", "gaming")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs font-bold border border-purple-200 transition-colors"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Simulate Gaming Hints</span>
            </button>
            <button
              onClick={() => triggerSimulation("Sam (Deliberate Thinker)", "naturally_slow")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-50 hover:bg-cyan-100 text-cyan-700 text-xs font-bold border border-cyan-200 transition-colors"
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Simulate Naturally Slow</span>
            </button>
            <button
              onClick={() => triggerSimulation("Maya (Steady Cadence)", "focused")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-bold border border-emerald-200 transition-colors"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Simulate Focused</span>
            </button>
          </div>
        </div>

        {/* The N x M Confusion Heatmap Grid */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-md p-6 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-base font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                  <Users className="w-5 h-5 text-[#6A35D8]" />
                  Student vs Concept Cognitive Heatmap Matrix
                </h2>
                <button
                  type="button"
                  onClick={() => setShowAddQuestionModal(true)}
                  className="hidden sm:flex items-center gap-1 text-xs font-bold text-[#6A35D8] dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300 bg-purple-50 dark:bg-purple-950/60 px-2.5 py-1 rounded-lg border border-purple-200/60 dark:border-purple-800/40 transition-colors"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>+ Author New Question</span>
                </button>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Cells color-coded by detected Cognitive State. Click any cell to inspect Hint 1 breakdown & Hint 3 efficacy verification.
              </p>
            </div>

            {/* 5-State Legend */}
            <div className="flex flex-wrap items-center gap-3 text-xs font-semibold">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-emerald-500 inline-block shadow-sm"></span>
                <span className="text-slate-600 dark:text-slate-300">Focused (Green)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-cyan-600 inline-block shadow-sm"></span>
                <span className="text-slate-600 dark:text-slate-300">Naturally Slow (Teal)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-amber-500 inline-block shadow-sm"></span>
                <span className="text-slate-600 dark:text-slate-300">Bored (Amber)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-purple-600 inline-block shadow-sm"></span>
                <span className="text-slate-600 dark:text-slate-300">Gaming (Purple)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-red-500 inline-block shadow-sm"></span>
                <span className="text-slate-600 dark:text-slate-300">Confused (Red)</span>
              </div>
            </div>
          </div>

          {/* Matrix Table */}
          {students.length > 0 && concepts.length > 0 ? (
            <div className="overflow-x-auto scrollbar-thin">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="text-left font-bold text-xs uppercase tracking-wider text-slate-400 py-3.5 px-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40 rounded-tl-xl w-44 min-w-[150px]">
                      Student Profile
                    </th>
                    {concepts.map((concept) => (
                      <th
                        key={concept.id}
                        className="text-center font-bold text-xs text-slate-700 dark:text-slate-200 py-3 px-2 border-b border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40 min-w-[115px]"
                      >
                        <span className="block text-[11px] font-bold leading-tight mx-auto max-w-[125px]" title={concept.name}>
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
                          const { bg, label } = getCellColor(cell);
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
                                title={`${label}: ${percentage}% confusion - ${cell.why}`}
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

          {/* Clickable Telemetry Diagnostic Drawer for Selected Cell */}
          {selectedCell && (
            <div className="mt-6 p-5 rounded-2xl bg-purple-50/70 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 animate-slide-up space-y-4">
              <div className="flex items-center justify-between border-b border-purple-200 dark:border-purple-800 pb-3">
                <span className="text-xs font-bold text-[#6A35D8] flex items-center gap-1.5 uppercase tracking-wider">
                  <Layers className="w-4 h-4" />
                  Telemetry Diagnostic & Efficacy Drawer
                </span>
                <button
                  onClick={() => setSelectedCell(null)}
                  className="text-xs text-slate-400 hover:text-slate-600 font-bold px-2 py-1 rounded-lg hover:bg-white dark:hover:bg-slate-800 transition-colors"
                >
                  ✕ Close
                </button>
              </div>

              {/* Student & Cell Metadata */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Student:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {selectedCell.student.name}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Concept:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {selectedCell.concept.name}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Cognitive State:</span>
                  <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold border mt-0.5 ${getCellColor(selectedCell.cell).badgeClass}`}>
                    {selectedCell.cell.cognitive_state || "FOCUSED"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Confusion Score:</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    {Math.round(selectedCell.cell.confusion * 100)}%
                  </span>
                </div>
              </div>

              {/* Hint 1 Breakdown: Why this state was chosen */}
              <div className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-purple-100 dark:border-purple-900/60 shadow-sm">
                <div className="flex items-center gap-2 mb-1.5">
                  <Clock className="w-3.5 h-3.5 text-[#6A35D8]" />
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    Hint 1: Persona-Normalized & Complexity-Scaled Breakdown
                  </span>
                </div>
                <p className="font-mono text-xs text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-950 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800">
                  {selectedCell.cell.breakdown || selectedCell.cell.why || "Cadence optimal; response matches student baseline."}
                </p>
              </div>

              {/* Hint 3 Verification Card: Closed-Loop Intervention Efficacy */}
              <div className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-purple-100 dark:border-purple-900/60 shadow-sm">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                      Hint 3: Closed-Loop Intervention Efficacy Verification
                    </span>
                  </div>
                  {selectedCell.cell.efficacy?.status && (
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border ${
                        selectedCell.cell.efficacy.status === "HELPED"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                          : selectedCell.cell.efficacy.status === "UNRESOLVED"
                          ? "bg-rose-50 text-rose-700 border-rose-300"
                          : "bg-blue-50 text-blue-700 border-blue-300"
                      }`}
                    >
                      {selectedCell.cell.efficacy.status}
                    </span>
                  )}
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-[11px]">
                    <div>
                      <span className="text-slate-400 block text-[9px]">BEFORE INTERVENTION:</span>
                      <strong className="text-amber-600">{selectedCell.cell.efficacy?.state_before || selectedCell.cell.cognitive_state || "CONFUSED"}</strong>
                    </div>
                    <div className="text-slate-400">➔</div>
                    <div>
                      <span className="text-slate-400 block text-[9px]">ACTION DISPATCHED:</span>
                      <strong className="text-purple-600">
                        {selectedCell.cell.cognitive_state === "GAMING"
                          ? "10s Cooldown Lock + Self-Check"
                          : selectedCell.cell.cognitive_state === "BORED"
                          ? "Rapid Streak Challenge"
                          : selectedCell.cell.cognitive_state === "NATURALLY_SLOW"
                          ? "Popup Suppression (Autonomous)"
                          : "Socratic Re-explanation"}
                      </strong>
                    </div>
                    <div className="text-slate-400">➔</div>
                    <div>
                      <span className="text-slate-400 block text-[9px]">OUTCOME:</span>
                      <strong className={selectedCell.cell.efficacy?.status === "HELPED" ? "text-emerald-600" : "text-rose-600"}>
                        {selectedCell.cell.efficacy?.state_after || selectedCell.cell.cognitive_state || "RESOLVED"}
                      </strong>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed italic">
                    {selectedCell.cell.efficacy?.summary_text ||
                      "✅ Verified Autonomous: Student pace matches deliberate profile. Intervention withheld to prevent cognitive friction."}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* AI Question Authoring Studio Modal */}
      <AddQuestionModal
        isOpen={showAddQuestionModal}
        onClose={() => setShowAddQuestionModal(false)}
        concepts={concepts}
        onQuestionCreated={() => fetchHeatmap()}
        onNavigateStudent={onNavigateStudent}
      />
    </div>
  );
};

export default Teacher;
