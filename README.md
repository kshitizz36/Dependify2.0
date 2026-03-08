# Dependify

**AI-powered code health remediation. Scan, fix, verify, ship.**

Dependify autonomously finds security flaws, outdated code, and tech debt in your repositories — then fixes them, verifies the changes compile and pass tests, and opens a PR. No manual triage.

## How it works

```
Scan → Fix → Verify → PR
```

1. **Reader** (Claude Sonnet) — Clones your repo, scans every file for security vulnerabilities, outdated patterns, dependency risks, and maintainability issues. Returns structured findings with evidence chains and confidence scores.

2. **Writer** (Claude Haiku) — Takes each finding, rewrites the code. Blast-radius aware — won't break exports used by other files. Processes up to 100 files in parallel.

3. **Verifier** (Haiku + Sonnet) — 3-tier verification loop. Haiku checks the fix, Sonnet diagnoses failures, Haiku corrects. Sandbox runs your build and tests in an isolated container. Ships only when green.

## What it scans for

- **Security** — SQL injection, XSS, hardcoded secrets, command injection, insecure crypto
- **Vulnerabilities** — Dangerous dependency patterns, eval/exec usage, insecure deserialization
- **Outdated code** — Deprecated APIs, legacy syntax, removed library methods
- **Maintainability** — High complexity, missing error handling, deep nesting
- **Dependencies** — Install scripts, URL-based deps, behavioral analysis

## Key features

- **Deterministic scoring** — Debt score (A–F) computed from findings without LLM. Same inputs = same score.
- **Blast radius analysis** — Import graph builder knows which files depend on which. Writer agent preserves exports for high-dependent files.
- **Sandbox verification** — Modal container runs build/test/lint before any PR is created. Unsafe = blocked.
- **Repo intelligence** — Architecture brief, API route detection, complexity hotspots, env var mapping, setup hints. Understand a new codebase in 60 seconds.
- **Threat modeling** — Entry points, sensitive sinks, data flow analysis with missing protections.
- **Learning loop** — Tracks which PRs your team merges or rejects. Future scans prioritize what you actually fix.
- **Fleet health** — Org-wide dashboard across all linked repos with aggregate scoring.

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, Tailwind CSS, Supabase Realtime |
| Backend | FastAPI (Python) |
| Compute | Modal serverless containers |
| LLMs | Claude Sonnet 4 (scan/analyze), Claude Haiku 4.5 (write/verify) |
| Database | Supabase (PostgreSQL) |
| Hosting | Vercel (frontend), Modal (agents) |

## Architecture

```
Browser → Next.js (Vercel) → FastAPI Backend → Modal Containers
                                    ↕
                              Supabase (DB + Realtime)
```

**Modal apps:** `claude-read` (Reader), `claude-write` (Writer), `claude-verify` (Verifier), `dependify-sandbox` (Safety gate)

## API

| Endpoint | What |
|----------|------|
| `POST /scan` | Score-only scan — findings + score, no PR |
| `POST /update` | Full pipeline — scan → fix → verify → sandbox → PR |
| `GET /repos/{name}/onboard` | Full onboarding: brief + API routes + complexity + env vars |
| `GET /repos/{name}/threat-model` | Entry points, sinks, data flows |
| `GET /repos/{name}/evolution` | Commit history analysis, churn hotspots |
| `GET /fleet/health` | Org-wide repo health dashboard |

## Status

Private beta. [Request access](https://dependify2-0.vercel.app).
