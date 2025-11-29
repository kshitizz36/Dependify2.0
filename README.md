# Dependify

**Code Smarter, Not Harder.**

Dependify is an AI-powered developer tool that automates code maintenance, modernizes legacy syntax, and creates detailed pull requests with AI-explained changelogs. Stop wrestling with outdated code patterns and let Dependify bring your projects into the future—automatically.

## 🔥 The Problem: Drowning in Technical Debt

The numbers don't lie:
- **41% of developers** spend most of their time dealing with technical debt
- Developers dedicate **16.4 hours per week** to maintenance tasks like debugging and refactoring
- This constant struggle with complex, outdated code is a major contributor to **developer burnout**

Sound familiar? You're not alone.

## 💡 The Dependify Solution: AI-Powered Code Modernization

Dependify 2.0 leverages cutting-edge AI to automate the tedious aspects of code maintenance. By intelligently scanning your codebase, refactoring outdated syntax, and generating comprehensive AI-explained changelogs, Dependify transforms your maintenance backlog into a streamlined, automated workflow.

**The result?** Improved code quality, reduced technical debt, and developers who can focus on what they do best: innovate and build great software.

## ✨ What's New in 2.0

### 🎨 **GitButler-Style PR Descriptions**
- AI-generated changelogs with detailed explanations for every file
- Clear before/after comparisons showing exactly what changed and why
- Professional, readable PR descriptions that help reviewers understand the impact

### 🔄 **Smart Repository Detection**
- Automatically detects if you own the repository
- For your repos: Creates PR directly in your repository
- For others' repos: Creates a fork and submits PR from your fork
- Works seamlessly with both public and private repositories

