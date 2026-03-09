"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";

const STEPS = [
  {
    id: "clone",
    label: "Clone",
    accent: "#3b82f6",
    title: "Reads your entire codebase.",
    description:
      "Clones the repo, indexes every file, maps dependencies and imports. No sampling — the full picture.",
    mockup: [
      { text: "src/ — 142 files", dim: false },
      { text: "tests/ — 38 files", dim: false },
      { text: "package.json — 47 deps", dim: false },
      { text: "12 API routes detected", dim: false },
      { text: "8 env vars found", dim: false },
    ],
  },
  {
    id: "scan",
    label: "Scan",
    accent: "#a855f7",
    title: "Finds what static rules miss.",
    description:
      "Catches injection vectors, hardcoded secrets, deprecated APIs, missing error handling, and risky dependency patterns — with an evidence chain for every finding.",
    mockup: [
      { text: "CRITICAL  SQL injection — auth.py:42", color: "#ef4444" },
      { text: "HIGH      Hardcoded secret — config.js", color: "#f97316" },
      { text: "MEDIUM    Deprecated API — 3 files", color: "#eab308" },
      { text: "Score: 62/100 (D)", color: "#ffffff", bold: true },
    ],
  },
  {
    id: "rewrite",
    label: "Rewrite",
    accent: "#22c55e",
    title: "Patches code. Upgrades deps.",
    description:
      "Rewrites each finding automatically. Knows which files depend on which — never breaks an export used elsewhere. Up to 100 files in parallel.",
    mockup: [
      { text: '- cursor.execute(f"...{uid}")', color: "#ef4444" },
      { text: '+ cursor.execute("...?", (id,))', color: "#22c55e" },
      { text: '- "lodash": "4.17.19"', color: "#ef4444" },
      { text: '+ "lodash": "4.17.21"  # CVE patched', color: "#22c55e" },
    ],
  },
  {
    id: "verify",
    label: "Verify",
    accent: "#f59e0b",
    title: "Runs your tests first.",
    description:
      "Every rewrite goes through a 3-tier check loop in an isolated sandbox. Build fails or test breaks = fix is reattempted automatically. Nothing ships unless green.",
    mockup: [
      { text: "✓  Build — 12s", color: "#22c55e" },
      { text: "✓  Tests (147/147) — 38s", color: "#22c55e" },
      { text: "✓  Lint — 4s", color: "#22c55e" },
      { text: "✓  Blast radius — 0 breaks", color: "#22c55e" },
      { text: "SAFE — ready to ship", color: "#22c55e", bold: true },
    ],
  },
  {
    id: "ship",
    label: "Ship",
    accent: "#06b6d4",
    title: "Opens a PR with full evidence.",
    description:
      "Creates a focused pull request explaining every change — what was found, why it was risky, and proof it compiles and passes tests.",
    mockup: [
      { text: "PR #47: fix 4 security findings", color: "#ffffff", bold: true },
      { text: "✓  SQL injection → parameterized query", color: "#6b7280" },
      { text: "✓  lodash → 4.17.21 (CVE patched)", color: "#6b7280" },
      { text: "+12 −8  3 files changed", color: "#6b7280" },
    ],
  },
];

export default function PipelineStrip() {
  const [activeIdx, setActiveIdx] = useState(0);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: false, margin: "-20%" });
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const displayIdx = hoveredIdx !== null ? hoveredIdx : activeIdx;

  // Auto-advance every 4s when in view and not hovered
  useEffect(() => {
    if (isInView && hoveredIdx === null) {
      intervalRef.current = setInterval(() => {
        setActiveIdx((prev) => (prev + 1) % STEPS.length);
      }, 4000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isInView, hoveredIdx]);

  // Sequentially light up on first view
  useEffect(() => {
    if (isInView) {
      setActiveIdx(0);
      let i = 0;
      const seq = setInterval(() => {
        i++;
        if (i >= STEPS.length) {
          clearInterval(seq);
          return;
        }
        setActiveIdx(i);
      }, 600);
      return () => clearInterval(seq);
    }
  }, [isInView]);

  const step = STEPS[displayIdx];

  return (
    <div ref={ref}>
      {/* Pipeline nodes */}
      <div className="flex items-center justify-center gap-0 mb-12">
        {STEPS.map((s, i) => {
          const isActive = i <= displayIdx;
          return (
            <div key={s.id} className="flex items-center">
              <button
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => setHoveredIdx(null)}
                onClick={() => { setActiveIdx(i); setHoveredIdx(null); }}
                className="flex flex-col items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300 hover:bg-white/[0.03]"
              >
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold transition-all duration-500 border"
                  style={{
                    borderColor: isActive ? s.accent : "#1f2937",
                    background: isActive ? `${s.accent}15` : "transparent",
                    color: isActive ? s.accent : "#4b5563",
                    boxShadow: isActive ? `0 0 20px ${s.accent}20` : "none",
                  }}
                >
                  {String(i + 1).padStart(2, "0")}
                </div>
                <span
                  className="text-[11px] font-semibold tracking-widest uppercase transition-colors duration-300"
                  style={{ color: isActive ? "#ffffff" : "#4b5563" }}
                >
                  {s.label}
                </span>
              </button>
              {i < STEPS.length - 1 && (
                <div className="w-12 h-px mx-1" style={{
                  background: i < displayIdx
                    ? `linear-gradient(to right, ${STEPS[i].accent}60, ${STEPS[i + 1].accent}60)`
                    : "#1f2937",
                  transition: "background 0.5s",
                }} />
              )}
            </div>
          );
        })}
      </div>

      {/* Active step detail */}
      <motion.div
        key={step.id}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-start max-w-5xl mx-auto"
      >
        <div>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-[11px] font-mono tracking-widest" style={{ color: step.accent }}>
              {String(displayIdx + 1).padStart(2, "0")}
            </span>
            <div className="h-px w-6" style={{ background: `${step.accent}40` }} />
            <span className="text-[10px] font-semibold tracking-widest uppercase" style={{ color: `${step.accent}99` }}>
              {step.label}
            </span>
          </div>
          <h3 className="text-2xl lg:text-3xl font-bold mb-4 tracking-tight text-white leading-tight">
            {step.title}
          </h3>
          <p className="text-gray-400 text-[15px] leading-relaxed max-w-md">
            {step.description}
          </p>
        </div>

        {/* Code mockup */}
        <div
          className="rounded-xl border p-5 font-mono text-sm"
          style={{
            background: `${step.accent}05`,
            borderColor: `${step.accent}15`,
          }}
        >
          <div className="flex items-center gap-2 mb-4 text-gray-600 text-xs">
            <div className="flex gap-1.5">
              <div className="w-2 h-2 rounded-full bg-[#ff5f57]/50" />
              <div className="w-2 h-2 rounded-full bg-[#ffbd2e]/50" />
              <div className="w-2 h-2 rounded-full bg-[#28c840]/50" />
            </div>
            <span className="ml-1">{step.id}</span>
          </div>
          <div className="space-y-1.5">
            {step.mockup.map((line, i) => (
              <div
                key={i}
                className={`text-xs ${(line as { bold?: boolean }).bold ? "font-semibold" : ""}`}
                style={{ color: (line as { color?: string }).color || "#9ca3af" }}
              >
                {line.text}
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
