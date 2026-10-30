import React, { useState, useEffect, useCallback } from 'react';
import { 
  HeatmapResponse, 
  HealthStatus, 
  Concept, 
  StudentSummary, 
  HeatmapCell 
} from '../types/api';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  Cell as RechartsCell,
  LineChart,
  Line
} from 'recharts';
import { 
  Users, 
  ArrowLeft, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw, 
  Server, 
  Zap, 
  Database,
  Layers,
  Sparkles,
  Play
} from 'lucide-react';

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
  const [simMessage, setSimMessage] = useState<string>('');

  const fetchHeatmap = useCallback(async () => {
    setIsLoading(true);
    try {
      const [resHeatmap, resHealth] = await Promise.all([
        fetch('/api/class/heatmap'),
        fetch('/api/health'),
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
      console.error('Error fetching teacher data:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHeatmap();
    const interval = setInterval(fetchHeatmap, 6000);
    return () => clearInterval(interval);
  }, [fetchHeatmap]);

  // Simulate a student event for hackathon live judge demo
  const triggerSimulation = async (personaName: string, state: 'confused' | 'hesitant' | 'focused') => {
    setSimMessage(`Simulating telemetry for ${personaName} (${state})...`);
    try {
      const dwell = state === 'confused' ? 28000 : state === 'hesitant' ? 16000 : 6000;
      const pause = state === 'confused' ? 22000 : state === 'hesitant' ? 10000 : 2000;
      const edits = state === 'confused' ? 4 : state === 'hesitant' ? 2 : 0;
      const switches = state === 'confused' ? 3 : state === 'hesitant' ? 1 : 0;
      const hints = state === 'confused' ? 1 : 0;

      // Start or retrieve session
      const sessRes = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: state }),
      });
      if (sessRes.ok) {
        const sess = await sessRes.json();
        await fetch('/api/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sess.session_id,
            question_id: sess.question.id,
            type: state === 'confused' ? 'lost' : 'submit',
            features: {
              dwell_time_ms: dwell,
              pause_duration_ms: pause,
              edit_count: edits,
              option_switches: switches,
              hint_clicks: hints,
              lost_clicks: state === 'confused' ? 1 : 0,
              rapid_clicks: state === 'confused' ? 2 : 0,
            },
            answer: state === 'focused' ? sess.question.correct_answer : 'wrong_answer',
          }),
        });
      }
      await fetchHeatmap();
      setSimMessage(`Injected real-time event for ${personaName}!`);
      setTimeout(() => setSimMessage(''), 4000);
    } catch (e) {
      setSimMessage('Simulation error occurred.');
    }
  };

  // Prepare chart data
  const chartData = heatmap
    ? heatmap.students.map((s) => ({
        name: s.name.split(' ')[0],
        confusionScore: Math.round(s.score * 100),
        state: s.state,
      }))
    : [];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      {/* Header */}
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-6 py-4 sticky top-0 z-30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onNavigateStudent}
            className="p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Return to Student View"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="font-extrabold text-slate-900 dark:text-white text-lg tracking-tight flex items-center gap-2">
              Teacher Analytics & Class Heatmap
              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                Live Class Monitoring
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Real-time cognitive state tracking across concepts with XGBoost + BKT
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchHeatmap}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={onNavigateStudent}
            className="px-4 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-md shadow-brand-500/20 transition-all"
          >
            Student View
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* System Health & Status Banner (Spec Section 8 GET /api/health) */}
        {health && (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm grid grid-cols-2 sm:grid-cols-5 gap-4 text-xs">
            <div>
              <span className="text-slate-400 font-medium block">Mode</span>
              <span className="font-bold text-slate-900 dark:text-white uppercase font-mono">
                {health.mode}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block">Groq API Status</span>
              <span className={`font-bold inline-flex items-center gap-1 ${health.groq_ok ? 'text-emerald-600' : 'text-amber-600'}`}>
                <span className={`w-2 h-2 rounded-full ${health.groq_ok ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}></span>
                {health.groq_ok ? 'Online' : 'Offline Bank Ready'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block">Model Chain</span>
              <span className="font-mono text-slate-700 dark:text-slate-300 font-bold truncate block" title={health.models.join(', ')}>
                {health.models[0]}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block">Fast Cache Hits</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400 font-mono text-sm">
                {health.cache_hits}
              </span>
            </div>
            <div>
              <span className="text-slate-400 font-medium block">Offline Fallbacks Used</span>
              <span className="font-bold text-amber-600 dark:text-amber-400 font-mono text-sm">
                {health.offline_used}
              </span>
            </div>
          </div>
        )}

        {/* Hackathon Judge Simulation Bar */}
        <div className="bg-brand-50/70 dark:bg-brand-950/30 rounded-2xl border border-brand-200 dark:border-brand-900/40 p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <span className="text-xs font-bold text-slate-900 dark:text-white">
              Hackathon Judge Controls:
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 hidden md:inline">
              Simulate live student personas into the heatmap in one click:
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => triggerSimulation('Liam (Confused)', 'confused')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500 text-white font-semibold text-xs shadow-sm hover:bg-rose-600 transition-colors"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Simulate Confused Student</span>
            </button>
            <button
              onClick={() => triggerSimulation('Maya (Hesitant)', 'hesitant')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 text-white font-semibold text-xs shadow-sm hover:bg-amber-600 transition-colors"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Simulate Hesitant Student</span>
            </button>
            <button
              onClick={() => triggerSimulation('Sophia (Mastery)', 'focused')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-semibold text-xs shadow-sm hover:bg-emerald-700 transition-colors"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Simulate Confident Student</span>
            </button>
          </div>
        </div>

        {simMessage && (
          <div className="p-3 bg-brand-500 text-white rounded-xl text-xs font-semibold animate-fade-in text-center">
            {simMessage}
          </div>
        )}

        {/* Heatmap Matrix Table */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-md overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white text-base flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand-600" />
                Student × Concept Confusion Matrix
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Click any cell to inspect Bayesian Knowledge Tracing diagnosis & reasons
              </p>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-emerald-500"></span>
                <span>Focused (&lt;35%)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-amber-500"></span>
                <span>Hesitant (35-65%)</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-rose-500"></span>
                <span>Confused (&gt;65%)</span>
              </span>
            </div>
          </div>

          {heatmap && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800">
                    <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-slate-400 bg-slate-50 dark:bg-slate-900/50">
                      Student
                    </th>
                    {heatmap.concepts.map((c) => (
                      <th
                        key={c.id}
                        className="py-3 px-3 text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 min-w-[120px]"
                      >
                        {c.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-sm">
                  {heatmap.students.map((student, rowIdx) => (
                    <tr key={student.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-white flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-700 dark:text-slate-300">
                          {student.name.charAt(0)}
                        </div>
                        <div>
                          <span>{student.name}</span>
                          <span className="block text-[11px] text-slate-400 font-mono">
                            {student.id.substring(0, 10)}
                          </span>
                        </div>
                      </td>

                      {heatmap.cells[rowIdx]?.map((cell, colIdx) => {
                        const concept = heatmap.concepts[colIdx];
                        const percentage = Math.round(cell.confusion * 100);

                        // Color coding
                        let cellBg = 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/50';
                        if (cell.confusion >= 0.65) {
                          cellBg = 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-300 dark:border-rose-800';
                        } else if (cell.confusion >= 0.35) {
                          cellBg = 'bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-800';
                        }

                        return (
                          <td key={colIdx} className="py-2.5 px-2">
                            <button
                              onClick={() => setSelectedCell({ student, concept, cell })}
                              className={`w-full py-2 px-2.5 rounded-xl border text-center transition-all hover:scale-105 shadow-sm font-mono text-xs font-bold ${cellBg}`}
                            >
                              <span>{percentage}%</span>
                              <span className="block text-[10px] font-sans font-medium opacity-80 capitalize">
                                {cell.state}
                              </span>
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Cell Drill-Down Modal */}
        {selectedCell && (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border-2 border-brand-500 p-5 shadow-xl animate-fade-in">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-brand-600" />
                <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                  Diagnostic Detail: {selectedCell.student.name} • {selectedCell.concept.name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedCell(null)}
                className="text-xs text-slate-400 hover:text-slate-600"
              >
                Close
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-slate-400 block font-medium">Confusion Probability</span>
                <span className="text-lg font-black text-slate-900 dark:text-white font-mono">
                  {Math.round(selectedCell.cell.confusion * 100)}%
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">State Diagnosis</span>
                <span className="text-sm font-bold capitalize text-slate-800 dark:text-slate-200">
                  {selectedCell.cell.state}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Pedagogical Trigger</span>
                <span className="text-xs font-mono text-brand-600 dark:text-brand-400">
                  {selectedCell.cell.why}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Recharts Analytics Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cohort Confusion Distribution */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-md">
            <h3 className="font-bold text-slate-900 dark:text-white text-sm mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-500" />
              Live Cohort Confusion Distribution
            </h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      color: '#fff',
                    }}
                  />
                  <Bar dataKey="confusionScore" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry, index) => {
                      const color =
                        entry.confusionScore >= 65
                          ? '#ef4444'
                          : entry.confusionScore >= 35
                          ? '#f59e0b'
                          : '#10b981';
                      return <RechartsCell key={`cell-${index}`} fill={color} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Average Concept Mastery Trend */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-md">
            <h3 className="font-bold text-slate-900 dark:text-white text-sm mb-4 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-500" />
              Mastery Progression across Concepts (BKT)
            </h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={
                    heatmap?.concepts.map((c, i) => {
                      // Calculate average mastery
                      let sum = 0;
                      heatmap.cells.forEach((row) => {
                        if (row[i]) sum += 1.0 - row[i].confusion;
                      });
                      const avgMastery = Math.round((sum / (heatmap.cells.length || 1)) * 100);
                      return {
                        name: c.name.split(' ')[0],
                        mastery: avgMastery,
                      };
                    }) || []
                  }
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      color: '#fff',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="mastery"
                    stroke="#6366f1"
                    strokeWidth={3}
                    dot={{ r: 4, fill: '#6366f1' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
