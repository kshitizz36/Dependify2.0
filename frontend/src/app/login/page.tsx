"use client";

import { useState } from "react";
import Image from "next/image";
import GradientCanvas from "@/components/GradientCanvas";

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);

  const handleGitHubLogin = () => {
    setIsLoading(true);
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID || "";
    const redirectUri = `${window.location.origin}/auth/callback`;
    const scope = "repo,user";

    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
  };

  const theme = {
    gradientColor1: "#023601",
    gradientColor2: "#1b4332",
    gradientColor3: "#000000",
  };

  return (
    <>
      <GradientCanvas
        gradientColor1={theme.gradientColor1}
        gradientColor2={theme.gradientColor2}
        gradientColor3={theme.gradientColor3}
      />
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="relative w-full max-w-md">
          <div className="relative bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] rounded-[24px] border border-gray-700/50 p-8 shadow-2xl">
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <Image
                    src="/pou-transparent-cropped.png"
                    alt="Dependify Mascot"
                    width={96}
                    height={96}
                    className="object-contain"
                  />
                </div>
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Welcome to Dependify
              </h1>
              <p className="text-gray-400 text-sm">
                AI-powered code health remediation
              </p>
            </div>

            <button
              onClick={handleGitHubLogin}
              disabled={isLoading}
              className="w-full bg-white hover:bg-gray-100 text-gray-900 font-semibold py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
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

            <div className="mt-6 text-center">
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

          <div className="absolute -top-10 -left-10 w-40 h-40 bg-green-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-green-500/10 rounded-full blur-3xl" />
        </div>
      </div>
    </>
  );
}
