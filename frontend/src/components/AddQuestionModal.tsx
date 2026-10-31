import React, { useState } from 'react';
import {
  Sparkles,
  X,
  PlusCircle,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Eye,
  BookOpen,
  ListOrdered,
  Smile,
  ArrowRight,
  RefreshCw,
  Code2,
  Calculator,
} from 'lucide-react';
import { Concept, Question, QuestionAnalysis, CreateQuestionResponse } from '../types/api';

interface AddQuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  concepts: Concept[];
  onQuestionCreated?: (question: Question, analysis: QuestionAnalysis) => void;
  onNavigateStudent?: () => void;
}

export const AddQuestionModal: React.FC<AddQuestionModalProps> = ({
  isOpen,
  onClose,
  concepts,
  onQuestionCreated,
  onNavigateStudent,
}) => {
  const [selectedConcept, setSelectedConcept] = useState<string>(
    concepts[0]?.id || 'c8_quadratic_algebra'
  );
  const [prompt, setPrompt] = useState<string>('');
  const [options, setOptions] = useState<string[]>(['', '', '', '']);
  const [correctIdx, setCorrectIdx] = useState<number>(0);
  const [difficulty, setDifficulty] = useState<string>('auto');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [createdResult, setCreatedResult] = useState<{
    question: Question;
    analysis: QuestionAnalysis;
  } | null>(null);
  const [previewTab, setPreviewTab] = useState<'visual' | 'analogy' | 'step_by_step' | 'simple_language'>('visual');

  if (!isOpen) return null;

  const handleOptionChange = (index: number, value: string) => {
    const updated = [...options];
    updated[index] = value;
    setOptions(updated);
  };

  const loadTemplate = (type: 'math' | 'code' | 'fraction') => {
    setError(null);
    setCreatedResult(null);
    if (type === 'math') {
      setSelectedConcept('c8_quadratic_algebra');
      setPrompt('What is the nature and count of the real roots for the quadratic equation: 4x² - 12x + 9 = 0?');
      setOptions([
        'Exactly one real root (repeated rational root, Δ = 0)',
        'Two distinct irrational real roots (Δ > 0)',
        'Two complex conjugate imaginary roots (Δ < 0)',
        'No real or complex roots exist',
      ]);
      setCorrectIdx(0);
      setDifficulty('medium');
    } else if (type === 'code') {
      setSelectedConcept('c7_python_tracing');
      setPrompt(
        'What is the exact output printed by this Python snippet?\n\n```python\ndef transform(nums, factor=2):\n    return [n * factor for n in nums if n % 2 != 0]\n\nprint(transform([1, 2, 3, 4], 3))\n```'
      );
      setOptions(['[3, 9]', '[2, 6]', '[3, 6, 9, 12]', '[1, 3]']);
      setCorrectIdx(0);
      setDifficulty('medium');
    } else {
      setSelectedConcept('c5_comparing_fractions');
      setPrompt('Which statement correctly compares 3/7 and 4/9 using cross-multiplication?');
      setOptions([
        '4/9 is greater because 4 × 7 = 28 > 3 × 9 = 27',
        '3/7 is greater because 3 × 9 = 27 > 4 × 7 = 28',
        'They are exactly equal (27 = 28)',
        'Cannot be compared without decimal long division',
      ]);
      setCorrectIdx(0);
      setDifficulty('easy');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const filledOptions = options.map((o) => o.trim()).filter((o) => o.length > 0);
    if (!prompt.trim()) {
      setError('Please provide a question prompt.');
      return;
    }
    if (filledOptions.length < 2) {
      setError('Please provide at least 2 distinct options.');
      return;
    }
    const correctAnswer = options[correctIdx]?.trim();
    if (!correctAnswer) {
      setError('Please select a valid option as the correct answer.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch('/api/teacher/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          concept_id: selectedConcept,
          prompt: prompt.trim(),
          options: filledOptions,
          correct_answer: correctAnswer,
          difficulty,
        }),
      });

      const data: CreateQuestionResponse = await res.json();
      if (!res.ok) {
        throw new Error((data as any).detail || data.message || 'Failed to create question');
      }

      setCreatedResult({
        question: data.question,
        analysis: data.analysis,
      });

      if (onQuestionCreated) {
        onQuestionCreated(data.question, data.analysis);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to synthesize question with AI Tutor');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setPrompt('');
    setOptions(['', '', '', '']);
    setCorrectIdx(0);
    setError(null);
    setCreatedResult(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200 overflow-y-auto">
      <div className="relative w-full max-w-3xl bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden text-slate-800 dark:text-slate-100 transition-all my-8">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#6A35D8] to-[#9060eb] flex items-center justify-center text-white shadow-md shadow-purple-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                AI Question Authoring Studio
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-purple-100 text-[#6A35D8] dark:bg-purple-950 dark:text-purple-300">
                  Auto-Scaffolding
                </span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Add an MCQ to any existing topic. ClearPath's AI Tutor automatically analyzes the problem and generates 4 multimodal scaffolds.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 max-h-[80vh] overflow-y-auto">
          {createdResult ? (
            /* AI Tutor Synthesis Success Preview */
            <div className="space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-bold text-sm text-emerald-900 dark:text-emerald-200">
                    Question Successfully Published to Live Quiz!
                  </h3>
                  <p className="text-xs text-emerald-700 dark:text-emerald-300 mt-0.5">
                    Question ID <code className="font-mono">{createdResult.question.id}</code> is now active in the curriculum. The AI Tutor has generated all 4 multimodal explanation modalities below.
                  </p>
                </div>
              </div>

              {/* Analysis Metrics Badge */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                    AI Pedagogical Analysis
                  </span>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-purple-100 dark:bg-purple-950 text-[#6A35D8] dark:text-purple-300">
                      Tier: {createdResult.analysis.complexity_tier}
                    </span>
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                      Expected Time: {createdResult.analysis.expected_time_sec}s
                    </span>
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
                      Weight: {createdResult.analysis.complexity_weight}x
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-400">Synthesis Engine</span>
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-200 block">
                    {createdResult.analysis.source === 'groq' ? '⚡ Groq LLaMA 3.3 Versatile' : '🛡️ Offline Fallback Synthesizer'}
                  </span>
                </div>
              </div>

              {/* Socratic Hint */}
              <div className="p-3.5 rounded-xl bg-purple-50/70 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800/50 text-xs">
                <span className="font-bold text-[#6A35D8] dark:text-purple-300 flex items-center gap-1.5 mb-1">
                  <HelpCircle className="w-3.5 h-3.5" />
                  Auto-Generated Socratic Student Hint:
                </span>
                <p className="text-slate-700 dark:text-slate-300 italic">
                  "{createdResult.analysis.hint}"
                </p>
              </div>

              {/* 4 Modalities Preview Tabs */}
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                  AI Tutor Multimodal Scaffolding (Live Preview):
                </span>
                <div className="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl gap-1 mb-3">
                  <button
                    type="button"
                    onClick={() => setPreviewTab('visual')}
                    className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                      previewTab === 'visual'
                        ? 'bg-white dark:bg-slate-700 text-[#6A35D8] dark:text-purple-300 shadow-sm'
                        : 'text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Visual</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPreviewTab('analogy')}
                    className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                      previewTab === 'analogy'
                        ? 'bg-white dark:bg-slate-700 text-[#6A35D8] dark:text-purple-300 shadow-sm'
                        : 'text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Analogy</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPreviewTab('step_by_step')}
                    className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                      previewTab === 'step_by_step'
                        ? 'bg-white dark:bg-slate-700 text-[#6A35D8] dark:text-purple-300 shadow-sm'
                        : 'text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <ListOrdered className="w-3.5 h-3.5" />
                    <span>Step-by-Step</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPreviewTab('simple_language')}
                    className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                      previewTab === 'simple_language'
                        ? 'bg-white dark:bg-slate-700 text-[#6A35D8] dark:text-purple-300 shadow-sm'
                        : 'text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <Smile className="w-3.5 h-3.5" />
                    <span>Simple (ELI5)</span>
                  </button>
                </div>

                <div className="p-4 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 space-y-2">
                  <div className="text-xs text-slate-800 dark:text-slate-200 whitespace-pre-line leading-relaxed">
                    {createdResult.analysis.explanations[previewTab]?.explanation}
                  </div>
                  {createdResult.analysis.explanations[previewTab]?.check_question && (
                    <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 text-[11px] text-purple-700 dark:text-purple-300 font-semibold flex items-center gap-1.5">
                      <span>Check Question:</span>
                      <span className="font-normal italic">
                        {createdResult.analysis.explanations[previewTab]?.check_question}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors"
                >
                  + Add Another Question
                </button>
                <div className="flex items-center gap-2">
                  {onNavigateStudent && (
                    <button
                      type="button"
                      onClick={() => {
                        onClose();
                        onNavigateStudent();
                      }}
                      className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-[#6A35D8] hover:bg-[#562ab3] shadow-md shadow-purple-500/20 transition-all flex items-center gap-1.5"
                    >
                      <span>Test Question in Student View</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-100 transition-colors"
                  >
                    Close Studio
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Authoring Form */
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* 1-Click Judge Templates */}
              <div className="p-3 rounded-2xl bg-purple-50/50 dark:bg-purple-950/20 border border-purple-200/60 dark:border-purple-800/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#6A35D8] dark:text-purple-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    1-Click Judge Demonstration Templates
                  </span>
                  <span className="text-[10px] text-slate-400">Instant Pre-Fill</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => loadTemplate('math')}
                    className="p-2 rounded-xl bg-white dark:bg-slate-800 hover:bg-purple-50 dark:hover:bg-purple-900/30 border border-slate-200 dark:border-slate-700 text-left text-xs font-semibold transition-all flex items-center gap-2"
                  >
                    <Calculator className="w-4 h-4 text-[#F25C1E]" />
                    <span className="truncate">Quadratic Discriminant</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => loadTemplate('code')}
                    className="p-2 rounded-xl bg-white dark:bg-slate-800 hover:bg-purple-50 dark:hover:bg-purple-900/30 border border-slate-200 dark:border-slate-700 text-left text-xs font-semibold transition-all flex items-center gap-2"
                  >
                    <Code2 className="w-4 h-4 text-[#6A35D8]" />
                    <span className="truncate">Python Comprehension</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => loadTemplate('fraction')}
                    className="p-2 rounded-xl bg-white dark:bg-slate-800 hover:bg-purple-50 dark:hover:bg-purple-900/30 border border-slate-200 dark:border-slate-700 text-left text-xs font-semibold transition-all flex items-center gap-2"
                  >
                    <BookOpen className="w-4 h-4 text-emerald-600" />
                    <span className="truncate">Fraction Cross-Multiply</span>
                  </button>
                </div>
              </div>

              {/* Concept Picker */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Select Target Curriculum Concept
                  </label>
                  <select
                    value={selectedConcept}
                    onChange={(e) => setSelectedConcept(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-[#6A35D8] text-slate-900 dark:text-slate-100"
                  >
                    {concepts.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.id})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Difficulty Setting
                  </label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-[#6A35D8] text-slate-900 dark:text-slate-100"
                  >
                    <option value="auto">Auto-Detect (AI Managed)</option>
                    <option value="easy">Easy (20s • 1.0x)</option>
                    <option value="medium">Medium (50s • 1.8x)</option>
                    <option value="hard">Hard (75s • 2.5x)</option>
                  </select>
                </div>
              </div>

              {/* Prompt Textarea */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                    Question Prompt / Problem Statement
                  </label>
                  <span className="text-[10px] text-slate-400">
                    Supports math formulas and ```python code blocks
                  </span>
                </div>
                <textarea
                  required
                  rows={4}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Enter problem statement, quadratic equation (e.g. 2x² - 7x + 3 = 0), or Python snippet..."
                  className="w-full px-3 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-[#6A35D8] text-slate-900 dark:text-slate-100 font-mono"
                />
              </div>

              {/* 4 Options with Correct Radio Button */}
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">
                  Answer Options (Select the Radio Button next to the Correct Option)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {options.map((opt, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center gap-2.5 p-2 rounded-xl border transition-all ${
                        correctIdx === idx
                          ? 'border-emerald-500 bg-emerald-50/40 dark:bg-emerald-950/20 ring-1 ring-emerald-500'
                          : 'border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800'
                      }`}
                    >
                      <input
                        type="radio"
                        name="correctOption"
                        id={`opt-${idx}`}
                        checked={correctIdx === idx}
                        onChange={() => setCorrectIdx(idx)}
                        className="w-4 h-4 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                        title="Mark as correct answer"
                      />
                      <span className="text-xs font-bold text-slate-400 w-4">
                        {String.fromCharCode(65 + idx)}.
                      </span>
                      <input
                        type="text"
                        required
                        value={opt}
                        onChange={(e) => handleOptionChange(idx, e.target.value)}
                        placeholder={`Option ${String.fromCharCode(65 + idx)}`}
                        className="w-full text-xs bg-transparent focus:outline-none text-slate-900 dark:text-slate-100"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Error Alert */}
              {error && (
                <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/60 text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-3 px-4 rounded-xl font-bold text-xs text-white bg-[#6A35D8] hover:bg-[#562ab3] shadow-lg shadow-purple-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>AI Tutor Analyzing & Synthesizing 4 Scaffolding Modalities...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>✨ Analyze & Publish Question with AI Tutor</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddQuestionModal;

