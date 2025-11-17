"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import GradientCanvas from "@/components/GradientCanvas";

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const error = searchParams.get("error");

      if (error) {
        setStatus("error");
        setErrorMessage("Authentication was cancelled or failed");
        setTimeout(() => router.push("/login"), 3000);
        return;
      }

      if (!code) {
        setStatus("error");
        setErrorMessage("No authorization code received");
        setTimeout(() => router.push("/login"), 3000);
        return;
      }

      try {
        // Call backend to exchange code for token
        const response = await fetch("http://localhost:5001/auth/github", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ code }),
        });

        if (!response.ok) {
          throw new Error("Failed to authenticate");
        }

        const data = await response.json();

        // Store token in localStorage
        localStorage.setItem("auth_token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.user));

        setStatus("success");

        // Redirect to dashboard
        setTimeout(() => router.push("/"), 1500);
      } catch (error) {
        console.error("Authentication error:", error);
        setStatus("error");
        setErrorMessage("Failed to complete authentication");
        setTimeout(() => router.push("/login"), 3000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

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
        <div className="relative bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] rounded-[24px] border border-gray-700/50 p-8 shadow-2xl text-center max-w-md w-full">
          {status === "loading" && (
            <div className="space-y-6">
              <div className="flex justify-center">
                <div className="w-16 h-16 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Authenticating...
                </h2>
                <p className="text-gray-400">
                  Please wait while we verify your credentials
                </p>
              </div>
            </div>
          )}

          {status === "success" && (
            <div className="space-y-6">
              <div className="flex justify-center">
                <div className="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-white"
                    fill="none"
                    strokeWidth="3"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Success!
                </h2>
                <p className="text-gray-400">
                  Redirecting to your dashboard...
                </p>
              </div>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-6">
              <div className="flex justify-center">
                <div className="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-white"
                    fill="none"
                    strokeWidth="3"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </div>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Authentication Failed
                </h2>
                <p className="text-gray-400">{errorMessage}</p>
                <p className="text-gray-500 text-sm mt-2">
                  Redirecting to login page...
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