### ⚡ **Production-Ready Deployment**
- **Frontend**: Deployed on Vercel at [dependify.vercel.app](https://dependify.vercel.app)
- **Backend**: Hosted on Render with Modal.com serverless containers
- **Authentication**: GitHub OAuth with 7-day session management
- **Real-time Updates**: Live progress tracking via Supabase

## 🚀 How It Works: Your Automated Code Modernization Workflow

### 1. **Connect Your Repository**
- Log in with GitHub OAuth
- Paste any GitHub repository URL (yours or someone else's public repo)
- Dependify handles the rest automatically

### 2. **Intelligent Code Analysis**
- Parallel processing with **Modal containers** and **Groq AI**
- Scans for outdated syntax patterns across all supported languages
- Identifies modernization opportunities with high accuracy

### 3. **AI-Powered Refactoring**
- Each file is processed independently for maximum speed
- Modern syntax patterns applied (e.g., `var` → `const/let`, class components → hooks)
- Code is validated for syntax correctness before proceeding

### 4. **Comprehensive Changelog Generation**
- AI explains **why** each change was made
- Details the **impact** of modernization
- Provides **before/after** context for reviewers

### 5. **Automated PR Creation**
- Creates a new branch with a unique identifier
- Commits all changes with detailed descriptions
- Submits pull request with full AI-generated changelog
- Handles both owned repositories and forks automatically

### 6. **Real-Time Progress Tracking**
- Live updates in the dashboard
- See exactly which files are being processed
- Get instant notifications when PR is created

## 🛠️ Tech Stack: Built for Production

We chose cutting-edge technologies to ensure Dependify 2.0 is robust, fast, and scalable:

### **Backend Infrastructure**
- **[FastAPI](https://fastapi.tiangolo.com/):** High-performance Python API with async support
- **[Modal](https://modal.com/):** Serverless containers for parallel file processing at scale
- **[Groq](https://groq.com/):** Lightning-fast AI inference (llama-3.1-8b-instant, llama-3.3-70b-versatile)
- **[Render](https://render.com/):** Reliable backend hosting with automatic deployments

### **Frontend & Real-time**
- **[Next.js 15](https://nextjs.org/):** Modern React framework with server components
- **[Supabase](https://supabase.com/):** Real-time PostgreSQL database for live updates
- **[Vercel](https://vercel.com/):** Edge-optimized frontend deployment

### **Authentication & Git**
- **[GitHub OAuth](https://docs.github.com/en/apps/oauth-apps):** Secure user authentication
- **[GitPython](https://gitpython.readthedocs.io/):** Automated git operations and PR creation

## 🎯 Current Capabilities

✅ **Fully Deployed and Working**
- Live production deployment at [dependify.vercel.app](https://dependify.vercel.app)
- GitHub OAuth authentication with session management
- Parallel processing of multiple files using Modal containers
- AI-powered code modernization with Groq inference
- Automatic PR creation with detailed changelogs
- Support for both owned and forked repositories
- Real-time progress updates via Supabase

✅ **Proven Track Record**
- Successfully modernized Microsoft's Magma repository (merged PR #63)
- Processes repositories of any size with parallel file handling
- Handles JavaScript/TypeScript, Python, and more
- Production-tested with real-world codebases

## 📊 System Architecture

```
User → Next.js Dashboard (Vercel)
         ↓
    FastAPI Backend (Render)
         ↓
    ┌────┴────┐
    ↓         ↓
Modal         GitHub API
Containers    (Fork, Clone, Push, PR)
    ↓
Groq AI
(Code Analysis)
    ↓
Supabase
(Real-time Updates)
```

## 🔧 Setup & Configuration

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.11+
- GitHub account
- API keys for Groq, Supabase, and Modal

### Environment Variables

**Frontend (.env.local)**
```bash
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_oauth_client_id
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Backend (.env)**
```bash
# AI & Processing
GROQ_API_KEY=your_groq_api_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key

# GitHub Authentication & API
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
GITHUB_TOKEN=your_github_classic_personal_access_token  # Requires 'repo' scope

# Security
API_SECRET_KEY=your_random_secret_key

# Frontend CORS
FRONTEND_URL=https://your-frontend.vercel.app
```

**Modal Secrets** (via `modal secret create`)
```bash
modal secret create GROQ_API_KEY
modal secret create SUPABASE_URL
modal secret create SUPABASE_KEY
```

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/kshitizz36/Dependify2.0.git
cd Dependify2.0
```

2. **Setup Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

3. **Setup Frontend**
```bash
cd frontend
pnpm install
pnpm dev
```

4. **Deploy Modal Containers**
```bash
cd backend
modal deploy containers.py  # For analysis
modal deploy modal_write.py  # For refactoring
```

## 📚 Key Technical Achievements

### 🚀 **Scalable Architecture**
- Modal containers handle 100+ files in parallel
- Serverless design scales automatically with load
- Efficient resource usage with container warm pools

### 🔐 **Secure Authentication**
- GitHub OAuth integration with token refresh
- 7-day session management with timestamp validation
- Secure API key handling via Modal secrets

### 🤖 **Advanced AI Integration**
- Lazy initialization pattern for Modal secrets
- Robust error handling and validation
- Structured output with Pydantic models

### 🔄 **Git Automation**
- Smart fork detection (own repo vs others)
- Authenticated clone URLs for push operations
- Automatic branch creation and PR submission

## 🔮 Roadmap: The Future of Autonomous Code Maintenance

### 🎯 **Near-Term Enhancements**
- [ ] **Multi-language Support:** Expand beyond JavaScript/TypeScript to Python, Go, Rust, and more
- [ ] **Custom Rules:** Allow users to define their own refactoring patterns
- [ ] **Batch Processing:** Process multiple repositories in one session
- [ ] **PR Templates:** Customizable changelog formats per organization

### 🧪 **Advanced Testing**
- [ ] **AI-Powered Unit Test Generation:** Automatically generate comprehensive unit tests for refactored code
- [ ] **Test Coverage Analysis:** Identify and fill gaps in your test suite
- [ ] **Regression Detection:** Verify refactored code maintains original behavior

### 🛡️ **Security & Reliability**
- [ ] **Proactive Security Audits:** AI-powered vulnerability detection and intelligent patching
- [ ] **Automated Security Updates:** Keep your dependencies secure without manual intervention
- [ ] **Breaking Change Detection:** Warn about potential breaking changes before merging

### 📝 **Documentation & Standards**
- [ ] **Intelligent Documentation Generation:** Auto-generate comprehensive docstrings and comments
- [ ] **Custom Style Enforcement:** Tailor AI refactoring to your team's coding standards and style guides
- [ ] **Migration Guides:** Generate step-by-step guides for major refactorings

## 🎯 Get Started with Dependify 2.0

Ready to reclaim your time and supercharge your codebase?

### 🚀 **Try It Now**
1. Visit **[dependify.vercel.app](https://dependify.vercel.app)**
2. Click "Continue with GitHub" to authenticate
3. Paste any GitHub repository URL
4. Watch as Dependify modernizes your code automatically!

### 📖 **Learn More**
- Read the [Setup Guide](./backend/SETUP.md) for local development
- Check out [Testing Results](./TESTING_RESULTS.md) for real-world examples
- See [Deployment Status](./DEPLOYMENT_STATUS.md) for infrastructure details

### 🤝 **Contributing**
We welcome contributions! Whether it's:
- 🐛 Bug reports and fixes
- ✨ Feature requests and implementations
- 📚 Documentation improvements
- 🎨 UI/UX enhancements

Feel free to open issues or submit pull requests.

### ⭐ **Show Your Support**
If Dependify helps improve your workflow:
- ⭐ Star this repository
- 🐦 Share it with your team
- 💬 Provide feedback through GitHub issues

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by [@kshitizz36](https://github.com/kshitizz36)
- Powered by [Modal](https://modal.com/), [Groq](https://groq.com/), [Supabase](https://supabase.com/), and [Vercel](https://vercel.com/)
- Inspired by the developer community's need for better code maintenance tools

---

*Dependify 2.0: Where AI meets code modernization. Code smarter, not harder.*

## GitAds Sponsored
[![Sponsored by GitAds](https://gitads.dev/v1/ad-serve?source=kshitizz36/dependify2.0@github)](https://gitads.dev/v1/ad-track?source=kshitizz36/dependify2.0@github)


