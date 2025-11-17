"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import GradientCanvas from "@/components/GradientCanvas";
import FeaturesShowcase from "@/components/FeaturesShowcase";

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [showEmailInput, setShowEmailInput] = useState(false);

  const handleGitHubLogin = async () => {
    setIsLoading(true);
    // GitHub OAuth flow
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || "your_github_oauth_client_id_here";
    const redirectUri = `${window.location.origin}/auth/callback`;
    const scope = "repo,user";

    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Simulate email login
    setTimeout(() => {
      setIsLoading(false);
      router.push("/");
    }, 1500);
  };

  // Theme matching your main app
  const theme = {
    gradientColor1: "#023601", // Deep forest green
    gradientColor2: "#1b4332", // Dark forest green
    gradientColor3: "#000000", // Black
  };

  return (
    <>
      <GradientCanvas
        gradientColor1={theme.gradientColor1}
        gradientColor2={theme.gradientColor2}
        gradientColor3={theme.gradientColor3}
      />
      <div className="min-h-screen p-8">
        {/* Login Card */}
        <div className="max-w-md mx-auto relative mb-16">
          {/* Glassmorphism Card */}
          <div className="relative bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] rounded-[24px] border border-gray-700/50 p-8 shadow-2xl">
            {/* Logo and Title */}
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <Image
                    src="/pou-transparent-cropped.png"
                    alt="Dependify Mascot"
                    width={96}
                    height={96}
                    priority={true}
                    style={{ width: 'auto', height: 'auto', maxWidth: '96px', maxHeight: '96px' }}
                    className="object-contain"
                  />
                </div>
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Welcome to Dependify
              </h1>
              <p className="text-gray-400 text-sm">
                Modernize your code with AI-powered refactoring
              </p>
            </div>

            {/* GitHub Login Button */}
            <button
              onClick={handleGitHubLogin}
              disabled={isLoading}
              className="w-full bg-white hover:bg-gray-100 text-gray-900 font-semibold py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-3 mb-4 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path
                      fillRule="evenodd"
                      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Continue with GitHub
                </>
              )}
            </button>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-700"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-[rgba(30,30,30,0.8)] text-gray-400">
                  or
                </span>
              </div>
            </div>

            {/* Email Login Option */}
            {!showEmailInput ? (
              <button
                onClick={() => setShowEmailInput(true)}
                className="w-full bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-3 border border-gray-700"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  strokeWidth="2"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                Continue with Email
              </button>
            ) : (
              <form onSubmit={handleEmailLogin} className="space-y-4">
                <div>
                  <label
                    htmlFor="email"
                    className="block text-sm font-medium text-gray-300 mb-2"
                  >
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                    placeholder="you@example.com"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoading || !email}
                  className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-500/30 hover:shadow-green-500/50"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Signing in...
                    </div>
                  ) : (
                    "Sign In"
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowEmailInput(false)}
                  className="w-full text-gray-400 hover:text-white text-sm transition-colors"
                >
                  Back to options
                </button>
              </form>
            )}

            {/* Footer */}
            <div className="mt-8 text-center">
              <p className="text-xs text-gray-500">
                By continuing, you agree to our{" "}
                <a href="#" className="text-green-400 hover:text-green-300 transition-colors">
                  Terms of Service
                </a>{" "}
                and{" "}
                <a href="#" className="text-green-400 hover:text-green-300 transition-colors">
                  Privacy Policy
                </a>
              </p>
            </div>
          </div>

          {/* Decorative Elements */}
          <div className="absolute -top-10 -left-10 w-40 h-40 bg-green-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-green-500/10 rounded-full blur-3xl" />
        </div>

        {/* Features Showcase Section */}
        <div className="max-w-7xl mx-auto mt-16 mb-12">
          <FeaturesShowcase />
        </div>

        {/* Footer Note */}
        <div className="max-w-md mx-auto mt-8 text-center">
          <p className="text-gray-500 text-sm">
            🚀 Ready to modernize your codebase?
          </p>
        </div>
      </div>
    </>
  );
}
