import React from "react";
import { Layers, ArrowRight, Check } from "lucide-react";

interface VisualDiagramProps {
  questionId?: string;
  conceptId?: string;
}

export const VisualDiagram: React.FC<VisualDiagramProps> = ({ questionId = "q_quad_roots_top", conceptId }) => {
  // Render tailored pedagogical SVGs based on the active question
  switch (questionId) {
    case "q_quad_roots_top":
      // Solve 2x² - 9x + 4 = 0 -> x = 4, x = 1/2
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Parabola Roots & Factor Breakdown: 2x² - 9x + 4 = 0
            </span>
            <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
              Roots: x = 1/2, x = 4
            </span>
          </div>

          <svg viewBox="0 0 420 160" className="w-full h-auto max-h-44 mx-auto">
            {/* Coordinate Grid */}
            <line x1="30" y1="95" x2="390" y2="95" stroke="#94a3b8" strokeWidth="1.5" />
            <line x1="80" y1="20" x2="80" y2="150" stroke="#94a3b8" strokeWidth="1.5" />
            <text x="385" y="90" fill="#64748b" fontSize="10" fontWeight="bold">x</text>
            <text x="75" y="25" fill="#64748b" fontSize="10" fontWeight="bold" textAnchor="end">y</text>

            {/* Parabola Curve y = 2x^2 - 9x + 4 */}
            <path
              d="M 50 30 Q 215 220 370 30"
              fill="none"
              stroke="#6A35D8"
              strokeWidth="2.5"
            />

            {/* Root Points on Axis */}
            <circle cx="115" cy="95" r="5" fill="#F25C1E" stroke="#ffffff" strokeWidth="1.5" />
            <text x="115" y="82" fill="#F25C1E" fontSize="11" fontWeight="bold" textAnchor="middle">x = 1/2 (0.5)</text>

            <circle cx="320" cy="95" r="5" fill="#F25C1E" stroke="#ffffff" strokeWidth="1.5" />
            <text x="320" y="82" fill="#F25C1E" fontSize="11" fontWeight="bold" textAnchor="middle">x = 4</text>

            {/* Factoring equation box */}
            <rect x="50" y="115" width="320" height="36" rx="6" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1" />
            <text x="210" y="130" fill="#334155" fontSize="11" fontWeight="bold" textAnchor="middle">
              Factoring: (2x - 1)(x - 4) = 0
            </text>
            <text x="210" y="144" fill="#6A35D8" fontSize="10" fontWeight="semibold" textAnchor="middle">
              Setting each factor to 0 → 2x - 1 = 0 (x = 1/2) & x - 4 = 0 (x = 4)
            </text>
          </svg>
        </div>
      );

    case "q_code_mutable_top":
      // def add_item(val, box=[]): box.append(val); return box
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Python Memory Reference Trace: box=[] Default Argument
            </span>
            <span className="text-[10px] font-mono bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full font-bold">
              Output: [10, 20]
            </span>
          </div>

          <svg viewBox="0 0 420 155" className="w-full h-auto max-h-44 mx-auto">
            {/* Function Definition / Scope Box */}
            <rect x="15" y="15" width="165" height="125" rx="8" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="1.5" />
            <text x="25" y="35" fill="#6A35D8" fontSize="11" fontWeight="bold">def add_item(val, box=[]):</text>
            
            <rect x="25" y="48" width="145" height="32" rx="4" fill="#ede9fe" stroke="#c4b5fd" strokeWidth="1" />
            <text x="32" y="68" fill="#4c1d95" fontSize="10" fontWeight="bold">Call 1: add_item(10)</text>

            <rect x="25" y="90" width="145" height="32" rx="4" fill="#ffedd5" stroke="#fed7aa" strokeWidth="1" />
            <text x="32" y="110" fill="#9a3412" fontSize="10" fontWeight="bold">Call 2: add_item(20)</text>

            {/* Arrow from Call 1 & 2 pointing to the same Heap Object */}
            <line x1="170" y1="64" x2="230" y2="78" stroke="#6A35D8" strokeWidth="2" strokeDasharray="3,2" />
            <line x1="170" y1="106" x2="230" y2="86" stroke="#F25C1E" strokeWidth="2" strokeDasharray="3,2" />

            {/* Heap Memory Box (Single Shared Object) */}
            <rect x="235" y="35" width="170" height="90" rx="8" fill="#ffffff" stroke="#6A35D8" strokeWidth="2" />
            <text x="320" y="55" fill="#6A35D8" fontSize="11" fontWeight="extrabold" textAnchor="middle">Shared Heap Object</text>
            <text x="320" y="70" fill="#64748b" fontSize="9" textAnchor="middle">id: 0x7f8a (reused across calls)</text>

            {/* List representation */}
            <rect x="250" y="80" width="60" height="32" rx="4" fill="#6A35D8" />
            <text x="280" y="101" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle">[10,</text>

            <rect x="315" y="80" width="60" height="32" rx="4" fill="#F25C1E" />
            <text x="345" y="101" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle">20]</text>

            {/* Callout beneath */}
            <text x="210" y="145" fill="#e11d48" fontSize="9.5" fontWeight="bold" textAnchor="middle">
              ⚠ Default argument box=[] is instantiated ONCE. Both calls mutate the SAME list!
            </text>
          </svg>
        </div>
      );

    case "q_quad_param_top":
      // x² - kx + 25 = 0 single repeated root -> k = 10, root x = 5
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Discriminant Zero Condition: x² - kx + 25 = 0
            </span>
            <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
              k = 10, Root: x = 5
            </span>
          </div>

          <svg viewBox="0 0 420 155" className="w-full h-auto max-h-44 mx-auto">
            {/* Coordinate Axis */}
            <line x1="30" y1="105" x2="390" y2="105" stroke="#94a3b8" strokeWidth="1.5" />
            <line x1="70" y1="20" x2="70" y2="145" stroke="#94a3b8" strokeWidth="1.5" />

            {/* Parabola Tangent to x-axis at x=5 */}
            <path
              d="M 120 25 Q 230 185 340 25"
              fill="none"
              stroke="#6A35D8"
              strokeWidth="2.5"
            />

            {/* Tangent point on x-axis */}
            <circle cx="230" cy="105" r="6" fill="#10b981" stroke="#ffffff" strokeWidth="2" />
            <text x="230" y="125" fill="#10b981" fontSize="11" fontWeight="extrabold" textAnchor="middle">
              Tangent Point: (5, 0)
            </text>

            {/* Discriminant Equation Box */}
            <rect x="50" y="25" width="140" height="55" rx="6" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1" />
            <text x="120" y="42" fill="#6A35D8" fontSize="10.5" fontWeight="bold" textAnchor="middle">Δ = b² - 4ac = 0</text>
            <text x="120" y="58" fill="#334155" fontSize="10" textAnchor="middle">k² - 4(1)(25) = 0</text>
            <text x="120" y="73" fill="#F25C1E" fontSize="10.5" fontWeight="bold" textAnchor="middle">k² = 100 → k = 10</text>

            {/* Root summary */}
            <text x="290" y="55" fill="#6A35D8" fontSize="11" fontWeight="bold" textAnchor="middle">
              (x - 5)² = 0
            </text>
            <text x="290" y="72" fill="#334155" fontSize="10" textAnchor="middle">
              Double root at x = 5
            </text>
          </svg>
        </div>
      );

    case "q_code_recursion_top":
      // def compute(n): if n<=1: return 1; return n * compute(n - 2)
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Recursion Call Stack & Value Unwinding: compute(5)
            </span>
            <span className="text-[10px] font-mono bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full font-bold">
              Output: 15
            </span>
          </div>

          <svg viewBox="0 0 420 155" className="w-full h-auto max-h-44 mx-auto">
            {/* Call 1: compute(5) */}
            <rect x="30" y="20" width="160" height="32" rx="6" fill="#ede9fe" stroke="#8b5cf6" strokeWidth="1.5" />
            <text x="110" y="40" fill="#5b21b6" fontSize="11" fontWeight="bold" textAnchor="middle">
              compute(5) = 5 * compute(3)
            </text>

            {/* Call 2: compute(3) */}
            <rect x="50" y="60" width="160" height="32" rx="6" fill="#ddd6fe" stroke="#7c3aed" strokeWidth="1.5" />
            <text x="130" y="80" fill="#4c1d95" fontSize="11" fontWeight="bold" textAnchor="middle">
              compute(3) = 3 * compute(1)
            </text>

            {/* Call 3: compute(1) Base Case */}
            <rect x="70" y="100" width="160" height="32" rx="6" fill="#bbf7d0" stroke="#16a34a" strokeWidth="1.5" />
            <text x="150" y="120" fill="#14532d" fontSize="11" fontWeight="extrabold" textAnchor="middle">
              compute(1) = 1 (Base Case)
            </text>

            {/* Upward Unwinding Box */}
            <rect x="250" y="25" width="150" height="100" rx="8" fill="#ffffff" stroke="#F25C1E" strokeWidth="1.5" />
            <text x="325" y="48" fill="#F25C1E" fontSize="11" fontWeight="bold" textAnchor="middle">Unwinding Multiply:</text>
            <text x="325" y="70" fill="#334155" fontSize="11" textAnchor="middle">compute(1) = 1</text>
            <text x="325" y="90" fill="#334155" fontSize="11" textAnchor="middle">compute(3) = 3 × 1 = 3</text>
            <text x="325" y="112" fill="#6A35D8" fontSize="12" fontWeight="extrabold" textAnchor="middle">5 × 3 = 15</text>
          </svg>
        </div>
      );

    case "q_math_slope_intercept":
      // 3x + 2y = 8 -> y = -1.5x + 4
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Linear Equation Form: 3x + 2y = 8 → y = (-3/2)x + 4
            </span>
            <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
              m = -3/2, b = 4
            </span>
          </div>

          <svg viewBox="0 0 420 155" className="w-full h-auto max-h-44 mx-auto">
            {/* Coordinate Grid */}
            <line x1="40" y1="120" x2="380" y2="120" stroke="#94a3b8" strokeWidth="1.5" />
            <line x1="120" y1="15" x2="120" y2="145" stroke="#94a3b8" strokeWidth="1.5" />
            <text x="375" y="115" fill="#64748b" fontSize="10" fontWeight="bold">x</text>
            <text x="115" y="25" fill="#64748b" fontSize="10" fontWeight="bold" textAnchor="end">y</text>

            {/* Line with slope -1.5 through (0, 4) */}
            <line x1="60" y1="30" x2="260" y2="150" stroke="#6A35D8" strokeWidth="2.5" />

            {/* Y-intercept (0, 4) at x=120, y=55 */}
            <circle cx="120" cy="65" r="5" fill="#F25C1E" stroke="#ffffff" strokeWidth="1.5" />
            <text x="135" y="65" fill="#F25C1E" fontSize="10.5" fontWeight="bold">y-intercept (0, 4)</text>

            {/* Slope triangle */}
            <line x1="120" y1="65" x2="120" y2="105" stroke="#64748b" strokeWidth="1.5" strokeDasharray="3,2" />
            <line x1="120" y1="105" x2="175" y2="105" stroke="#64748b" strokeWidth="1.5" strokeDasharray="3,2" />
            <text x="100" y="88" fill="#64748b" fontSize="9.5" fontWeight="bold" textAnchor="end">Δy = -3</text>
            <text x="148" y="118" fill="#64748b" fontSize="9.5" fontWeight="bold" textAnchor="middle">Δx = +2</text>

            {/* Summary card */}
            <rect x="250" y="25" width="150" height="65" rx="6" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1" />
            <text x="325" y="45" fill="#6A35D8" fontSize="11" fontWeight="bold" textAnchor="middle">Standard Form y = mx + b</text>
            <text x="325" y="62" fill="#F25C1E" fontSize="10.5" fontWeight="bold" textAnchor="middle">Slope m = -3/2</text>
            <text x="325" y="78" fill="#334155" fontSize="10" textAnchor="middle">y-intercept b = 4</text>
          </svg>
        </div>
      );

    case "q1_basics_1":
      // In 3/5, what does 5 represent? (5 total equal parts)
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: Understanding Fraction 3/5
            </span>
            <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
              Tape Diagram
            </span>
          </div>

          <svg viewBox="0 0 400 120" className="w-full h-auto max-h-36 mx-auto">
            {/* Whole container box */}
            <rect x="20" y="25" width="360" height="45" rx="6" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="2" />
            {/* 3 shaded parts */}
            <rect x="20" y="25" width="72" height="45" rx="4" fill="#6A35D8" />
            <rect x="92" y="25" width="72" height="45" rx="4" fill="#6A35D8" />
            <rect x="164" y="25" width="72" height="45" rx="4" fill="#6A35D8" />
            
            {/* Partition dividers */}
            <line x1="92" y1="25" x2="92" y2="70" stroke="#ffffff" strokeWidth="2" strokeDasharray="3,2" />
            <line x1="164" y1="25" x2="164" y2="70" stroke="#ffffff" strokeWidth="2" strokeDasharray="3,2" />
            <line x1="236" y1="25" x2="236" y2="70" stroke="#64748b" strokeWidth="2" />
            <line x1="308" y1="25" x2="308" y2="70" stroke="#64748b" strokeWidth="2" />

            {/* Labels on segments */}
            <text x="56" y="52" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle">1/5</text>
            <text x="128" y="52" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle">1/5</text>
            <text x="200" y="52" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle">1/5</text>
            <text x="272" y="52" fill="#64748b" fontSize="12" fontWeight="bold" textAnchor="middle">1/5</text>
            <text x="344" y="52" fill="#64748b" fontSize="12" fontWeight="bold" textAnchor="middle">1/5</text>

            {/* Top bracket: Numerator (3) */}
            <path d="M 20 18 Q 128 10 236 18" fill="none" stroke="#6A35D8" strokeWidth="2" />
            <text x="128" y="10" fill="#6A35D8" fontSize="11" fontWeight="bold" textAnchor="middle">
              Numerator: 3 parts counted
            </text>

            {/* Bottom bracket: Denominator (5) */}
            <path d="M 20 78 Q 200 92 380 78" fill="none" stroke="#F25C1E" strokeWidth="2" />
            <text x="200" y="104" fill="#F25C1E" fontSize="11" fontWeight="bold" textAnchor="middle">
              Denominator = 5 total equal parts that make the complete whole
            </text>
          </svg>
        </div>
      );

    case "q2_basics_2":
      // Chocolate bar broken into 8 pieces, 3 eaten, fraction remaining (5/8)
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: Chocolate Bar Subtraction (8 - 3 = 5)
            </span>
            <span className="text-[10px] font-mono bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full font-bold">
              5/8 Remaining
            </span>
          </div>

          <svg viewBox="0 0 400 110" className="w-full h-auto max-h-36 mx-auto">
            {/* 8-piece chocolate grid: 4 columns x 2 rows */}
            {/* Top row */}
            <rect x="30" y="15" width="80" height="35" rx="4" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="1.5" />
            <text x="70" y="37" fill="#64748b" fontSize="11" fontWeight="bold" textAnchor="middle">✕ Eaten</text>

            <rect x="115" y="15" width="80" height="35" rx="4" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="1.5" />
            <text x="155" y="37" fill="#64748b" fontSize="11" fontWeight="bold" textAnchor="middle">✕ Eaten</text>

            <rect x="200" y="15" width="80" height="35" rx="4" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="1.5" />
            <text x="240" y="37" fill="#64748b" fontSize="11" fontWeight="bold" textAnchor="middle">✕ Eaten</text>

            <rect x="285" y="15" width="80" height="35" rx="4" fill="#78350f" stroke="#451a03" strokeWidth="1.5" />
            <text x="325" y="37" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">✓ Kept</text>

            {/* Bottom row (all 4 remaining) */}
            <rect x="30" y="55" width="80" height="35" rx="4" fill="#78350f" stroke="#451a03" strokeWidth="1.5" />
            <text x="70" y="77" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">✓ Kept</text>

            <rect x="115" y="55" width="80" height="35" rx="4" fill="#78350f" stroke="#451a03" strokeWidth="1.5" />
            <text x="155" y="77" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">✓ Kept</text>

            <rect x="200" y="55" width="80" height="35" rx="4" fill="#78350f" stroke="#451a03" strokeWidth="1.5" />
            <text x="240" y="77" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">✓ Kept</text>

            <rect x="285" y="55" width="80" height="35" rx="4" fill="#78350f" stroke="#451a03" strokeWidth="1.5" />
            <text x="325" y="77" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">✓ Kept</text>

            {/* Summary */}
            <text x="200" y="104" fill="#6A35D8" fontSize="11" fontWeight="bold" textAnchor="middle">
              8 Total Pieces - 3 Eaten = 5 Remaining → Fraction: 5/8
            </text>
          </svg>
        </div>
      );

    case "q_equal_parts_1":
      // 4 equal quadrants vs unequal partition
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Equal Partitioning: All 4 Sections Must Be Equal Size
            </span>
            <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
              Strictly Equal Area
            </span>
          </div>

          <svg viewBox="0 0 400 120" className="w-full h-auto max-h-36 mx-auto">
            {/* Square 1: True Fourths (Equal) */}
            <rect x="50" y="15" width="80" height="80" rx="4" fill="#f8fafc" stroke="#6A35D8" strokeWidth="2" />
            <line x1="90" y1="15" x2="90" y2="95" stroke="#6A35D8" strokeWidth="1.5" />
            <line x1="50" y1="55" x2="130" y2="55" stroke="#6A35D8" strokeWidth="1.5" />
            <rect x="50" y="15" width="40" height="40" rx="2" fill="#6A35D8" opacity="0.3" />
            <text x="70" y="38" fill="#6A35D8" fontSize="11" fontWeight="bold" textAnchor="middle">1/4</text>
            <text x="90" y="112" fill="#16a34a" fontSize="10.5" fontWeight="bold" textAnchor="middle">✓ True Fourths (Equal)</text>

            {/* Square 2: Unequal Partitions (NOT Fourths) */}
            <rect x="230" y="15" width="80" height="80" rx="4" fill="#f8fafc" stroke="#e11d48" strokeWidth="2" />
            <line x1="250" y1="15" x2="250" y2="95" stroke="#e11d48" strokeWidth="1.5" />
            <line x1="230" y1="75" x2="310" y2="75" stroke="#e11d48" strokeWidth="1.5" />
            <rect x="230" y="15" width="20" height="60" rx="2" fill="#e11d48" opacity="0.3" />
            <text x="240" y="50" fill="#e11d48" fontSize="9" fontWeight="bold" textAnchor="middle">?</text>
            <text x="270" y="112" fill="#e11d48" fontSize="10.5" fontWeight="bold" textAnchor="middle">✕ NOT Fourths (Unequal)</text>
          </svg>
        </div>
      );

    case "q_equal_parts_2":
      // Uneven 50cm, 25cm, 25cm bar -> Piece A is 1/2, not 1/3
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Unequal Partition Bar: 50cm² + 25cm² + 25cm²
            </span>
            <span className="text-[10px] font-mono bg-rose-100 dark:bg-rose-900/60 text-rose-700 dark:text-rose-300 px-2 py-0.5 rounded-full font-bold">
              Piece A = 1/2, NOT 1/3
            </span>
          </div>

          <svg viewBox="0 0 400 125" className="w-full h-auto max-h-36 mx-auto">
            {/* 100cm total bar */}
            <rect x="30" y="25" width="340" height="45" rx="6" fill="#f1f5f9" stroke="#94a3b8" strokeWidth="2" />
            
            {/* Piece A (50%) */}
            <rect x="30" y="25" width="170" height="45" rx="4" fill="#F25C1E" />
            <text x="115" y="47" fill="#ffffff" fontSize="12" fontWeight="bold" textAnchor="middle">Piece A (50cm²)</text>
            <text x="115" y="62" fill="#fed7aa" fontSize="10" textAnchor="middle">50/100 = 1/2 of bar!</text>

            {/* Piece B (25%) */}
            <rect x="200" y="25" width="85" height="45" fill="#6A35D8" />
            <text x="242" y="52" fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">Piece B (25cm²)</text>

            {/* Piece C (25%) */}
            <rect x="285" y="25" width="85" height="45" rx="4" fill="#8b5cf6" />
            <text x="327" y="52" fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">Piece C (25cm²)</text>

            {/* Conclusion */}
            <text x="200" y="98" fill="#e11d48" fontSize="11" fontWeight="bold" textAnchor="middle">
              Piece A is HALF the whole bar, so it cannot represent 1/3!
            </text>
            <text x="200" y="115" fill="#64748b" fontSize="10" textAnchor="middle">
              To be 1/3, each of the 3 pieces would have to be exactly 33.3cm².
            </text>
          </svg>
        </div>
      );

    case "q3_division_1":
      // 3 personal pizzas shared equally among 4 friends (3/4 each)
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: 3 Pizzas ÷ 4 Friends = 3/4 Each
            </span>
            <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
              Equal Sharing
            </span>
          </div>

          <svg viewBox="0 0 400 125" className="w-full h-auto max-h-36 mx-auto">
            {/* 3 pizzas side-by-side */}
            {/* Pizza 1 */}
            <g transform="translate(60, 45)">
              <circle cx="0" cy="0" r="32" fill="#fed7aa" stroke="#ea580c" strokeWidth="2.5" />
              <line x1="-32" y1="0" x2="32" y2="0" stroke="#ea580c" strokeWidth="1.5" strokeDasharray="3,2" />
              <line x1="0" y1="-32" x2="0" y2="32" stroke="#ea580c" strokeWidth="1.5" strokeDasharray="3,2" />
              {/* Highlight top-left slice */}
              <path d="M 0 0 L -32 0 A 32 32 0 0 1 0 -32 Z" fill="#6A35D8" opacity="0.85" />
              <text x="0" y="44" fill="#334155" fontSize="10" fontWeight="bold" textAnchor="middle">Pizza 1</text>
            </g>

            {/* Pizza 2 */}
            <g transform="translate(160, 45)">
              <circle cx="0" cy="0" r="32" fill="#fed7aa" stroke="#ea580c" strokeWidth="2.5" />
              <line x1="-32" y1="0" x2="32" y2="0" stroke="#ea580c" strokeWidth="1.5" strokeDasharray="3,2" />
              <line x1="0" y1="-32" x2="0" y2="32" stroke="#ea580c" strokeWidth="1.5" strokeDasharray="3,2" />
              {/* Highlight top-left slice */}
              <path d="M 0 0 L -32 0 A 32 32 0 0 1 0 -32 Z" fill="#6A35D8" opacity="0.85" />
              <text x="0" y="44" fill="#334155" fontSize="10" fontWeight="bold" textAnchor="middle">Pizza 2</text>
            </g>

            {/* Pizza 3 */}
            <g transform="translate(260, 45)">
              <circle cx="0" cy="0" r="32" fill="#fed7aa" stroke="#ea580c" strokeWidth="2.5" />
              <line x1="-32" y1="0" x2="32" y2="0" stroke="#ea580c" strokeWidth="1.5" strokeDasharray="3,2" />
              <line x1="0" y1="-32" x2="0" y2="32" stroke="#ea580c" strokeWidth="1.5" strokeDasharray="3,2" />
              {/* Highlight top-left slice */}
              <path d="M 0 0 L -32 0 A 32 32 0 0 1 0 -32 Z" fill="#6A35D8" opacity="0.85" />
              <text x="0" y="44" fill="#334155" fontSize="10" fontWeight="bold" textAnchor="middle">Pizza 3</text>
            </g>

            {/* Result callout on right */}
            <g transform="translate(350, 45)">
              <rect x="-35" y="-30" width="70" height="60" rx="8" fill="#6A35D8" />
              <text x="0" y="-8" fill="#ffffff" fontSize="16" fontWeight="extrabold" textAnchor="middle">3/4</text>
              <text x="0" y="10" fill="#fed7aa" fontSize="9" fontWeight="bold" textAnchor="middle">of a pizza</text>
              <text x="0" y="22" fill="#ffffff" fontSize="8" textAnchor="middle">per friend</text>
            </g>

            <text x="200" y="115" fill="#6A35D8" fontSize="11" fontWeight="bold" textAnchor="middle">
              Cut each pizza into 4 quarters (12 quarters) ÷ 4 friends = 3 quarters (3/4) each!
            </text>
          </svg>
        </div>
      );

    case "q4_division_2":
      // Fraction 7/10 represents division 7 ÷ 10
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: Fraction Bar is Division (a/b = a ÷ b)
            </span>
            <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
              7/10 = 7 ÷ 10
            </span>
          </div>

          <svg viewBox="0 0 400 120" className="w-full h-auto max-h-36 mx-auto">
            {/* Transformation formula */}
            <g transform="translate(90, 55)">
              <text x="0" y="-12" fill="#6A35D8" fontSize="24" fontWeight="extrabold" textAnchor="middle">7</text>
              <line x1="-22" y1="-4" x2="22" y2="-4" stroke="#F25C1E" strokeWidth="3" />
              <text x="0" y="24" fill="#334155" fontSize="24" fontWeight="extrabold" textAnchor="middle">10</text>
              <text x="0" y="44" fill="#64748b" fontSize="10" textAnchor="middle">Fraction</text>
            </g>

            {/* Transform Arrow */}
            <g transform="translate(180, 55)">
              <text x="0" y="-8" fill="#F25C1E" fontSize="10" fontWeight="bold" textAnchor="middle">The line means</text>
              <text x="0" y="6" fill="#F25C1E" fontSize="12" fontWeight="extrabold" textAnchor="middle">"DIVIDE BY"</text>
              <path d="M -20 18 L 20 18 M 12 12 L 20 18 L 12 24" fill="none" stroke="#6A35D8" strokeWidth="2.5" />
            </g>

            {/* Division Result */}
            <g transform="translate(300, 55)">
              <rect x="-65" y="-35" width="130" height="70" rx="10" fill="#6A35D8" />
              <text x="0" y="6" fill="#ffffff" fontSize="22" fontWeight="extrabold" textAnchor="middle">7 ÷ 10</text>
              <text x="0" y="24" fill="#fed7aa" fontSize="10" fontWeight="bold" textAnchor="middle">Top ÷ Bottom</text>
            </g>

            <text x="200" y="112" fill="#334155" fontSize="11" fontWeight="bold" textAnchor="middle">
              Always read from top to bottom: Numerator (7) divided by Denominator (10)
            </text>
          </svg>
        </div>
      );

    case "q5_division_3":
      // 5 liters of juice poured equally into 2 pitchers = 5/2 = 2.5 L each
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: 5 Liters ÷ 2 Pitchers = 5/2 Liters (2.5 L)
            </span>
            <span className="text-[10px] font-mono bg-orange-100 dark:bg-orange-900/60 text-orange-700 dark:text-orange-300 px-2 py-0.5 rounded-full font-bold">
              Improper Fraction
            </span>
          </div>

          <svg viewBox="0 0 400 120" className="w-full h-auto max-h-36 mx-auto">
            {/* 5 juice bottles on left */}
            <g transform="translate(40, 20)">
              {[0, 22, 44, 66, 88].map((x, i) => (
                <g key={i} transform={`translate(${x}, 0)`}>
                  <rect x="0" y="10" width="16" height="35" rx="3" fill="#fed7aa" stroke="#ea580c" strokeWidth="1.5" />
                  <rect x="4" y="2" width="8" height="8" rx="1" fill="#ea580c" />
                  <text x="8" y="32" fill="#c2410c" fontSize="8" fontWeight="bold" textAnchor="middle">1L</text>
                </g>
              ))}
              <text x="52" y="60" fill="#334155" fontSize="10" fontWeight="bold" textAnchor="middle">5 Liters Total</text>
            </g>

            {/* Arrow */}
            <path d="M 165 40 L 205 40 M 195 34 L 205 40 L 195 46" fill="none" stroke="#6A35D8" strokeWidth="2.5" />
            <text x="185" y="28" fill="#6A35D8" fontSize="10" fontWeight="bold" textAnchor="middle">÷ 2</text>

            {/* 2 Pitchers on right */}
            <g transform="translate(240, 15)">
              {/* Pitcher 1 */}
              <rect x="0" y="5" width="45" height="50" rx="4" fill="#ffffff" stroke="#3b82f6" strokeWidth="2" />
              <rect x="2" y="25" width="41" height="28" fill="#fdba74" opacity="0.9" />
              <text x="22" y="42" fill="#9a3412" fontSize="9" fontWeight="bold" textAnchor="middle">2.5 L</text>
              <text x="22" y="68" fill="#334155" fontSize="9" fontWeight="bold" textAnchor="middle">Pitcher 1</text>

              {/* Pitcher 2 */}
              <rect x="65" y="5" width="45" height="50" rx="4" fill="#ffffff" stroke="#3b82f6" strokeWidth="2" />
              <rect x="67" y="25" width="41" height="28" fill="#fdba74" opacity="0.9" />
              <text x="87" y="42" fill="#9a3412" fontSize="9" fontWeight="bold" textAnchor="middle">2.5 L</text>
              <text x="87" y="68" fill="#334155" fontSize="9" fontWeight="bold" textAnchor="middle">Pitcher 2</text>
            </g>

            <text x="200" y="112" fill="#6A35D8" fontSize="11" fontWeight="bold" textAnchor="middle">
              5 ÷ 2 = 5/2 liters = 2 1/2 liters in each pitcher
            </text>
          </svg>
        </div>
      );

    case "q6_equiv_1":
      // Equivalent fractions: 1/2 = 2/4
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: 1/2 is Identical to 2/4 in Size
            </span>
            <span className="text-[10px] font-mono bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full font-bold">
              1/2 = 2/4
            </span>
          </div>

          <svg viewBox="0 0 400 115" className="w-full h-auto max-h-36 mx-auto">
            {/* Top Bar: 1/2 */}
            <text x="25" y="32" fill="#6A35D8" fontSize="12" fontWeight="bold" textAnchor="end">1/2:</text>
            <rect x="35" y="15" width="330" height="26" rx="4" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="1.5" />
            <rect x="35" y="15" width="165" height="26" rx="4" fill="#6A35D8" />
            <text x="117" y="32" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">1/2 Shaded</text>

            {/* Bottom Bar: 2/4 */}
            <text x="25" y="72" fill="#F25C1E" fontSize="12" fontWeight="bold" textAnchor="end">2/4:</text>
            <rect x="35" y="55" width="330" height="26" rx="4" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="1.5" />
            <rect x="35" y="55" width="82.5" height="26" rx="4" fill="#F25C1E" />
            <rect x="117.5" y="55" width="82.5" height="26" rx="4" fill="#F25C1E" />
            <line x1="117.5" y1="55" x2="117.5" y2="81" stroke="#ffffff" strokeWidth="2" strokeDasharray="2,2" />
            <text x="76" y="72" fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">1/4</text>
            <text x="158" y="72" fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">1/4</text>

            {/* Alignment line */}
            <line x1="200" y1="10" x2="200" y2="88" stroke="#10b981" strokeWidth="2.5" strokeDasharray="3,3" />

            <text x="200" y="105" fill="#10b981" fontSize="11" fontWeight="bold" textAnchor="middle">
              Both bars cover exactly 50% of the whole area → 1/2 = 2/4
            </text>
          </svg>
        </div>
      );

    case "q7_equiv_2":
      // Missing number in 3/4 = ?/12 (multiply top & bottom by 3 -> 9)
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: Scaling Multiplier Rule (×3 / ×3)
            </span>
            <span className="text-[10px] font-mono bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full font-bold">
              3/4 = 9/12
            </span>
          </div>

          <svg viewBox="0 0 400 115" className="w-full h-auto max-h-36 mx-auto">
            {/* Left fraction: 3/4 */}
            <g transform="translate(100, 55)">
              <text x="0" y="-14" fill="#6A35D8" fontSize="24" fontWeight="extrabold" textAnchor="middle">3</text>
              <line x1="-22" y1="-4" x2="22" y2="-4" stroke="#6A35D8" strokeWidth="3" />
              <text x="0" y="24" fill="#6A35D8" fontSize="24" fontWeight="extrabold" textAnchor="middle">4</text>
            </g>

            {/* Equals and Multiplier Arrows */}
            <text x="180" y="62" fill="#334155" fontSize="24" fontWeight="bold" textAnchor="middle">=</text>

            <path d="M 125 35 Q 180 18 235 35" fill="none" stroke="#F25C1E" strokeWidth="2" />
            <text x="180" y="20" fill="#F25C1E" fontSize="11" fontWeight="extrabold" textAnchor="middle">× 3</text>

            <path d="M 125 75 Q 180 92 235 75" fill="none" stroke="#F25C1E" strokeWidth="2" />
            <text x="180" y="104" fill="#F25C1E" fontSize="11" fontWeight="extrabold" textAnchor="middle">× 3 (4 × 3 = 12)</text>

            {/* Right fraction: 9/12 */}
            <g transform="translate(260, 55)">
              <rect x="-24" y="-35" width="48" height="30" rx="6" fill="#10b981" />
              <text x="0" y="-14" fill="#ffffff" fontSize="22" fontWeight="extrabold" textAnchor="middle">9</text>
              <line x1="-22" y1="-4" x2="22" y2="-4" stroke="#334155" strokeWidth="3" />
              <text x="0" y="24" fill="#334155" fontSize="24" fontWeight="extrabold" textAnchor="middle">12</text>
            </g>
          </svg>
        </div>
      );

    case "q8_compare_1":
      // Compare 2/5 and 3/5
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: Comparing Same Denominators (2/5 &lt; 3/5)
            </span>
            <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
              2/5 &lt; 3/5
            </span>
          </div>

          <svg viewBox="0 0 400 115" className="w-full h-auto max-h-36 mx-auto">
            {/* Bar 1: 2/5 */}
            <text x="25" y="32" fill="#6A35D8" fontSize="12" fontWeight="bold" textAnchor="end">2/5:</text>
            <rect x="35" y="15" width="330" height="26" rx="4" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="1.5" />
            <rect x="35" y="15" width="132" height="26" rx="4" fill="#6A35D8" />
            <text x="101" y="32" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">2 of 5</text>

            {/* Bar 2: 3/5 */}
            <text x="25" y="72" fill="#F25C1E" fontSize="12" fontWeight="bold" textAnchor="end">3/5:</text>
            <rect x="35" y="55" width="330" height="26" rx="4" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="1.5" />
            <rect x="35" y="55" width="198" height="26" rx="4" fill="#F25C1E" />
            <text x="134" y="72" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">3 of 5 (Longer!)</text>

            <text x="200" y="105" fill="#334155" fontSize="11" fontWeight="bold" textAnchor="middle">
              Identical denominator (5) means pieces are same size → 2 pieces is less than 3 pieces
            </text>
          </svg>
        </div>
      );

    case "q9_add_1":
      // 1/6 + 3/6 = 4/6 = 2/3
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Model: Adding Numerators (1/6 + 3/6 = 4/6 → 2/3)
            </span>
            <span className="text-[10px] font-mono bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full font-bold">
              Simplifies to 2/3
            </span>
          </div>

          <svg viewBox="0 0 400 115" className="w-full h-auto max-h-36 mx-auto">
            {/* 6-part segmented strip */}
            <rect x="35" y="20" width="330" height="32" rx="5" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="1.5" />
            
            {/* 1st segment: 1/6 (blue) */}
            <rect x="35" y="20" width="55" height="32" rx="3" fill="#3b82f6" />
            <text x="62.5" y="40" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">1/6</text>

            {/* 2nd, 3rd, 4th segments: + 3/6 (purple) */}
            <rect x="90" y="20" width="165" height="32" fill="#6A35D8" />
            <line x1="145" y1="20" x2="145" y2="52" stroke="#ffffff" strokeWidth="1.5" strokeDasharray="3,2" />
            <line x1="200" y1="20" x2="200" y2="52" stroke="#ffffff" strokeWidth="1.5" strokeDasharray="3,2" />
            <text x="172.5" y="40" fill="#ffffff" fontSize="11" fontWeight="bold" textAnchor="middle">+ 3/6 (3 parts)</text>

            {/* Result bracket */}
            <text x="200" y="76" fill="#6A35D8" fontSize="12" fontWeight="extrabold" textAnchor="middle">
              Total = 4 out of 6 parts = 4/6
            </text>

            <text x="200" y="100" fill="#10b981" fontSize="11" fontWeight="bold" textAnchor="middle">
              Simplifying: Divide numerator & denominator by 2 → 4/6 = 2/3
            </text>
          </svg>
        </div>
      );

    default:
      if (conceptId === "c7_python_tracing" || (questionId && questionId.includes("code"))) {
        return (
          <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" />
                Python Execution Stack & State Diagram
              </span>
              <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
                Trace Model
              </span>
            </div>
            <svg viewBox="0 0 400 110" className="w-full h-auto max-h-36 mx-auto">
              <rect x="30" y="15" width="160" height="80" rx="6" fill="#ffffff" stroke="#6A35D8" strokeWidth="1.5" />
              <text x="110" y="35" fill="#6A35D8" fontSize="11" fontWeight="bold" textAnchor="middle">Stack Frame</text>
              <text x="110" y="55" fill="#64748b" fontSize="10" textAnchor="middle">Local Scope & Variables</text>
              <text x="110" y="75" fill="#334155" fontSize="10" textAnchor="middle">Return Address</text>

              <line x1="190" y1="55" x2="230" y2="55" stroke="#F25C1E" strokeWidth="2" strokeDasharray="3,2" />

              <rect x="230" y="15" width="140" height="80" rx="6" fill="#ffffff" stroke="#F25C1E" strokeWidth="1.5" />
              <text x="300" y="35" fill="#F25C1E" fontSize="11" fontWeight="bold" textAnchor="middle">Heap Memory</text>
              <text x="300" y="55" fill="#64748b" fontSize="10" textAnchor="middle">Persistent Objects</text>
              <text x="300" y="75" fill="#334155" fontSize="10" textAnchor="middle">Mutable References</text>
            </svg>
          </div>
        );
      }

      if (conceptId === "c8_quadratic_algebra" || (questionId && (questionId.includes("quad") || questionId.includes("math")))) {
        return (
          <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" />
                Quadratic & Algebraic Coordinate Model
              </span>
              <span className="text-[10px] font-mono bg-purple-100 dark:bg-purple-900/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-bold">
                Curve Model
              </span>
            </div>
            <svg viewBox="0 0 400 110" className="w-full h-auto max-h-36 mx-auto">
              <line x1="20" y1="65" x2="380" y2="65" stroke="#94a3b8" strokeWidth="1.5" />
              <line x1="200" y1="10" x2="200" y2="100" stroke="#94a3b8" strokeWidth="1.5" />
              <path d="M 80 20 Q 200 120 320 20" fill="none" stroke="#6A35D8" strokeWidth="2" />
              <circle cx="130" cy="65" r="4" fill="#F25C1E" />
              <circle cx="270" cy="65" r="4" fill="#F25C1E" />
              <text x="200" y="100" fill="#6A35D8" fontSize="10" fontWeight="bold" textAnchor="middle">
                Parabola Roots where y = 0
              </text>
            </svg>
          </div>
        );
      }

      // Generic fraction model fallback
      return (
        <div className="bg-purple-50/70 dark:bg-purple-950/30 p-3.5 rounded-xl border border-purple-200 dark:border-purple-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6A35D8] flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Visual Conceptual Representation
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Fractions represent division of a whole into equal parts. The top number counts parts you have, and the bottom number defines the whole.
          </p>
        </div>
      );
  }
};

