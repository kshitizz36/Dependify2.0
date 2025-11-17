"use client";

import { useState, useMemo } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import SyntaxHighlighter from "react-syntax-highlighter";
import { vs2015 } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { ArrowRight } from "lucide-react";
import { Compare } from "./ui/compare";

interface CodeFile {
  name: string;
  content: string;
  description: string;
  confidence_score?: number;
  key_changes?: string[];
}

interface Comparison {
  old: CodeFile;
  new: CodeFile;
}

interface MultiFileCodeCardProps {
  files: Comparison[];
  link: string;
}

export default function MultiFileCodeCard({ files = [], link = "#" }: MultiFileCodeCardProps) {
  const [activeFile, setActiveFile] = useState(files[0]?.old?.name || "");

  // Early return if files is empty or invalid
  if (!files || !Array.isArray(files) || files.length === 0) {
    return (
      <Card className="w-full max-w-4xl bg-zinc-800 text-gray-100 border-none">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-gray-100">
            No files to display
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  const totalLines = useMemo(() => {
    if (!files || !Array.isArray(files)) return 0;
    return files.reduce(
      (acc, file) => {
        const content = file?.new?.content || "";
        return acc + content.split("\n").length;
      },
      0
    );
  }, [files]);
  


  console.log(files);

  return (
    <Card className="w-full max-w-4xl bg-zinc-800 text-gray-100 border-none">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-100">
          Code Changes
        </CardTitle>
        {/* <p className="text-sm text-gray-400">{summary}</p> */}
      </CardHeader>
      <CardContent>
        <div className="border-b ">
          <ScrollArea className="w-full whitespace-nowrap">
            <div className="flex">
              {files.map((file, index) => {
                const fileName = file?.old?.name || `file-${index}`;
                
                return (
                  <button
                    key={fileName}
                    onClick={() => setActiveFile(fileName)}
                    className={`px-4 py-2 text-sm font-medium transition-colors relative
                    ${
                      activeFile === fileName
                        ? "border-b-2 border-primary text-white"
                        : "text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    {fileName}
                  </button>
                );
              })}
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
        </div>
        <div className="mt-4">
          {files.map(
            (file) => {
              const fileName = file?.old?.name || "";
              const description = file?.old?.description || "";
              const keyChanges = file?.new?.key_changes;
              const beforeCode = file?.old?.content || "";
              const afterCode = file?.new?.content || "";
              
              return fileName === activeFile && (
                <div key={fileName}>
                  <p className="text-sm text-gray-400 mb-2">
                    {description}
                  </p>
                  
                  {keyChanges && Array.isArray(keyChanges) && keyChanges.length > 0 && (
                    <div className="mb-3 p-2 bg-blue-900/20 rounded border border-blue-700/30">
                      <p className="text-xs text-blue-300 font-semibold mb-1">Key Changes:</p>
                      <ul className="text-xs text-blue-200 space-y-1">
                        {keyChanges.map((change, idx) => (
                          <li key={idx}>{change || ''}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div className="rounded-md overflow-hidden">
                    <Compare
                      beforeCode={beforeCode}
                      afterCode={afterCode}
                      language="javascript"
                      className="h-[250px] w-[800px] md:h-[400px] md:w-[700px]"
                      slideMode="hover"
                    />
                  </div>
                </div>
              );
            }
          )}
        </div>
      </CardContent>
      <CardFooter className="flex justify-between items-center border-t border-gray-700/50 pt-4">
        <div className="flex items-center space-x-4">
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-100">{files.length}</p>
            <p className="text-sm text-gray-400">Files Changed</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-100">{totalLines}</p>
            <p className="text-sm text-gray-400">Lines Written</p>
          </div>
        </div>
        <Button className="bg-green-600 hover:bg-green-700 text-white transition-all duration-300 transform hover:scale-105" onClick={() => window.open(link, "_blank")}>
          View Pull Request
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
