"use client";

import 'rsuite/dist/rsuite.min.css';
import { BsCheckCircleFill } from 'react-icons/bs';
import { useState, useEffect, useCallback } from 'react';
import { AiOutlineEnter } from "react-icons/ai";
import "rsuite/dist/rsuite.min.css";
import Image from "next/image";
import { supabase } from '../app/lib/supabaseClient';
import LiveCodeCard from './LiveCodeCard';
import MultiFileCodeCard from './MultiFileCodeCard';

// --- Interfaces ---

interface LinkedRepo {
  id?: number;
  user_id: string;
  username: string;
  repo_url: string;
  repo_name: string;
  repo_owner: string;
  language: string | null;
  linked_at?: string;
  last_score?: {
    overall_debt_score: number;
    score_grade: string;
    created_at: string;
  } | null;
}

interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  owner: string;
  html_url: string;
  clone_url: string;
  language: string | null;
  updated_at: string;
  stargazers_count: number;
  private: boolean;
}

interface MainDashProps {
  sidebarOpen: boolean;
}

// --- Enums & Helpers ---

const getStateColor = (state: string): string => {
  switch (state) {
    case 'READING': return 'text-red-500';
    case 'WRITING': return 'text-orange-500';
    case 'VERIFYING': return 'text-blue-500';
    case 'VERIFIED': return 'text-green-500';
    case 'FIXING': return 'text-purple-500';
    case 'LOADING': return 'text-yellow-500';
    default: return 'text-white';
  }
};

const getStateEmoji = (state: string): string => {
  switch (state) {
    case 'READING': return '🤓';
    case 'WRITING': return '✍️';
    case 'VERIFYING': return '🔍';
    case 'VERIFIED': return '✅';
    case 'FIXING': return '🔧';
    case 'LOADING': return '🏃‍♂️';
    default: return '🤓';
  }
};

const getScoreColor = (grade: string): string => {
  switch (grade) {
    case 'A': return 'text-green-400';
    case 'B': return 'text-green-300';
    case 'C': return 'text-yellow-400';
    case 'D': return 'text-orange-400';
    case 'F': return 'text-red-400';
    default: return 'text-gray-400';
  }
};

export interface Update {
  id: number;
  created_at: string;
  status: string;
  message: string;
  code: string | null;
}


