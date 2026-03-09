"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

interface EarlyAccessFormProps {
  variant?: "hero" | "cta";
}

export default function EarlyAccessForm({ variant = "hero" }: EarlyAccessFormProps) {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [alreadyRegistered, setAlreadyRegistered] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("early_access_email");
    if (saved) {
      setEmail(saved);
      setAlreadyRegistered(true);
      setState("done");
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || state === "loading") return;

    setState("loading");
    try {
      const res = await fetch(`${API_URL}/early-access`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to register");
      }

      localStorage.setItem("early_access_email", email.trim());
      setState("done");
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  };

  if (state === "done") {
    return (
      <div className={`flex items-center gap-3 ${variant === "cta" ? "justify-center" : ""}`}>
        <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
          <svg className="w-3 h-3 text-green-400" fill="none" strokeWidth="3" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <span className="text-green-400 text-sm">
          {alreadyRegistered ? "You're registered." : "You're on the list."} We'll reach out when your spot opens.
        </span>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className={`flex gap-2 ${variant === "cta" ? "justify-center max-w-md mx-auto" : ""}`}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@company.com"
        required
        className="px-4 py-2.5 bg-white/5 border border-gray-700/60 rounded-lg text-white text-sm placeholder:text-gray-600 focus:outline-none focus:border-green-500/50 focus:ring-1 focus:ring-green-500/20 w-64 transition-colors"
      />
      <button
        type="submit"
        disabled={state === "loading"}
        className="px-5 py-2.5 bg-green-600 hover:bg-green-500 disabled:bg-green-800 disabled:cursor-wait text-white text-sm font-medium rounded-lg transition-colors whitespace-nowrap"
      >
        {state === "loading" ? "..." : state === "error" ? "Try again" : "Request Access"}
      </button>
    </form>
  );
}
