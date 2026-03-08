"use client";

import { useState, useRef, useEffect } from "react";

// ─── Feature Data ───────────────────────────────────────────

const FEATURES = [
  {
    id: "connect",
    label: "GITHUB ONBOARDING",
    title: "Connect. Pick. Scan.",
    description: "Link your GitHub account with OAuth, select the repos you care about, and run your first scan in under 60 seconds.",
    tags: ["OAuth Connect", "Repo Picker", "Instant Scan"],
    mockup: (
      <div className="bg-[rgba(15,15,15,0.95)] rounded-xl border border-gray-800 p-5 font-mono text-sm shadow-2xl">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">github.com / connect</span>
        </div>
        <div className="space-y-2.5">
          <div className="flex items-center justify-between p-3 rounded-lg bg-green-500/5 border border-green-500/20">
            <span className="text-gray-300">acme/api-gateway</span>
            <span className="text-green-400 text-xs bg-green-500/10 px-2.5 py-0.5 rounded-full">connected</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-800/40">
            <span className="text-gray-500">acme/frontend</span>
            <span className="text-yellow-400 text-xs bg-yellow-500/10 px-2.5 py-0.5 rounded-full">scanning...</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-800/40">
            <span className="text-gray-600">acme/workers</span>
            <span className="text-gray-600 text-xs">+ add</span>
          </div>
        </div>
        <div className="mt-4 pt-3 border-t border-gray-800 space-y-2">
          <div className="flex justify-between text-xs"><span className="text-gray-600">Scan frequency</span><span className="text-white bg-gray-800 px-2 py-0.5 rounded">Weekly</span></div>
          <div className="flex justify-between text-xs"><span className="text-gray-600">Severity threshold</span><span className="text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded">High + Critical</span></div>
        </div>
      </div>
    ),
  },
  {
    id: "scan",
    label: "AI-POWERED SCAN",
    title: "AI finds what rules miss.",
    description: "Claude Sonnet reads your code like a senior engineer. It catches security flaws, outdated patterns, and maintainability debt that static analyzers overlook.",
    tags: ["Security Scan", "Debt Scoring", "Evidence Chains"],
    mockup: (
      <div className="bg-[rgba(15,15,15,0.95)] rounded-xl border border-gray-800 p-5 font-mono text-sm shadow-2xl">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">scan results / 4 findings</span>
        </div>
        <div className="flex items-center gap-3 mb-4">
          <div className="text-4xl font-bold text-red-400">F</div>
          <div><div className="text-white text-sm">Score: 85/100 debt</div><div className="text-gray-600 text-xs">3 files analyzed</div></div>
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-red-500/15 text-red-400 rounded text-xs">CRITICAL</span><span className="text-gray-400 text-xs">SQL injection in auth.py:42</span></div>
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-orange-500/15 text-orange-400 rounded text-xs">HIGH</span><span className="text-gray-400 text-xs">Hardcoded secret in config.js:8</span></div>
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-yellow-500/15 text-yellow-400 rounded text-xs">MEDIUM</span><span className="text-gray-400 text-xs">React.createClass deprecated</span></div>
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-blue-500/15 text-blue-400 rounded text-xs">LOW</span><span className="text-gray-400 text-xs">Missing error boundary</span></div>
        </div>
      </div>
    ),
  },
  {
    id: "remediate",
    label: "AUTO REMEDIATION",
    title: "Zero triage. Just patches.",
    description: "Dependify rewrites vulnerable code patterns and upgrades dependencies end-to-end. No human touch at any point, from detection to a clean verified diff.",
    tags: ["Pattern Rewriting", "CVE Patching", "Blast Radius Aware"],
    mockup: (
      <div className="bg-[rgba(15,15,15,0.95)] rounded-xl border border-gray-800 p-5 font-mono text-sm shadow-2xl">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">patch.diff / 3 vulns</span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="text-gray-600">// package.json</div>
          <div className="text-red-400/80">- &quot;lodash&quot;: &quot;4.17.19&quot;</div>
          <div className="text-green-400/80">+ &quot;lodash&quot;: &quot;4.17.21&quot;  <span className="text-gray-600"># CVE-2021-23337</span></div>
          <div className="mt-1.5 text-red-400/80">- &quot;axios&quot;: &quot;0.21.1&quot;</div>
          <div className="text-green-400/80">+ &quot;axios&quot;: &quot;1.6.8&quot;   <span className="text-gray-600"># SSRF fixed</span></div>
          <div className="mt-1.5 text-red-400/80">- &quot;minimist&quot;: &quot;1.2.5&quot;</div>
          <div className="text-green-400/80">+ &quot;minimist&quot;: &quot;1.2.8&quot;  <span className="text-gray-600"># CVE-2021-44906</span></div>
        </div>
        <div className="flex gap-2 mt-4 pt-3 border-t border-gray-800">
          <span className="text-green-400 text-xs bg-green-500/10 px-2 py-1 rounded">3 patches applied</span>
          <span className="text-green-400 text-xs bg-green-500/10 px-2 py-1 rounded">0 regressions</span>
        </div>
      </div>
    ),
  },
  {
    id: "verify",
    label: "SAFETY GATES",
    title: "Ships only when green.",
    description: "Every fix runs through sequential verification: Haiku writes, Sonnet verifies, sandbox runs build and tests. Unsafe changes never create a PR.",
    tags: ["Sandbox Testing", "3-Agent Verification", "Build/Test Gates"],
    mockup: (
      <div className="bg-[rgba(15,15,15,0.95)] rounded-xl border border-gray-800 p-5 font-mono text-sm shadow-2xl">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">pipeline run #047</span>
        </div>
        <div className="space-y-3">
          {[
            { label: "Build", time: "12s" },
            { label: "Unit Tests (147/147)", time: "38s" },
            { label: "Lint Check", time: "4s" },
            { label: "Blast Radius: 0 affected", time: "2s" },
          ].map((s) => (
            <div key={s.label} className="flex items-center justify-between">
              <div className="flex items-center gap-2"><span className="text-green-400">&#10003;</span><span className="text-gray-300">{s.label}</span></div>
              <span className="text-gray-600 text-xs">{s.time}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t border-gray-800 flex items-center justify-between">
          <span className="text-green-400 font-medium text-xs">SAFE — PR created</span>
          <span className="text-gray-600 text-xs">56s total</span>
        </div>
      </div>
    ),
  },
  {
    id: "onboard",
    label: "REPO INTELLIGENCE",
    title: "Understands your codebase.",
    description: "Within 60 seconds, Dependify generates a full architecture brief — tech stack, API routes, complexity hotspots, env vars, and a setup guide that actually works.",
    tags: ["Onboarding Brief", "API Route Map", "Complexity Analysis"],
    mockup: (
      <div className="bg-[rgba(15,15,15,0.95)] rounded-xl border border-gray-800 p-5 text-sm shadow-2xl">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs font-mono">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">repo brief / acme-api</span>
        </div>
        <div className="grid grid-cols-2 gap-2.5 mb-3">
          <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">Architecture</div><div className="text-white text-xs mt-1">Monolith</div></div>
          <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">Frameworks</div><div className="flex gap-1 mt-1"><span className="bg-gray-800 text-gray-400 rounded px-1.5 py-0.5 text-[10px]">FastAPI</span><span className="bg-gray-800 text-gray-400 rounded px-1.5 py-0.5 text-[10px]">React</span></div></div>
          <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">API Routes</div><div className="text-white text-xs mt-1">23 endpoints</div></div>
          <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">Env Vars</div><div className="text-yellow-400 text-xs mt-1">8 required</div></div>
        </div>
        <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">Hotspots</div><div className="text-orange-300 text-xs mt-1 font-mono">auth.py — 12 imports, no tests</div></div>
      </div>
    ),
  },
];

// ─── Component ──────────────────────────────────────────────

export default function LandingPage() {
  const [activeFeature, setActiveFeature] = useState(0);
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Intersection observer for scroll-triggered stacking
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = sectionRefs.current.indexOf(entry.target as HTMLDivElement);
            if (idx !== -1) setActiveFeature(idx);
          }
        });
      },
      { threshold: 0.4 }
    );
    sectionRefs.current.forEach((ref) => { if (ref) observer.observe(ref); });
    return () => observer.disconnect();
  }, []);

  const handleLogin = () => {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || "";
    const redirectUri = `${window.location.origin}/auth/callback`;
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=repo,user`;
  };

  return (
    <div className="min-h-screen text-white selection:bg-green-500/20">

      {/* ─── Header ─── */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-gray-800/60">
        <div className="bg-[rgba(5,5,5,0.8)] backdrop-blur-2xl">
          <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2.5">
                <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
                <span className="font-semibold text-[15px] tracking-tight">Dependify</span>
              </div>
              <nav className="hidden md:flex items-center gap-6 text-[13px] text-gray-400">
                <a href="#features" className="hover:text-white transition-colors">Product</a>
                <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
                <a href="#security" className="hover:text-white transition-colors">Security</a>
              </nav>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleLogin}
                className="px-4 py-1.5 text-[13px] text-gray-300 hover:text-white transition-colors"
              >
                Log In
              </button>
              <button
                onClick={handleLogin}
                className="px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white text-[13px] font-medium rounded-lg transition-colors flex items-center gap-1.5"
              >
                Sign Up
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M7 17L17 7M17 7H7M17 7v10"/></svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* ─── Hero ─── */}
      <section className="pt-36 pb-28 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-green-500/20 bg-green-500/5 text-green-400 text-[13px] mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Now in private beta
          </div>
          <h1 className="text-5xl md:text-[72px] font-bold leading-[1.05] tracking-tight mb-6">
            From alert to{" "}
            <span className="text-green-400">verified PR</span>
            <br />
            in one workflow.
          </h1>
          <p className="text-[17px] text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Dependify autonomously scans for security flaws, outdated code, and tech debt — then fixes, verifies, and ships a PR with full evidence. No manual triage.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={handleLogin}
              className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-medium rounded-xl transition-all shadow-lg shadow-green-500/15 hover:shadow-green-500/25 flex items-center gap-2 text-[15px]"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
              Connect GitHub
            </button>
            <a
              href="#features"
              className="px-6 py-3 text-gray-300 hover:text-white font-medium rounded-xl border border-gray-700/50 hover:border-gray-600 transition-all text-[15px]"
            >
              See how it works
            </a>
          </div>
        </div>
      </section>

      {/* ─── Divider ─── */}
      <div className="max-w-7xl mx-auto px-6"><div className="border-t border-gray-800/50" /></div>

      {/* ─── Features — Scroll Stack ─── */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-16">
            <span className="text-green-400 text-[13px] font-medium tracking-widest uppercase">Platform Features</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-3 leading-tight tracking-tight">
              Everything your codebase needs.
              <br />
              <span className="text-gray-600">Nothing your team has to touch.</span>
            </h2>
          </div>

          <div className="flex gap-16">
            {/* Sticky Left Nav */}
            <div className="hidden lg:block w-52 shrink-0">
              <div className="sticky top-24 space-y-0.5">
                {FEATURES.map((f, idx) => (
                  <button
                    key={f.id}
                    onClick={() => sectionRefs.current[idx]?.scrollIntoView({ behavior: "smooth", block: "center" })}
                    className={`block w-full text-left px-3 py-2.5 rounded-lg text-[13px] tracking-wide transition-all duration-300 ${
                      activeFeature === idx
                        ? "text-white bg-white/[0.04]"
                        : "text-gray-600 hover:text-gray-400"
                    }`}
                  >
                    <span className={`inline-block w-2 h-2 rounded-sm mr-2.5 transition-colors duration-300 ${
                      activeFeature === idx ? "bg-green-500" : "bg-gray-800"
                    }`} />
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Stacking Feature Cards */}
            <div className="flex-1 space-y-0">
              {FEATURES.map((feature, idx) => {
                const isActive = activeFeature === idx;
                const isPast = idx < activeFeature;

                return (
                  <div
                    key={feature.id}
                    ref={(el) => { sectionRefs.current[idx] = el; }}
                    className="border-t border-gray-800/50"
                  >
                    {/* Always-visible title bar */}
                    <button
                      onClick={() => sectionRefs.current[idx]?.scrollIntoView({ behavior: "smooth", block: "center" })}
                      className={`w-full text-left py-5 transition-all duration-300 ${
                        isPast ? "opacity-40" : ""
                      }`}
                    >
                      <h3 className={`text-2xl md:text-3xl font-bold transition-all duration-500 ${
                        isActive ? "text-white" : "text-gray-500"
                      }`}>
                        {feature.title}
                      </h3>
                    </button>

                    {/* Expandable content — only active shows */}
                    <div className={`grid transition-all duration-500 ease-in-out ${
                      isActive
                        ? "grid-rows-[1fr] opacity-100 pb-16"
                        : "grid-rows-[0fr] opacity-0"
                    }`}>
                      <div className="overflow-hidden">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 pt-2">
                          <div>
                            <p className="text-gray-400 leading-relaxed mb-6 text-[15px]">{feature.description}</p>
                            <div className="flex flex-wrap gap-2">
                              {feature.tags.map((tag) => (
                                <span key={tag} className="px-3 py-1 border border-gray-800 text-gray-500 rounded-lg text-xs">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="flex justify-end">
                            <div className="w-full max-w-sm">{feature.mockup}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* ─── How it works ─── */}
      <section id="how-it-works" className="py-24 px-6 border-t border-gray-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-green-400 text-[13px] font-medium tracking-widest uppercase">How it works</span>
            <h2 className="text-4xl font-bold mt-3 tracking-tight">Three agents. One pipeline.</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { step: "1", title: "Reader (Sonnet)", desc: "Clones your repo, scans every file for security flaws, outdated patterns, and tech debt. Returns structured findings with evidence chains." },
              { step: "2", title: "Writer (Haiku)", desc: "Takes each finding and rewrites the code. Respects blast radius — won't break exports used by other files. 100 files in parallel." },
              { step: "3", title: "Verifier (Haiku + Sonnet)", desc: "3-tier verification loop. Haiku checks, Sonnet diagnoses failures, Haiku fixes. Sandbox runs build + tests. Ships only when green." },
            ].map((item) => (
              <div key={item.step} className="bg-[rgba(20,20,20,0.5)] rounded-2xl p-6 border border-gray-800/50">
                <div className="w-9 h-9 rounded-lg bg-green-500/10 text-green-400 text-sm font-bold flex items-center justify-center mb-4">
                  {item.step}
                </div>
                <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Security ─── */}
      <section id="security" className="py-24 px-6 border-t border-gray-800/50">
        <div className="max-w-4xl mx-auto text-center">
          <span className="text-green-400 text-[13px] font-medium tracking-widest uppercase">Security First</span>
          <h2 className="text-4xl font-bold mt-3 mb-12 tracking-tight">Built for teams that ship fast and break nothing.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              { title: "Sandbox Verified", desc: "Every change runs in an isolated container. Build fails = PR blocked." },
              { title: "Blast Radius Aware", desc: "Import graph analysis prevents breaking downstream consumers." },
              { title: "Evidence Pack", desc: "Every PR includes what was found, why it matters, and proof it works." },
            ].map((item) => (
              <div key={item.title} className="p-5 rounded-xl border border-gray-800/50 bg-[rgba(20,20,20,0.3)] text-left">
                <h4 className="font-semibold mb-2 text-[15px]">{item.title}</h4>
                <p className="text-gray-500 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="py-28 px-6 border-t border-gray-800/50">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">
            Stop triaging.<br />Start shipping fixes.
          </h2>
          <p className="text-gray-500 text-lg mb-10">
            Dependify is in private beta. Request access and scan your first repo in under 60 seconds.
          </p>
          <button
            onClick={handleLogin}
            className="px-8 py-3.5 bg-green-600 hover:bg-green-500 text-white font-medium rounded-xl text-[15px] transition-all shadow-lg shadow-green-500/15 hover:shadow-green-500/25"
          >
            Request Early Access
          </button>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-gray-800/50 py-6 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-[13px] text-gray-600">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
            <span>Dependify</span>
          </div>
          <span>Built with Claude on Modal.</span>
        </div>
      </footer>
    </div>
  );
}