export default function MainDash({ sidebarOpen }: MainDashProps) {
  // --- Existing state ---
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [finished, setFinished] = useState(false);
  const [updates, setUpdates] = useState<Update[]>([
    { id: 1, created_at: '2024-01-01', status: 'READING', message: 'Initializing repository scan...', code: null }
  ]);
  const [apiResponse, setApiResponse] = useState<any>(null);
  const [runStartTime, setRunStartTime] = useState<string | null>(null);

  // --- New state for linked repos ---
  const [linkedRepos, setLinkedRepos] = useState<LinkedRepo[]>([]);
  const [showRepoPicker, setShowRepoPicker] = useState(false);
  const [githubRepos, setGithubRepos] = useState<GitHubRepo[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<Set<string>>(new Set());
  const [isLoadingRepos, setIsLoadingRepos] = useState(false);
  const [isLinking, setIsLinking] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [repoSearch, setRepoSearch] = useState('');

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Get auth token from localStorage
  // Auth callback stores as 'auth_token', check both for compatibility
  const getAuthToken = useCallback((): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token') || localStorage.getItem('access_token');
  }, []);

  // Check auth on mount
  useEffect(() => {
    const token = getAuthToken();
    setIsAuthenticated(!!token);
    if (token) {
      fetchLinkedRepos(token);
    }
  }, [getAuthToken]);

  // Fetch user's linked repos from backend
  const fetchLinkedRepos = async (token: string) => {
    try {
      const resp = await fetch(`${apiUrl}/repos`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (resp.ok) {
        const data = await resp.json();
        setLinkedRepos(data.repos || []);
      }
    } catch (e) {
      console.error('Error fetching linked repos:', e);
    }
  };

  // Fetch GitHub repos for picker modal
  const fetchGitHubRepos = async () => {
    const token = getAuthToken();
    if (!token) return;
    setIsLoadingRepos(true);
    try {
      const resp = await fetch(`${apiUrl}/github/repos`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (resp.ok) {
        const data = await resp.json();
        setGithubRepos(data.repos || []);
      }
    } catch (e) {
      console.error('Error fetching GitHub repos:', e);
    } finally {
      setIsLoadingRepos(false);
    }
  };

  // Link selected repos
  const handleLinkRepos = async () => {
    const token = getAuthToken();
    if (!token || selectedRepos.size === 0) return;
    setIsLinking(true);
    try {
      const reposToLink = githubRepos
        .filter(r => selectedRepos.has(r.full_name))
        .map(r => ({
          repo_url: r.clone_url,
          repo_name: r.name,
          repo_owner: r.owner,
          language: r.language,
        }));

      const resp = await fetch(`${apiUrl}/repos/link`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repos: reposToLink }),
      });

      if (resp.ok) {
        setShowRepoPicker(false);
        setSelectedRepos(new Set());
        fetchLinkedRepos(token);
      }
    } catch (e) {
      console.error('Error linking repos:', e);
    } finally {
      setIsLinking(false);
    }
  };

  // Unlink a repo
  const handleUnlinkRepo = async (repoName: string) => {
    const token = getAuthToken();
    if (!token) return;
    try {
      await fetch(`${apiUrl}/repos/${repoName}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      fetchLinkedRepos(token);
    } catch (e) {
      console.error('Error unlinking repo:', e);
    }
  };

  // Scan state
  const [scanResult, setScanResult] = useState<any>(null);
  const [scanResultsCache, setScanResultsCache] = useState<Record<string, any>>({});
  const [isScanning, setIsScanning] = useState(false);
  const [scanningRepo, setScanningRepo] = useState<string | null>(null);
  const [showScanPanel, setShowScanPanel] = useState(false);

  // Score-only scan (no PR)
  const handleRepoScan = async (repo: LinkedRepo) => {
    const token = getAuthToken();
    setIsScanning(true);
    setScanningRepo(repo.repo_name);
    setScanResult(null);
    setShowScanPanel(true);
    try {
      const htmlUrl = `https://github.com/${repo.repo_owner}/${repo.repo_name}`;
      const resp = await fetch(`${apiUrl}/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          repository: htmlUrl,
          repository_owner: repo.repo_owner,
          repository_name: repo.repo_name,
          generate_brief: true,
        }),
      });
      const data = await resp.json();
      setScanResult(data);
      if (data.status === 'success') {
        // Cache results by repo name so clicking score reopens them
        setScanResultsCache(prev => ({ ...prev, [repo.repo_name]: data }));
        // Immediately update the score in the linked repos table (no re-fetch needed)
        setLinkedRepos(prev => prev.map(r =>
          r.repo_name === repo.repo_name
            ? {
                ...r,
                last_score: {
                  overall_debt_score: data.score?.overall_debt_score ?? 0,
                  score_grade: data.score?.score_grade ?? 'A',
                  created_at: new Date().toISOString(),
                }
              }
            : r
        ));
      }
    } catch (e) {
      console.error('Scan error:', e);
    } finally {
      setIsScanning(false);
      setScanningRepo(null);
    }
  };

  // Open cached scan results when clicking on a score
  const handleScoreClick = (repo: LinkedRepo) => {
    const cached = scanResultsCache[repo.repo_name];
    if (cached) {
      setScanResult(cached);
      setShowScanPanel(true);
    } else {
      // No cached results, trigger a new scan
      handleRepoScan(repo);
    }
  };

  // Run update on a linked repo (auto-fills URL and triggers pipeline)
  const handleRepoUpdate = (repo: LinkedRepo) => {
    const url = repo.repo_url.replace('.git', '');
    const htmlUrl = `https://github.com/${repo.repo_owner}/${repo.repo_name}`;
    setInputValue(htmlUrl);
    // Trigger the pipeline
    setIsLoading(true);
    setFinished(false);
    setRunStartTime(new Date().toISOString());
    setUpdates([{ id: 0, created_at: new Date().toISOString(), status: 'READING', message: 'Initializing repository scan...', code: null }]);

    fetch(`${apiUrl}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repository: htmlUrl,
        repository_owner: repo.repo_owner,
        repository_name: repo.repo_name,
      }),
    })
      .then(response => response.json())
      .then(data => {
        setApiResponse(data);
        if (data.output && Array.isArray(data.output)) {
          setUpdates((current) => {
            const hasData = current.some(u => u.status === 'WRITING' || u.status === 'VERIFIED');
            if (hasData) return current;
            const fallbackUpdates: Update[] = data.output.map((item: any, idx: number) => {
              const filename = item.path?.split('/').pop() || `file-${idx}`;
              return [
                { id: 1000 + idx * 2, created_at: new Date().toISOString(), status: 'READING', message: `📖 Reading ${filename}`, code: item.old_content || item.new_content || '' },
                { id: 1000 + idx * 2 + 1, created_at: new Date().toISOString(), status: 'VERIFIED', message: `✅ Verified ${filename}`, code: item.new_content || '' }
              ];
            }).flat();
            return [...current, ...fallbackUpdates];
          });
        }
        setFinished(true);
      })
      .catch((error) => console.error('Error:', error));
  };

  // Polling: fetch new rows from Supabase every 2 seconds while loading
  useEffect(() => {
    if (!isLoading || finished || !runStartTime) return;

    const poll = async () => {
      try {
        const { data, error } = await supabase
          .from('repo-updates')
          .select('*')
          .gt('created_at', runStartTime)
          .order('created_at', { ascending: true });

        if (error) { console.error('Polling error:', error); return; }
        if (data && data.length > 0) {
          setUpdates(data as Update[]);
        }
      } catch (e) {
        console.error('Polling exception:', e);
      }
    };

    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [isLoading, finished, runStartTime]);

  const isGithubUrl = (url: string) => {
    try { return new URL(url).hostname === 'github.com'; }
    catch { return false; }
  };

  const handleEnterClick = () => {
    setIsLoading(true);
    setFinished(false);
    setRunStartTime(new Date().toISOString());
    setUpdates([{ id: 0, created_at: new Date().toISOString(), status: 'READING', message: 'Initializing repository scan...', code: null }]);

    fetch(`${apiUrl}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        repository: inputValue,
        repository_owner: inputValue.split('/')[3],
        repository_name: inputValue.split('/')[4]?.replace('.git', ''),
      }),
    })
      .then(response => response.json())
      .then(data => {
        setApiResponse(data);
        if (data.output && Array.isArray(data.output)) {
          setUpdates((current) => {
            const hasData = current.some(u => u.status === 'WRITING' || u.status === 'VERIFIED');
            if (hasData) return current;
            const fallbackUpdates: Update[] = data.output.map((item: any, idx: number) => {
              const filename = item.path?.split('/').pop() || `file-${idx}`;
              return [
                { id: 1000 + idx * 2, created_at: new Date().toISOString(), status: 'READING', message: `📖 Reading ${filename}`, code: item.old_content || item.new_content || '' },
                { id: 1000 + idx * 2 + 1, created_at: new Date().toISOString(), status: 'VERIFIED', message: `✅ Verified ${filename}`, code: item.new_content || '' }
              ];
            }).flat();
            return [...current, ...fallbackUpdates];
          });
        }
        setFinished(true);
      })
      .catch((error) => console.error('Error:', error));
  };

  // Toggle repo selection in picker
  const toggleRepoSelection = (fullName: string) => {
    setSelectedRepos(prev => {
      const next = new Set(prev);
      if (next.has(fullName)) next.delete(fullName);
      else next.add(fullName);
      return next;
    });
  };

  // Filter GitHub repos by search
  const filteredGithubRepos = githubRepos.filter(r =>
    r.name.toLowerCase().includes(repoSearch.toLowerCase()) ||
    r.full_name.toLowerCase().includes(repoSearch.toLowerCase())
  );

  // Already linked repo names (to grey them out in picker)
  const linkedRepoNames = new Set(linkedRepos.map(r => `${r.repo_owner}/${r.repo_name}`));

  return (
    <div className={`flex-1 p-8 transition-all duration-300 ${sidebarOpen ? 'ml-40' : 'ml-0'}`}>
      <h1 className="text-3xl font-bold text-white mb-20">Dashboard</h1>

      {/* Search Bar - Manual URL input */}
      <div className={`relative max-w-xl mx-auto transition-all duration-300 ${isGithubUrl(inputValue) ? 'h-20' : 'h-12'} ${isLoading ? 'mb-0' : 'mb-10'}`}>
        {!finished && (
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && isGithubUrl(inputValue)) handleEnterClick();
            }}
            disabled={isLoading}
            className="w-full bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] text-white rounded-full py-5 pl-12 pr-12 border border-gray-700/50 focus:outline-none focus:border-gray-600 placeholder-gray-400 disabled:opacity-75 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(255,255,255,0.1)] focus:shadow-[0_0_20px_rgba(255,255,255,0.2)] transition-shadow duration-300"
            placeholder="Insert a Github repository URL"
          />
        )}
        {isGithubUrl(inputValue) && !isLoading && (
          <>
            <div className="absolute inset-y-0 right-5 top-5 flex items-start pointer-events-none">
              <BsCheckCircleFill className="w-5 h-5 text-green-500" />
            </div>
            <div className="flex justify-end px-4 mt-4">
              <button
                onClick={handleEnterClick}
                className="flex items-center gap-2 text-white bg-[rgba(60,60,60,0.8)] px-4 py-1.5 rounded-md hover:bg-[rgba(75,75,75,0.8)]"
              >
                <span>Enter</span>
                <AiOutlineEnter className="w-4 h-4" />
              </button>
            </div>
          </>
        )}
      </div>

      {/* Results - Code Comparison */}
      {finished && (
        <div className="max-w-5xl mx-auto">
          <div className="bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] rounded-[20px] p-16 mb-8 border border-gray-700/50">
            <MultiFileCodeCard
              files={(() => {
                const extractFilename = (msg: string) => {
                  const match = msg.match(/(?:📖|✍️|🔍|✅|🔧)\s*(?:Reading|Updating|Verifying|Verified|Analyzing & fixing|Fixing)\s+(.+?)(?:\s*\(|\s|$)/);
                  if (match) return match[1].trim();
                  const parts = msg.split(' ');
                  return parts[1]?.replace("...", "") || 'unknown';
                };

                const verifiedUpdates = updates.filter((u) => u.status === 'VERIFIED');
                const writingUpdates = updates.filter((u) => u.status === 'WRITING');
                const finalUpdates = verifiedUpdates.length > 0 ? verifiedUpdates : writingUpdates;

                return finalUpdates.map((update) => {
                  const filename = extractFilename(update.message);
                  const oldCode = updates.find((u) => {
                    return extractFilename(u.message) === filename && u.status === 'READING';
                  });
                  return {
                    old: { name: filename, content: oldCode?.code || "", description: oldCode?.message || update.message },
                    new: { name: filename, content: update.code || "", description: verifiedUpdates.length > 0 ? `✅ Verified: ${filename}` : update.message }
                  };
                });
              })()}
              link={inputValue.replace(".git", "") + "/pulls"}
            />
          </div>
        </div>
      )}

      {/* Loading / Processing State */}
      {isLoading && !finished && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] rounded-[20px] p-16 mb-8 border border-gray-700/50">
            {/* Phase Indicator */}
            <div className="flex items-center justify-center gap-3 mb-8">
              {[
                { label: 'Reading', statuses: ['READING'], emoji: '🤓' },
                { label: 'Writing', statuses: ['WRITING'], emoji: '✍️' },
                { label: 'Verifying', statuses: ['VERIFYING', 'FIXING', 'VERIFIED'], emoji: '🔍' },
              ].map((phase, idx) => {
                const latestStatus = updates[updates.length - 1]?.status;
                const isActive = phase.statuses.includes(latestStatus);
                const isPast = (() => {
                  const phaseOrder = ['READING', 'WRITING', 'VERIFYING'];
                  const currentPhaseIdx = phaseOrder.findIndex(p => phase.statuses.includes(p));
                  const latestPhaseIdx = phaseOrder.findIndex(p => {
                    const ph = [{ statuses: ['READING'] }, { statuses: ['WRITING'] }, { statuses: ['VERIFYING', 'FIXING', 'VERIFIED'] }];
                    return ph[phaseOrder.indexOf(p)]?.statuses.includes(latestStatus);
                  });
                  return currentPhaseIdx < latestPhaseIdx;
                })();
                return (
                  <div key={phase.label} className="flex items-center gap-3">
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-500 ${
                      isActive ? 'bg-white/10 border border-white/30 scale-110'
                        : isPast ? 'bg-green-500/10 border border-green-500/30'
                        : 'bg-white/5 border border-white/10 opacity-40'
                    }`}>
                      <span className="text-lg">{isPast ? '✅' : phase.emoji}</span>
                      <span className={`text-sm font-medium ${isActive ? 'text-white' : isPast ? 'text-green-400' : 'text-gray-500'}`}>{phase.label}</span>
                      {isActive && <div className="w-2 h-2 bg-white rounded-full animate-pulse" />}
                    </div>
                    {idx < 2 && <div className={`w-8 h-[2px] ${isPast ? 'bg-green-500/50' : 'bg-white/10'}`} />}
                  </div>
                );
              })}
            </div>

            <div className="flex flex-col items-center justify-center space-y-4">
              <div className="flex flex-col items-center">
                <span className="text-4xl">{getStateEmoji(updates[updates.length - 1].status)}</span>
                <div className="animate-blur-in">
                  <div
                    className={`absolute inset-7 -m-12 opacity-30 blur-2xl rounded-full ${getStateColor(updates[updates.length - 1].status)}`}
                    style={{ background: `radial-gradient(ellipse, currentColor 0%, transparent 65%)` }}
                  />
                </div>
                <div className="relative h-8 overflow-hidden" />
              </div>

              <LiveCodeCard
                filename={(() => {
                  const msg = updates[updates.length - 1].message;
                  const match = msg.match(/(?:📖|✍️|🔍|✅|🔧)\s*(?:Reading|Updating|Verifying|Verified|Analyzing & fixing|Fixing)\s+(.+?)(?:\s*\(|\s|$)/);
                  if (match) return match[1].trim();
                  const parts = msg.split(' ');
                  return parts[1]?.replace("...", "") || 'processing...';
                })()}
                language="javascript"
                finalCode={updates[updates.length - 1].code || ""}
                typingSpeed={2}
                message={updates[updates.length - 1].message}
              />
            </div>
          </div>
        </div>
      )}

      {/* Linked Repositories Table */}
      <div className="relative bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] rounded-[20px] p-6 mb-8 border border-gray-700/50">
        <div className="top-[-110px] right-[20px] absolute h-[110px] transition-all pt-12 duration-500 hover:pt-8 opacity-75 hover:filter-none overflow-hidden filter">
          <Image src="/pou-transparent-cropped.png" width="110" height="600" alt="Pou is sad." />
        </div>
        <div className="w-full overflow-x-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl text-white">Linked Repositories</h2>
            {isAuthenticated && (
              <button
                onClick={() => { setShowRepoPicker(true); fetchGitHubRepos(); }}
                className="px-4 py-2 bg-green-600/80 hover:bg-green-500/80 text-white rounded-lg text-sm font-medium transition-colors"
              >
                + Add Repository
              </button>
            )}
          </div>

          {!isAuthenticated ? (
            <div className="text-center py-8">
              <p className="text-gray-400 mb-3">Connect your GitHub account to link repositories</p>
              <a
                href="/login"
                className="inline-block px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm font-medium transition-colors border border-white/20"
              >
                Login with GitHub
              </a>
            </div>
          ) : linkedRepos.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400 mb-3">No repositories linked yet</p>
              <p className="text-gray-500 text-sm">Click &quot;+ Add Repository&quot; to get started</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="px-4 py-3 text-left font-medium">NAME</th>
                  <th className="px-4 py-3 text-left font-medium">LANGUAGE</th>
                  <th className="px-4 py-3 text-left font-medium">DEBT SCORE</th>
                  <th className="px-4 py-3 text-left font-medium">LINKED</th>
                  <th className="px-4 py-3 text-left font-medium">ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {linkedRepos.map((repo) => (
                  <tr key={repo.repo_url} className="border-b border-gray-700/50 hover:bg-gray-800/50">
                    <td className="px-4 py-4">
                      <div>
                        <span className="text-white font-medium">{repo.repo_name}</span>
                        <span className="text-gray-500 text-sm ml-2">{repo.repo_owner}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-gray-300 text-sm">{repo.language || '—'}</span>
                    </td>
                    <td className="px-4 py-4">
                      {repo.last_score ? (
                        <button
                          onClick={() => handleScoreClick(repo)}
                          className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
                          title="Click to view scan details"
                        >
                          <span className={`text-lg font-bold ${getScoreColor(repo.last_score.score_grade)}`}>
                            {repo.last_score.score_grade}
                          </span>
                          <span className="text-gray-400 text-sm">{repo.last_score.overall_debt_score}/100</span>
                          <span className="text-gray-600 text-xs">&#9654;</span>
                        </button>
                      ) : (
                        <span className="text-gray-500 text-sm">Not scanned</span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-gray-400 text-sm">
                      {repo.linked_at ? new Date(repo.linked_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleRepoScan(repo)}
                          disabled={isScanning || isLoading}
                          className="px-4 py-1.5 bg-blue-600/80 hover:bg-blue-500/80 disabled:opacity-50 rounded text-sm text-white font-medium transition-colors"
                        >
                          {scanningRepo === repo.repo_name ? 'Scanning...' : 'Scan'}
                        </button>
                        <button
                          onClick={() => handleRepoUpdate(repo)}
                          disabled={isLoading || isScanning}
                          className="px-4 py-1.5 bg-green-600/80 hover:bg-green-500/80 disabled:opacity-50 rounded text-sm text-white font-medium transition-colors"
                        >
                          Update
                        </button>
                        <button
                          onClick={() => handleUnlinkRepo(repo.repo_name)}
                          className="px-4 py-1.5 bg-gray-800/80 hover:bg-red-600/60 rounded text-sm text-gray-300 hover:text-white transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Scanning Indicator */}
      {isScanning && showScanPanel && !scanResult && (
        <div className="relative bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] rounded-[20px] p-6 mb-8 border border-gray-700/50">
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-white font-medium">Scanning {scanningRepo}...</p>
            <p className="text-gray-400 text-sm">Analyzing files for security, vulnerabilities, and code health</p>
          </div>
        </div>
      )}

      {/* Scan Results Panel */}
      {showScanPanel && scanResult && scanResult.status === 'success' && (
        <div className="relative bg-[rgba(30,30,30,0.8)] backdrop-blur-[50px] rounded-[20px] p-6 mb-8 border border-gray-700/50">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-xl text-white font-bold">Scan Results</h2>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-gray-500 text-xs">
                  Last scanned: {scanResult.run_id ? new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Unknown'}
                  {scanResult.repository && <span className="ml-2 text-gray-600">| {scanResult.repository.split('/').slice(-1)[0]}</span>}
                </p>
                {scanResult.learning_context && (
                  <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">Tuned scan</span>
                )}
              </div>
            </div>
            <button onClick={() => setShowScanPanel(false)} className="text-gray-400 hover:text-white text-xl">&times;</button>
          </div>

          {/* Score Card */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800/60 rounded-xl p-4 text-center">
              <div className={`text-4xl font-bold ${getScoreColor(scanResult.score?.score_grade || 'A')}`}>
                {scanResult.score?.score_grade || 'A'}
              </div>
              <div className="text-gray-400 text-sm mt-1">Grade</div>
              <div className="text-gray-500 text-xs">{scanResult.score?.overall_debt_score || 0}/100 debt</div>
            </div>
            <div className="bg-gray-800/60 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-white">{scanResult.files_analyzed || 0}</div>
              <div className="text-gray-400 text-sm mt-1">Files Analyzed</div>
            </div>
            <div className="bg-gray-800/60 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-orange-400">{scanResult.files_with_issues || 0}</div>
              <div className="text-gray-400 text-sm mt-1">Files with Issues</div>
            </div>
            <div className="bg-gray-800/60 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-red-400">{scanResult.total_findings || 0}</div>
              <div className="text-gray-400 text-sm mt-1">Total Findings</div>
            </div>
          </div>

          {/* Severity Breakdown */}
          <div className="flex gap-3 mb-6">
            {scanResult.findings_by_severity?.critical > 0 && (
              <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm font-medium">
                {scanResult.findings_by_severity.critical} Critical
              </span>
            )}
            {scanResult.findings_by_severity?.high > 0 && (
              <span className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded-full text-sm font-medium">
                {scanResult.findings_by_severity.high} High
              </span>
            )}
            {scanResult.findings_by_severity?.medium > 0 && (
              <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-sm font-medium">
                {scanResult.findings_by_severity.medium} Medium
              </span>
            )}
            {scanResult.findings_by_severity?.low > 0 && (
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm font-medium">
                {scanResult.findings_by_severity.low} Low
              </span>
            )}
          </div>

          {/* File Risk Heatmap (simplified list) */}
          {scanResult.file_scores && scanResult.file_scores.length > 0 && (
            <div className="mb-6">
              <h3 className="text-white font-medium mb-3">File Risk Scores</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {scanResult.file_scores.map((fs: any, idx: number) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-gray-300 text-sm font-mono truncate">{fs.file}</span>
                        <span className="text-gray-400 text-xs">{fs.issues} issues</span>
                      </div>
                      <div className="w-full bg-gray-700/50 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            fs.score >= 70 ? 'bg-red-500' : fs.score >= 40 ? 'bg-orange-500' : fs.score >= 20 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(fs.score, 100)}%` }}
                        />
                      </div>
                    </div>
                    <span className={`text-sm font-bold min-w-[40px] text-right ${
                      fs.score >= 70 ? 'text-red-400' : fs.score >= 40 ? 'text-orange-400' : fs.score >= 20 ? 'text-yellow-400' : 'text-green-400'
                    }`}>
                      {fs.score}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Blast Radius */}
          {scanResult.blast_radius && scanResult.blast_radius.total_affected_files > 0 && (
            <div className="mb-6 bg-gray-800/40 rounded-xl p-4">
              <h3 className="text-white font-medium mb-3">Blast Radius</h3>
              <div className="flex gap-4 mb-3">
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">{scanResult.blast_radius.total_affected_files}</div>
                  <div className="text-gray-400 text-xs">Affected Files</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-400">{scanResult.blast_radius.high_risk_changes || 0}</div>
                  <div className="text-gray-400 text-xs">High Risk</div>
                </div>
              </div>
              {scanResult.blast_radius.per_file?.filter((f: any) => f.dependent_count > 0).slice(0, 5).map((f: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-1 text-sm">
                  <span className="text-gray-300 font-mono truncate">{f.file}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    f.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                    f.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'
                  }`}>
                    {f.dependent_count} dependents
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Dependency Analysis */}
          {scanResult.dep_analysis && scanResult.dep_analysis.total_findings > 0 && (
            <div className="mb-6 bg-gray-800/40 rounded-xl p-4">
              <h3 className="text-white font-medium mb-3">Dependency Risks</h3>
              <div className="flex gap-2 mb-3">
                {scanResult.dep_analysis.by_severity?.critical > 0 && (
                  <span className="px-2 py-0.5 bg-red-500/20 text-red-400 rounded text-xs">{scanResult.dep_analysis.by_severity.critical} critical</span>
                )}
                {scanResult.dep_analysis.by_severity?.high > 0 && (
                  <span className="px-2 py-0.5 bg-orange-500/20 text-orange-400 rounded text-xs">{scanResult.dep_analysis.by_severity.high} high</span>
                )}
                {scanResult.dep_analysis.by_severity?.medium > 0 && (
                  <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-xs">{scanResult.dep_analysis.by_severity.medium} medium</span>
                )}
              </div>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {scanResult.dep_analysis.findings?.slice(0, 8).map((f: any, i: number) => (
                  <div key={i} className="text-sm">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-xs mr-2 ${
                      f.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                      f.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>{f.type}</span>
                    <span className="text-gray-300">{f.description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Repo Intelligence Brief */}
          {scanResult.brief && !scanResult.brief.error && (
            <div className="border-t border-gray-700/50 pt-4">
              <h3 className="text-white font-medium mb-3">Repo Intelligence Brief</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {scanResult.brief.architecture && (
                  <div className="bg-gray-800/40 rounded-lg p-3">
                    <span className="text-gray-400 text-xs uppercase">Architecture</span>
                    <p className="text-white text-sm mt-1">{scanResult.brief.architecture}</p>
                  </div>
                )}
                {scanResult.brief.frameworks && scanResult.brief.frameworks.length > 0 && (
                  <div className="bg-gray-800/40 rounded-lg p-3">
                    <span className="text-gray-400 text-xs uppercase">Frameworks</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {scanResult.brief.frameworks.map((fw: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-700/60 text-gray-300 rounded text-xs">{fw}</span>
                      ))}
                    </div>
                  </div>
                )}
                {scanResult.brief.test_coverage_estimate && (
                  <div className="bg-gray-800/40 rounded-lg p-3">
                    <span className="text-gray-400 text-xs uppercase">Test Coverage</span>
                    <p className={`text-sm mt-1 ${
                      scanResult.brief.test_coverage_estimate === 'high' ? 'text-green-400' :
                      scanResult.brief.test_coverage_estimate === 'medium' ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {scanResult.brief.test_coverage_estimate}
                    </p>
                  </div>
                )}
                {scanResult.brief.setup_hint && (
                  <div className="bg-gray-800/40 rounded-lg p-3">
                    <span className="text-gray-400 text-xs uppercase">Setup</span>
                    <p className="text-gray-300 text-sm mt-1 font-mono">{scanResult.brief.setup_hint}</p>
                  </div>
                )}
              </div>
              {scanResult.brief.onboarding_summary && (
                <div className="bg-gray-800/40 rounded-lg p-3 mt-3">
                  <span className="text-gray-400 text-xs uppercase">Onboarding Summary</span>
                  <p className="text-gray-300 text-sm mt-1 leading-relaxed">{scanResult.brief.onboarding_summary}</p>
                </div>
              )}
              {scanResult.brief.risky_hotspots && scanResult.brief.risky_hotspots.length > 0 && (
                <div className="bg-gray-800/40 rounded-lg p-3 mt-3">
                  <span className="text-gray-400 text-xs uppercase">Risky Hotspots</span>
                  <ul className="mt-1 space-y-1">
                    {scanResult.brief.risky_hotspots.map((hs: string, i: number) => (
                      <li key={i} className="text-orange-300 text-sm font-mono">{hs}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Repo Picker Modal */}
      {showRepoPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-[rgba(30,30,30,0.95)] backdrop-blur-[50px] rounded-[20px] p-6 border border-gray-700/50 w-full max-w-2xl max-h-[80vh] flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl text-white font-bold">Add Repositories</h2>
              <button onClick={() => setShowRepoPicker(false)} className="text-gray-400 hover:text-white text-2xl">&times;</button>
            </div>

            {/* Search */}
            <input
              type="text"
              value={repoSearch}
              onChange={(e) => setRepoSearch(e.target.value)}
              placeholder="Search repositories..."
              className="w-full bg-gray-800/80 text-white rounded-lg py-2 px-4 mb-4 border border-gray-700/50 focus:outline-none focus:border-gray-600 placeholder-gray-500"
            />

            {/* Repo List */}
            <div className="flex-1 overflow-y-auto min-h-0 space-y-1">
              {isLoadingRepos ? (
                <div className="text-center py-8 text-gray-400">Loading your repositories...</div>
              ) : filteredGithubRepos.length === 0 ? (
                <div className="text-center py-8 text-gray-400">No repositories found</div>
              ) : (
                filteredGithubRepos.map((repo) => {
                  const isLinked = linkedRepoNames.has(repo.full_name);
                  const isSelected = selectedRepos.has(repo.full_name);
                  return (
                    <div
                      key={repo.id}
                      onClick={() => !isLinked && toggleRepoSelection(repo.full_name)}
                      className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                        isLinked ? 'opacity-40 cursor-not-allowed' :
                        isSelected ? 'bg-green-600/20 border border-green-500/30' :
                        'hover:bg-gray-800/80'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={isSelected || isLinked}
                          disabled={isLinked}
                          onChange={() => {}}
                          className="rounded bg-gray-700/50 border-gray-600"
                        />
                        <div>
                          <span className="text-white font-medium">{repo.name}</span>
                          {repo.private && <span className="ml-2 text-xs text-yellow-400 bg-yellow-400/10 px-1.5 py-0.5 rounded">private</span>}
                          {isLinked && <span className="ml-2 text-xs text-green-400">already linked</span>}
                        </div>
                      </div>
                      <div className="flex items-center gap-3 text-sm text-gray-400">
                        {repo.language && <span className="bg-gray-800 px-2 py-0.5 rounded">{repo.language}</span>}
                        {repo.stargazers_count > 0 && <span>⭐ {repo.stargazers_count}</span>}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-700/50">
              <span className="text-gray-400 text-sm">
                {selectedRepos.size} selected
              </span>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowRepoPicker(false)}
                  className="px-4 py-2 bg-gray-800/80 hover:bg-gray-700/80 text-gray-300 rounded-lg text-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={handleLinkRepos}
                  disabled={selectedRepos.size === 0 || isLinking}
                  className="px-6 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  {isLinking ? 'Linking...' : `Link ${selectedRepos.size} Repos`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
