"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const LINES = [
  { text: "$ dependify scan acme/payments-api", type: "command" as const, delay: 600 },
  { text: "  Cloning repository...", type: "dim" as const, delay: 800 },
  { text: "  Indexed 142 files, 47 dependencies", type: "dim" as const, delay: 600 },
  { text: "", type: "dim" as const, delay: 300 },
  { text: "  CRITICAL  SQL injection — auth.py:42", type: "critical" as const, delay: 400 },
  { text: "  HIGH      Hardcoded secret — config.js:8", type: "high" as const, delay: 350 },
  { text: "  MEDIUM    Deprecated API — 3 files", type: "medium" as const, delay: 350 },
  { text: "  LOW       Missing error handler — api.py:91", type: "low" as const, delay: 300 },
  { text: "", type: "dim" as const, delay: 200 },
  { text: "  Score: 62/100 (D)", type: "score" as const, delay: 500 },
  { text: "", type: "dim" as const, delay: 300 },
  { text: "  Rewriting 4 files...", type: "dim" as const, delay: 800 },
  { text: "  Sandbox: build OK, 147/147 tests pass", type: "success" as const, delay: 700 },
  { text: "", type: "dim" as const, delay: 200 },
  { text: "  ✓ PR #47 created — fix: patch 4 security findings", type: "success" as const, delay: 0 },
];

const TYPE_COLORS: Record<string, string> = {
  command: "text-white",
  dim: "text-gray-600",
  critical: "text-red-400",
  high: "text-orange-400",
  medium: "text-yellow-400",
  low: "text-blue-400",
  score: "text-white font-semibold",
  success: "text-green-400",
};

export default function TerminalDemo() {
  const [visibleLines, setVisibleLines] = useState<number>(0);
  const [isTyping, setIsTyping] = useState(false);
  const [typedText, setTypedText] = useState("");
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let idx = 0;

    const showNext = () => {
      if (idx >= LINES.length) {
        // Pause then restart
        timeoutRef.current = setTimeout(() => {
          setVisibleLines(0);
          setIsTyping(false);
          setTypedText("");
          idx = 0;
          timeoutRef.current = setTimeout(showNext, 800);
        }, 4000);
        return;
      }

      const line = LINES[idx];

      if (idx === 0) {
        // Type the command character by character
        setIsTyping(true);
        let charIdx = 0;
        const prefix = "$ ";
        const cmd = line.text.slice(2); // remove "$ "

        const typeChar = () => {
          if (charIdx <= cmd.length) {
            setTypedText(prefix + cmd.slice(0, charIdx));
            charIdx++;
            timeoutRef.current = setTimeout(typeChar, 35);
          } else {
            setIsTyping(false);
            setVisibleLines(1);
            idx++;
            timeoutRef.current = setTimeout(showNext, line.delay);
          }
        };
        typeChar();
      } else {
        idx++;
        setVisibleLines(idx);
        timeoutRef.current = setTimeout(showNext, line.delay);
      }
    };

    timeoutRef.current = setTimeout(showNext, 1000);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <div className="rounded-xl border border-gray-800/80 overflow-hidden shadow-2xl shadow-black/50">
      {/* Title bar */}
      <div className="bg-[#1a1a1a] px-4 py-2.5 flex items-center gap-2 border-b border-gray-800/50">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
          <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
          <div className="w-3 h-3 rounded-full bg-[#28c840]" />
        </div>
        <span className="ml-2 text-gray-500 text-xs font-mono">dependify — scan</span>
      </div>

      {/* Terminal body */}
      <div className="bg-[#0a0a0a] p-5 font-mono text-[13px] leading-relaxed min-h-[320px]">
        {/* Typing line */}
        {visibleLines === 0 && (
          <div className="text-white">
            {typedText}
            {isTyping && (
              <span className="inline-block w-2 h-4 bg-green-400 ml-0.5 animate-pulse" />
            )}
            {!isTyping && !typedText && (
              <span className="inline-block w-2 h-4 bg-green-400 ml-0.5 animate-pulse" />
            )}
          </div>
        )}

        {/* Revealed lines */}
        <AnimatePresence>
          {LINES.slice(0, visibleLines).map((line, i) => (
            <motion.div
              key={`${i}-${visibleLines > 0 ? "v" : "h"}`}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className={TYPE_COLORS[line.type] || "text-gray-400"}
            >
              {line.text || "\u00A0"}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Blinking cursor at end */}
        {visibleLines >= LINES.length && (
          <div className="mt-1">
            <span className="text-gray-600">$ </span>
            <span className="inline-block w-2 h-4 bg-green-400/60 animate-pulse" />
          </div>
        )}
      </div>
    </div>
  );
}
