"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";

// Feature data for stacking sections
const FEATURES = [
  {
    number: "01",
    title: "Connect. Pick. Scan.",
    description: "Link your GitHub account with OAuth, select the repos you care about, and run your first scan in under 60 seconds.",
    tags: ["OAuth Connect", "Repo Picker", "Instant Scan"],
    mockup: (
      <div className="bg-[rgba(20,20,20,0.9)] rounded-xl border border-gray-700/50 p-5 font-mono text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500/60"/><div className="w-3 h-3 rounded-full bg-yellow-500/60"/><div className="w-3 h-3 rounded-full bg-green-500/60"/></div>
          <span>github.com / connect</span>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-800/60 border border-green-500/30">
            <div className="flex items-center gap-2"><span className="text-gray-400">acme/api-gateway</span></div>
            <span className="text-green-400 text-xs bg-green-500/10 px-2 py-0.5 rounded">connected</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-800/40">
            <div className="flex items-center gap-2"><span className="text-gray-500">acme/frontend</span></div>
            <span className="text-yellow-400 text-xs bg-yellow-500/10 px-2 py-0.5 rounded">scanning...</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-800/40">
            <div className="flex items-center gap-2"><span className="text-gray-500">acme/workers</span></div>
            <span className="text-gray-500 text-xs">+ add</span>
          </div>
        </div>
        <div className="mt-4 pt-3 border-t border-gray-700/50 space-y-2">
          <div className="flex justify-between text-xs"><span className="text-gray-500">Scan frequency</span><span className="text-white bg-gray-700 px-2 py-0.5 rounded">Weekly</span></div>
          <div className="flex justify-between text-xs"><span className="text-gray-500">Severity threshold</span><span className="text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded">High + Critical</span></div>
        </div>
      </div>
    ),
  },
  {
    number: "02",
    title: "AI finds what rules miss.",
    description: "Claude Sonnet reads your code like a senior engineer. It catches security flaws, outdated patterns, and maintainability debt that static analyzers overlook.",
    tags: ["Security Scan", "Debt Scoring", "Evidence Chains"],
    mockup: (
      <div className="bg-[rgba(20,20,20,0.9)] rounded-xl border border-gray-700/50 p-5 font-mono text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500/60"/><div className="w-3 h-3 rounded-full bg-yellow-500/60"/><div className="w-3 h-3 rounded-full bg-green-500/60"/></div>
          <span>scan results / 4 findings</span>
        </div>
        <div className="flex items-center gap-3 mb-4">
          <div className="text-4xl font-bold text-red-400">F</div>
          <div><div className="text-white text-sm">Score: 85/100 debt</div><div className="text-gray-500 text-xs">3 files analyzed</div></div>
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded text-xs">CRITICAL</span><span className="text-gray-300 text-xs">SQL injection in auth.py:42</span></div>
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded text-xs">HIGH</span><span className="text-gray-300 text-xs">Hardcoded secret in config.js:8</span></div>
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-xs">MEDIUM</span><span className="text-gray-300 text-xs">React.createClass deprecated</span></div>
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">LOW</span><span className="text-gray-300 text-xs">Missing error boundary</span></div>
        </div>
      </div>
    ),
  },
  {
    number: "03",
    title: "Zero triage. Just patches.",
    description: "Dependify rewrites vulnerable code patterns and upgrades dependencies end-to-end. No human touch at any point, from detection to a clean verified diff.",
    tags: ["Auto Remediation", "Blast Radius", "Pattern Rewriting"],
    mockup: (
      <div className="bg-[rgba(20,20,20,0.9)] rounded-xl border border-gray-700/50 p-5 font-mono text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500/60"/><div className="w-3 h-3 rounded-full bg-yellow-500/60"/><div className="w-3 h-3 rounded-full bg-green-500/60"/></div>
          <span>patch.diff / 3 vulns</span>
        </div>
        <div className="space-y-2 text-xs">
          <div className="text-gray-500">// package.json</div>
          <div className="text-red-400">- &quot;lodash&quot;: &quot;4.17.19&quot;</div>
          <div className="text-green-400">+ &quot;lodash&quot;: &quot;4.17.21&quot;  <span className="text-gray-500"># CVE-2021-23337</span></div>
          <div className="mt-2 text-red-400">- &quot;axios&quot;: &quot;0.21.1&quot;</div>
          <div className="text-green-400">+ &quot;axios&quot;: &quot;1.6.8&quot;   <span className="text-gray-500"># SSRF fixed</span></div>
          <div className="mt-2 text-red-400">- &quot;minimist&quot;: &quot;1.2.5&quot;</div>
          <div className="text-green-400">+ &quot;minimist&quot;: &quot;1.2.8&quot;  <span className="text-gray-500"># CVE-2021-44906</span></div>
        </div>
        <div className="flex gap-2 mt-4 pt-3 border-t border-gray-700/50">
          <span className="text-green-400 text-xs bg-green-500/10 px-2 py-1 rounded">3 patches applied</span>
          <span className="text-green-400 text-xs bg-green-500/10 px-2 py-1 rounded">0 regressions</span>
        </div>
      </div>
    ),
  },
  {
    number: "04",
    title: "Ships only when green.",
    description: "Every fix runs through a sequential verification pipeline: Haiku writes, Sonnet verifies, sandbox runs build and tests. Unsafe changes never create a PR.",
    tags: ["Sandbox Testing", "3-Agent Verification", "Safety Gates"],
    mockup: (
      <div className="bg-[rgba(20,20,20,0.9)] rounded-xl border border-gray-700/50 p-5 font-mono text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500/60"/><div className="w-3 h-3 rounded-full bg-yellow-500/60"/><div className="w-3 h-3 rounded-full bg-green-500/60"/></div>
          <span>pipeline run #047</span>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="text-green-400">&#10003;</span><span className="text-white">Build</span></div><span className="text-gray-500 text-xs">12s</span></div>
          <div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="text-green-400">&#10003;</span><span className="text-white">Unit Tests (147/147)</span></div><span className="text-gray-500 text-xs">38s</span></div>
          <div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="text-green-400">&#10003;</span><span className="text-white">Lint Check</span></div><span className="text-gray-500 text-xs">4s</span></div>
          <div className="flex items-center justify-between"><div className="flex items-center gap-2"><span className="text-green-400">&#10003;</span><span className="text-white">Blast Radius: 0 affected</span></div><span className="text-gray-500 text-xs">2s</span></div>
        </div>
        <div className="mt-4 pt-3 border-t border-gray-700/50 flex items-center justify-between">
          <span className="text-green-400 font-medium">SAFE — PR created</span>
          <span className="text-gray-500 text-xs">56s total</span>
        </div>
      </div>
    ),
  },
  {
    number: "05",
    title: "Understands your codebase.",
    description: "Within 60 seconds of linking a repo, Dependify generates a full architecture brief — tech stack, frameworks, risky hotspots, and a setup guide that actually works.",
    tags: ["Repo Intelligence", "Onboarding Brief", "Risk Heatmap"],
    mockup: (
      <div className="bg-[rgba(20,20,20,0.9)] rounded-xl border border-gray-700/50 p-5 text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs font-mono">
          <div className="flex gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500/60"/><div className="w-3 h-3 rounded-full bg-yellow-500/60"/><div className="w-3 h-3 rounded-full bg-green-500/60"/></div>
          <span>repo brief / acme-api</span>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div className="bg-gray-800/40 rounded-lg p-2"><div className="text-gray-500 text-xs">Architecture</div><div className="text-white text-xs mt-1">Monolith</div></div>
          <div className="bg-gray-800/40 rounded-lg p-2"><div className="text-gray-500 text-xs">Frameworks</div><div className="flex gap-1 mt-1"><span className="bg-gray-700/60 text-gray-300 rounded px-1.5 py-0.5 text-xs">FastAPI</span><span className="bg-gray-700/60 text-gray-300 rounded px-1.5 py-0.5 text-xs">React</span></div></div>
        </div>
        <div className="bg-gray-800/40 rounded-lg p-2"><div className="text-gray-500 text-xs">Risky Hotspots</div><div className="text-orange-300 text-xs mt-1 font-mono">auth.py — 12 imports, no tests</div><div className="text-orange-300 text-xs font-mono">utils/db.ts — raw SQL queries</div></div>
      </div>
    ),
  },
];

