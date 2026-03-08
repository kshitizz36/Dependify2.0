"use client";

import { useState } from "react";
import Image from "next/image";

import GradientCanvas from "@/components/GradientCanvas";
import MainDash from "@/components/MainDash";

import { Animation } from "rsuite";
import "rsuite/dist/rsuite.min.css";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState("dashboard");

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  // Add a simple theme object
  const theme = {
    gradientColor1: "#023601", // Deep forest green
    gradientColor2: "#1b4332", // Dark forest green
    gradientColor3: "#000000", // Black
  };

  const renderContent = () => {
    switch (currentPage) {
      case "dashboard":
        return (
          <MainDash
            sidebarOpen={sidebarOpen}
          />
        );

      default:
        return null;
    }
  };

  return (
    <>
      <GradientCanvas
        gradientColor1={theme.gradientColor1}
        gradientColor2={theme.gradientColor2}
        gradientColor3={theme.gradientColor3}
      />
      <div className="min-h-screen flex">
        {/* Sidebar */}
        <aside
          className={`fixed left-0 top-0 h-full bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] text-white p-4 transform transition-transform duration-300 border border-gray-700/50 rounded-r-[20px] ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          } sm:w-40`}
          style={{
            fontFamily:
              "-apple-system, BlinkMacSystemFont, system-ui, sans-serif",
          }}
        >
          <h2 className="text-xl font-bold mb-4">Dependify</h2>
          <ul>
            {[
              { text: "Profile", icon: "/user-round.svg", page: "profile" },
              {
                text: "Dashboard",
                icon: "/layout-dashboard.svg",
                page: "dashboard",
              },
              {
                text: "Repository",
                icon: "/git-branch.svg",
                page: "repository",
              },
              { text: "Settings", icon: "/settings.svg", page: "settings" },
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
          </ul>
        </aside>

        {/* Single Animation.Slide wrapper */}
        <Animation.Slide
          in={true}
          placement={currentPage === "dashboard" ? "left" : "right"}
          unmountOnExit
        >
          {renderContent()}
        </Animation.Slide>

        {/* Toggle Button */}
        <button
          onClick={toggleSidebar}
          className="fixed bottom-4 left-4 bg-gray-800 text-white px-3 py-2 rounded-md shadow-lg transition-transform duration-300"
        >
          {sidebarOpen ? (
            <Image
              src="/arrow-left-from-line.svg"
              width={24}
              height={24}
              className="invert"
              alt="Close Sidebar"
            />
          ) : (
            <Image
              src="/arrow-right-from-line.svg"
              width={24}
              height={24}
              className="invert"
              alt="Open Sidebar"
            />
          )}
        </button>
      </div>
    </>
  );
}
