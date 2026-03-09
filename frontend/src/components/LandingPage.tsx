"use client";

import { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Shield, GitBranch, FileCheck } from "lucide-react";
import TerminalDemo from "./landing/TerminalDemo";
import EarlyAccessForm from "./landing/EarlyAccessForm";
import PipelineStrip from "./landing/PipelineStrip";

/* ───────────────────── Animated counter hook ───────────────────── */
function useCountUp(end: number, duration = 2000, startOnView = true) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref as React.RefObject<Element>, { once: true, margin: "-10%" });
  const started = useRef(false);

  useEffect(() => {
    if (!startOnView || !inView || started.current) return;
    started.current = true;
    const start = performance.now();
    const step = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(eased * end));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [inView, end, duration, startOnView]);

  return { count, ref };
}

/* ───────────────────── Main Landing Page ───────────────────── */
export default function LandingPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const ctaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const token = localStorage.getItem("auth_token") || localStorage.getItem("access_token");
    setIsLoggedIn(!!token);
  }, []);

  const scrollToCTA = () => {
    ctaRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleGitHubLogin = () => {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || "";
    const redirectUri = `${window.location.origin}/auth/callback`;
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=repo,user`;
  };

  /* ── Stats ── */
  const stat1 = useCountUp(4200);
  const stat2 = useCountUp(97);
  const stat3 = useCountUp(60);
  const stat4 = useCountUp(100);

  return (
    <div className="min-h-screen bg-[#050505] text-white overflow-x-hidden">
      {/* ━━━━━━━━━━━━━━━━━ HEADER ━━━━━━━━━━━━━━━━━ */}
      <header className="sticky top-0 z-50 border-b border-white/[0.04]">
        <div className="bg-[rgba(5,5,5,0.8)] backdrop-blur-2xl">
          <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
              <span className="font-semibold text-[15px] tracking-tight">Dependify</span>
            </div>
            <nav className="hidden md:flex items-center gap-6 text-[13px] text-gray-500">
              <a href="#pipeline" className="hover:text-white transition-colors">How it works</a>
              <a href="#safety" className="hover:text-white transition-colors">Safety</a>
            </nav>
            <div className="flex items-center gap-3">
              {isLoggedIn ? (
                <a
                  href="/"
                  className="px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white text-[13px] font-medium rounded-lg transition-colors"
                >
                  Go to Dashboard
                </a>
              ) : (
                <>
                  <button
                    onClick={handleGitHubLogin}
                    className="px-4 py-1.5 text-[13px] text-gray-400 hover:text-white transition-colors hidden sm:block"
                  >
                    Log In
                  </button>
                  <button
                    onClick={scrollToCTA}
                    className="px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white text-[13px] font-medium rounded-lg transition-colors"
                  >
                    Request Access
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* ━━━━━━━━━━━━━━━━━ HERO ━━━━━━━━━━━━━━━━━ */}
      <section className="pt-20 pb-24 px-6">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left — copy + email form */}
          <div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-green-500/15 bg-green-500/5 text-green-400 text-[12px] mb-8">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Private beta
            </div>

            <h1 className="text-4xl md:text-[56px] font-bold leading-[1.08] tracking-tight mb-5">
              Your codebase
              <br />
              has debt.
              <br />
              <span className="text-green-400">We pay it off.</span>
            </h1>

            <p className="text-gray-400 text-[16px] leading-relaxed mb-8 max-w-md">
              Scans for security flaws, rewrites the code, verifies it compiles and passes tests, and opens a PR.
              Fully automated.
            </p>

            <EarlyAccessForm variant="hero" />
          </div>

          {/* Right — terminal */}
          <div className="hidden lg:block">
            <TerminalDemo />
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━ PIPELINE ━━━━━━━━━━━━━━━━━ */}
      <section id="pipeline" className="py-24 px-6 border-t border-white/[0.04]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-green-400 text-[12px] font-semibold tracking-widest uppercase">How it works</span>
            <h2 className="text-3xl md:text-4xl font-bold mt-3 tracking-tight">
              Five steps. Zero manual work.
            </h2>
          </div>
          <PipelineStrip />
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━ BEFORE / AFTER ━━━━━━━━━━━━━━━━━ */}
      <section className="py-20 px-6 border-t border-white/[0.04]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tight">See the diff.</h2>
            <p className="text-gray-500 mt-2 text-[15px]">Real vulnerability, real fix, real PR.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Before */}
            <div className="rounded-xl border border-red-500/10 bg-red-500/[0.03] p-6">
              <div className="text-red-400 text-[11px] font-semibold tracking-widest uppercase mb-4">Before</div>
              <pre className="font-mono text-[13px] text-gray-400 leading-relaxed whitespace-pre-wrap">
{`@app.post("/login")
def login(request):
    user = request.json["user"]
    pw = request.json["pass"]
    q = f"SELECT * FROM users
         WHERE name='{user}'
         AND pass='{pw}'"
    cursor.execute(q)
    return cursor.fetchone()`}
              </pre>
              <div className="mt-4 pt-3 border-t border-red-500/10">
                <span className="text-red-400 text-xs">SQL injection — CRITICAL</span>
              </div>
            </div>

            {/* After */}
            <div className="rounded-xl border border-green-500/10 bg-green-500/[0.03] p-6">
              <div className="text-green-400 text-[11px] font-semibold tracking-widest uppercase mb-4">After</div>
              <pre className="font-mono text-[13px] text-gray-400 leading-relaxed whitespace-pre-wrap">
{`@app.post("/login")
def login(request):
    user = request.json["user"]
    pw = request.json["pass"]
    q = """SELECT * FROM users
           WHERE name = ?
           AND pass = ?"""
    cursor.execute(q, (user, pw))
    return cursor.fetchone()`}
              </pre>
              <div className="mt-4 pt-3 border-t border-green-500/10 flex items-center gap-2">
                <span className="text-green-400 text-xs">Parameterized query — SAFE</span>
                <span className="text-gray-600 text-xs">sandbox: build OK, tests pass</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━ STATS BAR ━━━━━━━━━━━━━━━━━ */}
      <section className="py-16 px-6 border-t border-white/[0.04] bg-white/[0.01]">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { ref: stat1.ref, count: stat1.count, suffix: "+", label: "vulnerabilities found" },
            { ref: stat2.ref, count: stat2.count, suffix: "%", label: "build pass rate" },
            { ref: stat3.ref, count: stat3.count, prefix: "<", suffix: "s", label: "first scan time" },
            { ref: stat4.ref, count: stat4.count, suffix: "", label: "parallel rewrites" },
          ].map((s, i) => (
            <div key={i}>
              <div className="text-3xl md:text-4xl font-bold font-mono tracking-tight text-white">
                <span ref={s.ref}>
                  {s.prefix || ""}{s.count.toLocaleString()}{s.suffix}
                </span>
              </div>
              <div className="text-gray-600 text-xs mt-1 tracking-wide uppercase">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━ SAFETY ━━━━━━━━━━━━━━━━━ */}
      <section id="safety" className="py-24 px-6 border-t border-white/[0.04]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <span className="text-green-400 text-[12px] font-semibold tracking-widest uppercase">Safety first</span>
            <h2 className="text-3xl md:text-4xl font-bold mt-3 tracking-tight">Ship fast. Break nothing.</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              {
                icon: <Shield className="w-5 h-5" />,
                title: "Sandbox verified",
                desc: "Every rewrite runs in an isolated container. Build fails or test breaks = PR blocked.",
                accent: "#22c55e",
              },
              {
                icon: <GitBranch className="w-5 h-5" />,
                title: "Blast radius aware",
                desc: "Import graph analysis prevents breaking downstream consumers. High-dependent files get extra care.",
                accent: "#3b82f6",
              },
              {
                icon: <FileCheck className="w-5 h-5" />,
                title: "Evidence included",
                desc: "Every PR includes what was found, why it was risky, and proof the fix compiles and passes tests.",
                accent: "#f59e0b",
              },
            ].map((card) => (
              <div
                key={card.title}
                className="p-6 rounded-xl border border-white/[0.04] bg-white/[0.02] hover:bg-white/[0.03] transition-colors"
              >
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center mb-4"
                  style={{ background: `${card.accent}12`, color: card.accent }}
                >
                  {card.icon}
                </div>
                <h4 className="font-semibold mb-2 text-[15px]">{card.title}</h4>
                <p className="text-gray-500 text-sm leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━ BOTTOM CTA ━━━━━━━━━━━━━━━━━ */}
      <section ref={ctaRef} className="py-28 px-6 border-t border-white/[0.04]">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 tracking-tight">
            Stop triaging.
            <br />
            Start shipping fixes.
          </h2>
          <p className="text-gray-500 mb-8">Private beta. Scan your first repo in under 60 seconds.</p>
          <EarlyAccessForm variant="cta" />
          <div className="mt-6">
            <button
              onClick={handleGitHubLogin}
              className="text-gray-600 hover:text-gray-400 text-[13px] transition-colors inline-flex items-center gap-1.5"
            >
              Already approved?
              <span className="underline underline-offset-2">Log in with GitHub</span>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 17L17 7M17 7H7M17 7v10" />
              </svg>
            </button>
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━ FOOTER ━━━━━━━━━━━━━━━━━ */}
      <footer className="border-t border-white/[0.04] py-6 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-[13px] text-gray-700">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
            <span>Dependify</span>
          </div>
          <span>Private beta.</span>
        </div>
      </footer>
    </div>
  );
}