// Sticky feature nav items for left sidebar
const FEATURE_NAV = [
  "GitHub Onboarding",
  "AI-Powered Scan",
  "Auto Remediation",
  "Safety Gates",
  "Repo Intelligence",
];

export default function LandingPage() {
  const [activeFeature, setActiveFeature] = useState(0);
  const featureRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Intersection observer for stacking scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const index = featureRefs.current.indexOf(entry.target as HTMLDivElement);
            if (index !== -1) setActiveFeature(index);
          }
        });
      },
      { threshold: 0.5, rootMargin: "-20% 0px -20% 0px" }
    );

    featureRefs.current.forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, []);

  const handleLogin = () => {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || "";
    const redirectUri = `${window.location.origin}/auth/callback`;
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=repo,user`;
  };

  return (
    <div className="min-h-screen text-white">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[rgba(0,0,0,0.6)] backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
            <span className="font-bold text-lg">Dependify</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-gray-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
            <a href="#security" className="hover:text-white transition-colors">Security</a>
          </div>
          <button
            onClick={handleLogin}
            className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Request Early Access
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-40 pb-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-green-500/30 bg-green-500/5 text-green-400 text-sm mb-8">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            Now in private beta
          </div>
          <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
            From alert to{" "}
            <span className="text-green-400">verified PR</span>
            <br />
            in one workflow.
          </h1>
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Dependify autonomously scans for security flaws, outdated code, and tech debt — then fixes, verifies, and ships a PR with full evidence. No manual triage.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={handleLogin}
              className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-green-500/20 hover:shadow-green-500/30 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
              Connect GitHub
            </button>
            <a
              href="#features"
              className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl border border-white/10 transition-all"
            >
              See how it works
            </a>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="max-w-7xl mx-auto px-6"><div className="border-t border-gray-800/50" /></div>

      {/* Features - Stacking Sections */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-16">
            <span className="text-green-400 text-sm font-medium tracking-wider uppercase">Platform Features</span>
            <h2 className="text-4xl md:text-5xl font-bold mt-3 leading-tight">
              Everything your codebase needs.
              <br />
              <span className="text-gray-500">Nothing your team has to touch.</span>
            </h2>
            <p className="text-gray-400 mt-4 max-w-2xl">
              Five tightly integrated capabilities — from first scan to merged PR — all operating autonomously.
            </p>
          </div>

          <div className="flex gap-12">
            {/* Sticky Nav (left) */}
            <div className="hidden lg:block w-56 shrink-0">
              <div className="sticky top-32 space-y-1">
                {FEATURE_NAV.map((name, idx) => (
                  <button
                    key={name}
                    onClick={() => featureRefs.current[idx]?.scrollIntoView({ behavior: "smooth", block: "center" })}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                      activeFeature === idx
                        ? "text-white font-medium bg-white/5"
                        : "text-gray-500 hover:text-gray-300"
                    }`}
                  >
                    <span className={`inline-block w-2 h-2 rounded-sm mr-2 ${activeFeature === idx ? "bg-green-500" : "bg-gray-700"}`} />
                    {name}
                  </button>
                ))}
              </div>
            </div>

            {/* Feature Cards (right) */}
            <div className="flex-1 space-y-8">
              {FEATURES.map((feature, idx) => (
                <div
                  key={feature.number}
                  ref={(el) => { featureRefs.current[idx] = el; }}
                  className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center min-h-[400px]"
                >
                  <div>
                    <span className="text-green-400 text-sm font-mono">{feature.number}</span>
                    <h3 className="text-3xl font-bold mt-2 mb-4">{feature.title}</h3>
                    <p className="text-gray-400 leading-relaxed mb-6">{feature.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {feature.tags.map((tag) => (
                        <span key={tag} className="px-3 py-1 border border-gray-700/50 text-gray-400 rounded-lg text-xs">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <div className="w-full max-w-md">
                      {feature.mockup}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-green-400 text-sm font-medium tracking-wider uppercase">How it works</span>
            <h2 className="text-4xl font-bold mt-3">Three agents. One pipeline.</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: "1", title: "Reader (Sonnet)", desc: "Clones your repo, scans every file for security flaws, outdated patterns, and tech debt. Returns structured findings with evidence chains." },
              { step: "2", title: "Writer (Haiku)", desc: "Takes each finding and rewrites the code. Respects blast radius — won't break exports used by other files. 100 files in parallel." },
              { step: "3", title: "Verifier (Haiku + Sonnet)", desc: "3-tier verification loop. Haiku checks, Sonnet diagnoses failures, Haiku fixes. Sandbox runs build + tests. Ships only when green." },
            ].map((item) => (
              <div key={item.step} className="bg-[rgba(30,30,30,0.5)] backdrop-blur-sm rounded-2xl p-6 border border-gray-800/50">
                <div className="w-10 h-10 rounded-xl bg-green-500/10 text-green-400 font-bold flex items-center justify-center mb-4">
                  {item.step}
                </div>
                <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security */}
      <section id="security" className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <span className="text-green-400 text-sm font-medium tracking-wider uppercase">Security First</span>
          <h2 className="text-4xl font-bold mt-3 mb-6">Built for teams that ship fast and break nothing.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            {[
              { title: "Sandbox Verified", desc: "Every change runs in an isolated container. Build fails = PR blocked." },
              { title: "Blast Radius Aware", desc: "Import graph analysis prevents breaking downstream consumers." },
              { title: "Evidence Pack", desc: "Every PR includes what was found, why it matters, and proof it works." },
            ].map((item) => (
              <div key={item.title} className="p-5 rounded-xl border border-gray-800/50 bg-[rgba(30,30,30,0.3)]">
                <h4 className="font-semibold mb-2">{item.title}</h4>
                <p className="text-gray-400 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Stop triaging.<br />Start shipping fixes.
          </h2>
          <p className="text-gray-400 text-lg mb-10">
            Dependify is in private beta. Request access and scan your first repo in under 60 seconds.
          </p>
          <button
            onClick={handleLogin}
            className="px-8 py-4 bg-green-600 hover:bg-green-500 text-white font-semibold rounded-xl text-lg transition-all shadow-lg shadow-green-500/20 hover:shadow-green-500/30"
          >
            Request Early Access
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-8 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>Dependify</span>
          </div>
          <span>Built with Claude on Modal.</span>
        </div>
      </footer>
    </div>
  );
}
