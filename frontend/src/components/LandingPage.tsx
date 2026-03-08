"use client";

import ScrollStack, { ScrollStackItem } from "./ScrollStack";
import "./scroll-stack.css";

const STEPS = [
  {
    step: "01",
    label: "CLONE & INDEX",
    title: "Reads your entire codebase.",
    description:
      "Links to your repo, clones every file, and builds a complete index — dependencies, imports, entry points, env vars. No sampling. No diffs. The whole thing.",
    accent: "#3b82f6",
    bg: "linear-gradient(135deg, #070b14 0%, #0b1120 100%)",
    border: "rgba(59,130,246,0.12)",
    mockup: (
      <div
        className="rounded-xl border p-5 font-mono text-sm"
        style={{ background: "rgba(7,11,20,0.9)", borderColor: "rgba(59,130,246,0.15)" }}
      >
        <div className="text-xs text-gray-600 mb-3 flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          indexing repo...
        </div>
        <div className="space-y-1.5 text-xs">
          {["src/ — 142 files", "tests/ — 38 files", "package.json — 47 deps", "12 API routes found", "8 env vars detected"].map((line, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-blue-400/60">›</span>
              <span className="text-gray-400">{line}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t border-gray-800 text-xs text-blue-400">
          Index complete — 180 files
        </div>
      </div>
    ),
  },
  {
    step: "02",
    label: "SCAN & SCORE",
    title: "Finds what static rules miss.",
    description:
      "Reads code the way a senior engineer would. Spots injection vectors, hardcoded secrets, deprecated APIs, missing error handling, and high-risk dependency patterns — with an evidence chain for every finding.",
    accent: "#a855f7",
    bg: "linear-gradient(135deg, #0c070f 0%, #160b1f 100%)",
    border: "rgba(168,85,247,0.12)",
    mockup: (
      <div
        className="rounded-xl border p-5 font-mono text-sm"
        style={{ background: "rgba(12,7,15,0.9)", borderColor: "rgba(168,85,247,0.15)" }}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="text-4xl font-bold" style={{ color: "#ef4444" }}>D</div>
          <div>
            <div className="text-white text-sm">62 / 100 debt</div>
            <div className="text-gray-600 text-xs">7 findings across 4 files</div>
          </div>
        </div>
        <div className="space-y-2">
          {[
            { level: "CRITICAL", color: "#ef4444", bg: "rgba(239,68,68,0.08)", label: "SQL injection — auth.py:42" },
            { level: "HIGH", color: "#f97316", bg: "rgba(249,115,22,0.08)", label: "Hardcoded secret — config.js" },
            { level: "MEDIUM", color: "#eab308", bg: "rgba(234,179,8,0.08)", label: "Deprecated API — 3 files" },
          ].map((f) => (
            <div key={f.level} className="flex items-center gap-2 text-xs">
              <span className="px-1.5 py-0.5 rounded font-mono" style={{ color: f.color, background: f.bg }}>{f.level}</span>
              <span className="text-gray-500">{f.label}</span>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    step: "03",
    label: "REWRITE",
    title: "Patches code. Upgrades deps.",
    description:
      "Rewrites each finding automatically. Knows which files depend on which — so it never breaks an export used elsewhere. Up to 100 files rewritten in parallel.",
    accent: "#22c55e",
    bg: "linear-gradient(135deg, #060e09 0%, #091508 100%)",
    border: "rgba(34,197,94,0.12)",
    mockup: (
      <div
        className="rounded-xl border p-5 font-mono text-sm"
        style={{ background: "rgba(6,14,9,0.9)", borderColor: "rgba(34,197,94,0.15)" }}
      >
        <div className="text-xs text-gray-600 mb-3">patch.diff — 3 changes</div>
        <div className="space-y-1.5 text-xs">
          <div className="text-red-400/70">- cursor.execute(f&quot;SELECT * FROM users WHERE id=&#123;uid&#125;&quot;)</div>
          <div className="text-green-400/70">+ cursor.execute("SELECT * FROM users WHERE id=?", (id,))</div>
        </div>
        <div className="mt-3 pt-3 border-t border-gray-800 space-y-1 text-xs">
          <div className="text-red-400/70">- &quot;lodash&quot;: &quot;4.17.19&quot;</div>
          <div className="text-green-400/70">+ &quot;lodash&quot;: &quot;4.17.21&quot; <span className="text-gray-700"># CVE patched</span></div>
        </div>
        <div className="flex gap-2 mt-3 pt-3 border-t border-gray-800">
          <span className="text-xs px-2 py-0.5 rounded" style={{ color: "#22c55e", background: "rgba(34,197,94,0.08)" }}>3 rewrites</span>
          <span className="text-xs px-2 py-0.5 rounded" style={{ color: "#22c55e", background: "rgba(34,197,94,0.08)" }}>14 dependents safe</span>
        </div>
      </div>
    ),
  },
  {
    step: "04",
    label: "VERIFY",
    title: "Runs your tests before touching main.",
    description:
      "Every rewrite goes through a 3-tier check loop. If build or tests fail, the fix is reattempted and diagnosed automatically. Nothing reaches a PR until the sandbox is green.",
    accent: "#f59e0b",
    bg: "linear-gradient(135deg, #0f0a05 0%, #1a1005 100%)",
    border: "rgba(245,158,11,0.12)",
    mockup: (
      <div
        className="rounded-xl border p-5 font-mono text-sm"
        style={{ background: "rgba(15,10,5,0.9)", borderColor: "rgba(245,158,11,0.15)" }}
      >
        <div className="text-xs text-gray-600 mb-3">sandbox / pipeline #047</div>
        <div className="space-y-2.5">
          {[
            { label: "Build", time: "12s", done: true },
            { label: "Tests (147 / 147)", time: "38s", done: true },
            { label: "Lint", time: "4s", done: true },
            { label: "Blast radius check", time: "2s", done: true },
          ].map((s) => (
            <div key={s.label} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-green-400 text-xs">✓</span>
                <span className="text-gray-300 text-xs">{s.label}</span>
              </div>
              <span className="text-gray-600 text-xs">{s.time}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t border-gray-800">
          <span className="text-xs font-medium text-green-400">SAFE — ready to ship</span>
        </div>
      </div>
    ),
  },
  {
    step: "05",
    label: "SHIP PR",
    title: "Opens a PR. Only when it's clean.",
    description:
      "Creates a focused pull request with every change explained — what was found, why it was risky, what was rewritten, and proof it works. Reviewers see the full evidence pack.",
    accent: "#06b6d4",
    bg: "linear-gradient(135deg, #050b0e 0%, #071318 100%)",
    border: "rgba(6,182,212,0.12)",
    mockup: (
      <div
        className="rounded-xl border p-5 text-sm"
        style={{ background: "rgba(5,11,14,0.9)", borderColor: "rgba(6,182,212,0.15)" }}
      >
        <div className="flex items-center gap-2 mb-4">
          <div className="w-4 h-4 rounded-full flex items-center justify-center" style={{ background: "rgba(34,197,94,0.15)" }}>
            <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
          </div>
          <span className="text-sm font-medium text-white">fix: patch 3 security findings</span>
        </div>
        <div className="space-y-2 text-xs">
          {[
            "✓  SQL injection → parameterized query",
            "✓  lodash → 4.17.21 (CVE-2021-23337)",
            "✓  Deprecated .createClass removed",
          ].map((line) => (
            <div key={line} className="text-gray-500">{line}</div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t border-gray-800 flex gap-3 text-xs">
          <span className="text-gray-600">3 files changed</span>
          <span style={{ color: "#22c55e" }}>+12</span>
          <span style={{ color: "#ef4444" }}>−8</span>
        </div>
      </div>
    ),
  },
];

export default function LandingPage() {
  const handleLogin = () => {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || "";
    const redirectUri = `${window.location.origin}/auth/callback`;
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=repo,user`;
  };

  return (
    <ScrollStack className="text-white selection:bg-green-500/20">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-gray-800/60">
        <div className="bg-[rgba(5,5,5,0.85)] backdrop-blur-2xl">
          <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2.5">
                <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
                <span className="font-semibold text-[15px] tracking-tight">Dependify</span>
              </div>
              <nav className="hidden md:flex items-center gap-6 text-[13px] text-gray-400">
                <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
                <a href="#security" className="hover:text-white transition-colors">Security</a>
              </nav>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={handleLogin} className="px-4 py-1.5 text-[13px] text-gray-300 hover:text-white transition-colors">Log In</button>
              <button onClick={handleLogin} className="px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white text-[13px] font-medium rounded-lg transition-colors flex items-center gap-1.5">
                Sign Up
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M7 17L17 7M17 7H7M17 7v10"/></svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-28 pb-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-green-500/20 bg-green-500/5 text-green-400 text-[13px] mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Now in private beta
          </div>
          <h1 className="text-5xl md:text-[72px] font-bold leading-[1.05] tracking-tight mb-6">
            From alert to <span className="text-green-400">verified PR</span><br />in one workflow.
          </h1>
          <p className="text-[17px] text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Scans your codebase for security flaws, outdated patterns, and tech debt — then rewrites the code, verifies it compiles and passes tests, and opens a PR. No manual triage.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button onClick={handleLogin} className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-medium rounded-xl transition-all shadow-lg shadow-green-500/15 flex items-center gap-2 text-[15px]">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
              Connect GitHub
            </button>
            <a href="#how-it-works" className="px-6 py-3 text-gray-300 hover:text-white font-medium rounded-xl border border-gray-700/50 hover:border-gray-600 transition-all text-[15px]">See how it works</a>
          </div>
        </div>
      </section>

      {/* Section label */}
      <section id="how-it-works" className="pt-16 pb-4 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <span className="text-green-400 text-[13px] font-medium tracking-widest uppercase">How it works</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-3 leading-tight tracking-tight">
              Five steps.<br /><span className="text-gray-600">Fully automated.</span>
            </h2>
          </div>
          {/* Pipeline steps overview */}
          <div className="hidden lg:flex items-center gap-0 text-[11px] font-mono">
            {STEPS.map((s, i) => (
              <div key={i} className="flex items-center">
                <div className="px-3 py-1.5 rounded border" style={{ borderColor: s.border, color: s.accent, background: "transparent" }}>
                  {s.label}
                </div>
                {i < STEPS.length - 1 && <div className="w-6 h-px bg-gray-800" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stacking feature cards */}
      {STEPS.map((step, idx) => (
        <ScrollStackItem key={idx}>
          <div className="max-w-6xl mx-auto px-6">
            <div
              className="rounded-2xl p-8 md:p-10 min-h-[22rem]"
              style={{
                background: step.bg,
                border: `1px solid ${step.border}`,
                boxShadow: `0 0 60px ${step.accent}08`,
              }}
            >
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
                <div>
                  <div className="flex items-center gap-3 mb-5">
                    <span
                      className="text-[11px] font-mono tracking-widest font-semibold"
                      style={{ color: step.accent }}
                    >
                      {step.step}
                    </span>
                    <div className="h-px w-6" style={{ background: step.border }} />
                    <span
                      className="text-[10px] font-semibold tracking-widest uppercase"
                      style={{ color: `${step.accent}99` }}
                    >
                      {step.label}
                    </span>
                  </div>
                  <h3 className="text-2xl md:text-[2rem] font-bold mb-4 tracking-tight leading-tight text-white">
                    {step.title}
                  </h3>
                  <p className="text-gray-400 leading-relaxed text-[15px] max-w-sm">
                    {step.description}
                  </p>
                </div>
                <div className="flex justify-center lg:justify-end">
                  <div className="w-full max-w-sm">{step.mockup}</div>
                </div>
              </div>
            </div>
          </div>
        </ScrollStackItem>
      ))}

      {/* Security */}
      <section id="security" className="py-24 px-6 mt-16 border-t border-gray-800/30">
        <div className="max-w-4xl mx-auto text-center">
          <span className="text-green-400 text-[13px] font-medium tracking-widest uppercase">Safety first</span>
          <h2 className="text-4xl font-bold mt-3 mb-12 tracking-tight">Ship fast. Break nothing.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              { title: "Sandbox verified", desc: "Every rewrite runs in an isolated container. Build fails = PR blocked. Always." },
              { title: "Blast radius aware", desc: "Import graph prevents breaking downstream consumers. High-dependent files are handled with extra care." },
              { title: "Evidence included", desc: "Every PR ships with what was found, why it was risky, and proof the fix works." },
            ].map((item) => (
              <div key={item.title} className="p-5 rounded-xl border border-gray-800/50 bg-[rgba(18,18,18,0.4)] text-left">
                <h4 className="font-semibold mb-2 text-[15px]">{item.title}</h4>
                <p className="text-gray-500 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-28 px-6 border-t border-gray-800/30">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">Stop triaging.<br />Start shipping fixes.</h2>
          <p className="text-gray-500 text-lg mb-10">Private beta. Scan your first repo in under 60 seconds.</p>
          <button onClick={handleLogin} className="px-8 py-3.5 bg-green-600 hover:bg-green-500 text-white font-medium rounded-xl text-[15px] transition-all shadow-lg shadow-green-500/15">
            Request Early Access
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800/30 py-6 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-[13px] text-gray-600">
          <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-green-500" /><span>Dependify</span></div>
          <span>Private beta.</span>
        </div>
      </footer>
    </ScrollStack>
  );
}
