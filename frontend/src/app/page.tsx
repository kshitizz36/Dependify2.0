"use client";

import { useState, useEffect } from "react";
import Image from "next/image";

import GradientCanvas from "@/components/GradientCanvas";
import MainDash from "@/components/MainDash";
import LandingPage from "@/components/LandingPage";

import { Animation } from "rsuite";
import "rsuite/dist/rsuite.min.css";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  // Check auth on mount
  useEffect(() => {
    const token = localStorage.getItem("auth_token") || localStorage.getItem("access_token");
    setIsAuthenticated(!!token);
    setIsChecking(false);
  }, []);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  const theme = {
    gradientColor1: "#023601",
    gradientColor2: "#1b4332",
    gradientColor3: "#000000",
  };

  // Show nothing while checking auth
  if (isChecking) return null;

  // Show landing page for non-authenticated users (owns its own bg)
  if (!isAuthenticated) {
    return <LandingPage />;
  }

  // Dashboard for authenticated users
  return (
    <>
      <GradientCanvas
        gradientColor1={theme.gradientColor1}
        gradientColor2={theme.gradientColor2}
        gradientColor3={theme.gradientColor3}
      />
      <div className="min-h-screen flex">
        <aside
          className={`fixed left-0 top-0 h-full bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] text-white p-4 transform transition-transform duration-300 border border-gray-700/50 rounded-r-[20px] z-40 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          } sm:w-40`}
        >
          <h2 className="text-xl font-bold mb-4">Dependify</h2>
          <ul>
            {[
              { text: "Dashboard", icon: "/layout-dashboard.svg", page: "dashboard" },
            ].map((item, index) => (
              <li key={index} className="mb-2">
                <button
                  onClick={() => setCurrentPage(item.page)}
                  className={`flex items-center p-2 rounded-lg transition duration-200 hover:bg-gray-800 w-full ${
                    currentPage === item.page ? "bg-gray-800" : ""
                  }`}
                >
                  <Image
                    src={item.icon}
                    width={24}
                    height={24}
                    className="mr-2 invert"
                    alt={`${item.text} Icon`}
                  />
                  {item.text}
                </button>
              </li>
            ))}
            <li className="mt-4 pt-4 border-t border-gray-700/50">
              <button
                onClick={() => {
                  localStorage.removeItem("auth_token");
                  localStorage.removeItem("access_token");
                  localStorage.removeItem("user");
                  setIsAuthenticated(false);
                }}
                className="flex items-center p-2 rounded-lg transition duration-200 hover:bg-red-900/30 w-full text-gray-400 hover:text-red-400 text-sm"
              >
                Logout
              </button>
            </li>
          </ul>
        </aside>

        <Animation.Slide in={true} placement="left" unmountOnExit>
          <MainDash sidebarOpen={sidebarOpen} />
        </Animation.Slide>

        <button
          onClick={toggleSidebar}
          className="fixed bottom-4 left-4 bg-gray-800 text-white px-3 py-2 rounded-md shadow-lg transition-transform duration-300 z-50"
        >
          {sidebarOpen ? (
            <Image src="/arrow-left-from-line.svg" width={24} height={24} className="invert" alt="Close Sidebar" />
          ) : (
            <Image src="/arrow-right-from-line.svg" width={24} height={24} className="invert" alt="Open Sidebar" />
          )}
        </button>
      </div>
    </>
  );
}
