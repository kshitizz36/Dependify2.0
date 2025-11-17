"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  CheckCircle2, 
  Sparkles, 
  Gauge, 
  Zap, 
  Code2, 
  Eye 
} from "lucide-react";

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
  badge: string;
  stats?: string;
}

const features: Feature[] = [
  {
    icon: <Sparkles className="w-6 h-6 text-purple-400" />,
    title: "AI-Explained Changelogs",
    description: "File-by-file breakdown with AI reasoning for every change. See exactly why and how code was modernized.",
    badge: "UNIQUE",
    stats: "100% transparency"
  },
  {
    icon: <CheckCircle2 className="w-6 h-6 text-green-400" />,
    title: "Multi-Language Validation",
    description: "Syntax validation across Python, JavaScript, TypeScript, Go, Rust, and Java before PR creation.",
    badge: "PRODUCTION-GRADE",
    stats: "6+ languages"
  },
  {
    icon: <Gauge className="w-6 h-6 text-blue-400" />,
    title: "Confidence Scoring",
    description: "0-100 score based on syntax validation and change complexity. Know exactly what to trust.",
    badge: "INNOVATION",
    stats: "Real-time metrics"
  },
  {
    icon: <Zap className="w-6 h-6 text-yellow-400" />,
    title: "Parallel Processing",
    description: "Process 100 files simultaneously with Modal.com. 10x faster than competitors.",
    badge: "PERFORMANCE",
    stats: "3 min for 54 files"
  },
  {
    icon: <Code2 className="w-6 h-6 text-orange-400" />,
    title: "Full Code Modernization",
    description: "Complete syntax refactoring, not just dependency updates. Modernize entire codebases.",
    badge: "CORE FEATURE",
    stats: "Beyond version bumps"
  },
  {
    icon: <Eye className="w-6 h-6 text-cyan-400" />,
    title: "Real-Time Dashboard",
    description: "Live code comparison slider with before/after syntax highlighting. Visual wow factor.",
    badge: "UX EXCELLENCE",
    stats: "Live updates"
  }
];

export default function FeaturesShowcase() {
  return (
    <div className="w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">
          🏆 What Makes Dependify Unbeatable
        </h2>
        <p className="text-gray-400">
          Six killer features that no competitor has together
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {features.map((feature, index) => (
          <Card 
            key={index}
            className="bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] border-gray-700/50 hover:border-gray-600/70 transition-all duration-300 hover:transform hover:scale-105"
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="p-2 bg-gray-800/50 rounded-lg">
                  {feature.icon}
                </div>
                <Badge variant="outline" className="text-xs border-purple-500/50 text-purple-300">
                  {feature.badge}
                </Badge>
              </div>
              <CardTitle className="text-lg text-white mt-3">
                {feature.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-400 mb-3">
                {feature.description}
              </p>
              {feature.stats && (
                <div className="flex items-center gap-2">
                  <div className="h-1 flex-1 bg-gray-700 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-purple-500 to-blue-500 w-full" />
                  </div>
                  <span className="text-xs text-gray-500">{feature.stats}</span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Competitive Advantage Section */}
      <Card className="mt-6 bg-gradient-to-br from-purple-900/20 to-blue-900/20 border-purple-700/30">
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            Competitive Advantage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-black/20 rounded-lg">
              <div className="text-3xl font-bold text-purple-400 mb-1">10x</div>
              <div className="text-sm text-gray-400">Faster Processing</div>
              <div className="text-xs text-gray-500 mt-1">vs Dependabot</div>
            </div>
            <div className="text-center p-4 bg-black/20 rounded-lg">
              <div className="text-3xl font-bold text-blue-400 mb-1">100%</div>
              <div className="text-sm text-gray-400">Syntax Validated</div>
              <div className="text-xs text-gray-500 mt-1">Zero broken PRs</div>
            </div>
            <div className="text-center p-4 bg-black/20 rounded-lg">
              <div className="text-3xl font-bold text-green-400 mb-1">6+</div>
              <div className="text-sm text-gray-400">Languages</div>
              <div className="text-xs text-gray-500 mt-1">Multi-language support</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
