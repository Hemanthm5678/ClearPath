import React from "react";
import { Layers, ArrowRight, Check } from "lucide-react";

interface VisualDiagramProps {
  questionId?: string;
  conceptId?: string;
}

export const VisualDiagram: React.FC<VisualDiagramProps> = ({ questionId = "q3_division_1" }) => {
  // Render tailored pedagogical SVGs based on the active question
  switch (questionId) {
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

