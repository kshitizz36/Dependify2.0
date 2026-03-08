"use client";

import ScrollStack, { ScrollStackItem } from "./ScrollStack";
import "./scroll-stack.css";

const FEATURE_CARDS = [
  {
    title: "Connect. Pick. Scan.",
    description: "Link your GitHub account with OAuth, select repos, and run your first scan in under 60 seconds.",
    tags: ["OAuth Connect", "Repo Picker", "Instant Scan"],
    mockup: (
      <div className="bg-[rgba(12,12,12,0.95)] rounded-xl border border-gray-800 p-5 font-mono text-sm">
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
      </div>
    ),
  },
  {
    title: "AI finds what rules miss.",
    description: "Claude Sonnet reads your code like a senior engineer — catches security flaws, outdated patterns, and tech debt that static analyzers overlook.",
    tags: ["Security Scan", "Debt Scoring", "Evidence Chains"],
    mockup: (
      <div className="bg-[rgba(12,12,12,0.95)] rounded-xl border border-gray-800 p-5 font-mono text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">scan / 4 findings</span>
        </div>
        <div className="flex items-center gap-3 mb-4">
          <div className="text-4xl font-bold text-red-400">F</div>
          <div><div className="text-white text-sm">85/100 debt</div><div className="text-gray-600 text-xs">3 files</div></div>
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-red-500/15 text-red-400 rounded text-xs">CRITICAL</span><span className="text-gray-400 text-xs">SQL injection in auth.py:42</span></div>
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-orange-500/15 text-orange-400 rounded text-xs">HIGH</span><span className="text-gray-400 text-xs">Hardcoded secret in config.js</span></div>
          <div className="flex items-center gap-2"><span className="px-1.5 py-0.5 bg-yellow-500/15 text-yellow-400 rounded text-xs">MEDIUM</span><span className="text-gray-400 text-xs">Deprecated React API</span></div>
        </div>
      </div>
    ),
  },
  {
    title: "Zero triage. Just patches.",
    description: "Rewrites vulnerable patterns and upgrades dependencies end-to-end. From detection to a clean verified diff — no human touch.",
    tags: ["Pattern Rewriting", "CVE Patching", "Blast Radius"],
    mockup: (
      <div className="bg-[rgba(12,12,12,0.95)] rounded-xl border border-gray-800 p-5 font-mono text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">patch.diff / 3 vulns</span>
        </div>
        <div className="space-y-1.5 text-xs">
          <div className="text-red-400/80">- &quot;lodash&quot;: &quot;4.17.19&quot;</div>
          <div className="text-green-400/80">+ &quot;lodash&quot;: &quot;4.17.21&quot;  <span className="text-gray-600"># CVE-2021-23337</span></div>
          <div className="mt-2 text-red-400/80">- &quot;axios&quot;: &quot;0.21.1&quot;</div>
          <div className="text-green-400/80">+ &quot;axios&quot;: &quot;1.6.8&quot;   <span className="text-gray-600"># SSRF fixed</span></div>
        </div>
        <div className="flex gap-2 mt-4 pt-3 border-t border-gray-800">
          <span className="text-green-400 text-xs bg-green-500/10 px-2 py-1 rounded">3 patches</span>
          <span className="text-green-400 text-xs bg-green-500/10 px-2 py-1 rounded">0 regressions</span>
        </div>
      </div>
    ),
  },
  {
    title: "Ships only when green.",
    description: "Every fix runs through verification: Haiku writes, Sonnet verifies, sandbox runs build and tests. Unsafe changes never create a PR.",
    tags: ["Sandbox Testing", "3-Agent Verify", "Safety Gates"],
    mockup: (
      <div className="bg-[rgba(12,12,12,0.95)] rounded-xl border border-gray-800 p-5 font-mono text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">pipeline #047</span>
        </div>
        <div className="space-y-3">
          {["Build — 12s", "Tests (147/147) — 38s", "Lint — 4s", "Blast Radius — 2s"].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <span className="text-green-400">&#10003;</span>
              <span className="text-gray-300 text-xs">{s}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-3 border-t border-gray-800">
          <span className="text-green-400 font-medium text-xs">SAFE — PR created</span>
        </div>
      </div>
    ),
  },
  {
    title: "Understands your codebase.",
    description: "Architecture brief, API routes, complexity hotspots, env vars, and a verified setup guide — in 60 seconds.",
    tags: ["Onboarding Brief", "API Map", "Complexity"],
    mockup: (
      <div className="bg-[rgba(12,12,12,0.95)] rounded-xl border border-gray-800 p-5 text-sm">
        <div className="flex items-center gap-2 mb-4 text-gray-500 text-xs font-mono">
          <div className="flex gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"/><div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"/><div className="w-2.5 h-2.5 rounded-full bg-[#28c840]"/></div>
          <span className="ml-2">brief / acme-api</span>
        </div>
        <div className="grid grid-cols-2 gap-2.5 mb-3">
          <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">Architecture</div><div className="text-white text-xs mt-1">Monolith</div></div>
          <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">Frameworks</div><div className="flex gap-1 mt-1"><span className="bg-gray-800 text-gray-400 rounded px-1.5 py-0.5 text-[10px]">FastAPI</span><span className="bg-gray-800 text-gray-400 rounded px-1.5 py-0.5 text-[10px]">React</span></div></div>
          <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">API Routes</div><div className="text-white text-xs mt-1">23 endpoints</div></div>
          <div className="bg-gray-800/30 rounded-lg p-2.5"><div className="text-gray-600 text-xs">Env Vars</div><div className="text-yellow-400 text-xs mt-1">8 required</div></div>
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
                <a href="#features" className="hover:text-white transition-colors">Product</a>
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
            Dependify autonomously scans for security flaws, outdated code, and tech debt — then fixes, verifies, and ships a PR with full evidence. No manual triage.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button onClick={handleLogin} className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-medium rounded-xl transition-all shadow-lg shadow-green-500/15 flex items-center gap-2 text-[15px]">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
              Connect GitHub
            </button>
            <a href="#features" className="px-6 py-3 text-gray-300 hover:text-white font-medium rounded-xl border border-gray-700/50 hover:border-gray-600 transition-all text-[15px]">See how it works</a>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-6"><div className="border-t border-gray-800/50" /></div>

      {/* Features heading */}
      <section id="features" className="pt-20 px-6">
        <div className="max-w-7xl mx-auto mb-8">
          <span className="text-green-400 text-[13px] font-medium tracking-widest uppercase">Platform Features</span>
          <h2 className="text-4xl md:text-5xl font-bold mt-3 leading-tight tracking-tight">
            Everything your codebase needs.<br /><span className="text-gray-600">Nothing your team has to touch.</span>
          </h2>
        </div>
      </section>

      {/* Stacking feature cards */}
      {FEATURE_CARDS.map((feature, idx) => (
        <ScrollStackItem key={idx}>
          <div className="max-w-6xl mx-auto px-6">
            <div className="bg-[rgba(18,18,18,0.95)] backdrop-blur-sm rounded-2xl border border-gray-800/60 p-8 md:p-10 shadow-2xl shadow-black/40 min-h-[20rem]">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
                <div>
                  <span className="text-green-400 text-xs font-mono mb-2 block">0{idx + 1}</span>
                  <h3 className="text-2xl md:text-3xl font-bold mb-4 tracking-tight">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed mb-5 text-[15px]">{feature.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {feature.tags.map((tag) => (
                      <span key={tag} className="px-3 py-1 border border-gray-800 text-gray-500 rounded-lg text-xs">{tag}</span>
                    ))}
                  </div>
                </div>
                <div className="flex justify-center lg:justify-end">
                  <div className="w-full max-w-sm">{feature.mockup}</div>
                </div>
              </div>
            </div>
          </div>
        </ScrollStackItem>
      ))}

      {/* How it works */}
      <section id="how-it-works" className="py-28 px-6 mt-16">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-green-400 text-[13px] font-medium tracking-widest uppercase">How it works</span>
            <h2 className="text-4xl font-bold mt-3 tracking-tight">Three agents. One pipeline.</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { step: "1", title: "Reader (Sonnet)", desc: "Clones your repo, scans every file for security flaws, outdated patterns, and tech debt. Returns findings with evidence." },
              { step: "2", title: "Writer (Haiku)", desc: "Rewrites code for each finding. Blast-radius aware — preserves exports. 100 files in parallel on Modal." },
              { step: "3", title: "Verifier", desc: "3-tier loop: check, diagnose, fix. Sandbox runs build + tests in isolation. Ships only when green." },
            ].map((item) => (
              <div key={item.step} className="bg-[rgba(18,18,18,0.6)] rounded-2xl p-6 border border-gray-800/50">
                <div className="w-9 h-9 rounded-lg bg-green-500/10 text-green-400 text-sm font-bold flex items-center justify-center mb-4">{item.step}</div>
                <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security */}
      <section id="security" className="py-24 px-6 border-t border-gray-800/30">
        <div className="max-w-4xl mx-auto text-center">
          <span className="text-green-400 text-[13px] font-medium tracking-widest uppercase">Security First</span>
          <h2 className="text-4xl font-bold mt-3 mb-12 tracking-tight">Ship fast. Break nothing.</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              { title: "Sandbox Verified", desc: "Every change runs in an isolated container. Build fails = PR blocked." },
              { title: "Blast Radius Aware", desc: "Import graph analysis prevents breaking downstream files." },
              { title: "Evidence Pack", desc: "Every PR includes what was found, why, and proof it works." },
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
          <span>Built with Claude on Modal.</span>
        </div>
      </footer>
    </ScrollStack>
  );
}
