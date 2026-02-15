# Dependify 2.0 Backend Setup Guide

This guide will help you set up the Dependify backend with all required credentials and configurations.

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- GitHub account
- Modal account (for serverless containers)
- Supabase account (for real-time database)
- Groq API account (for LLM processing)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Now edit the `.env` file and fill in your credentials (see detailed instructions below).

### 3. Run the Server

```bash
python server.py
```

The server will start on `http://localhost:5000`

---

## 🔑 Getting Your API Keys

### Groq API Key

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create API Key"
5. Copy the key and add to `.env`:
   ```
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```

### Supabase Credentials

1. Go to [https://supabase.com](https://supabase.com)
2. Create a new project or select existing one
3. Go to "Settings" → "API"
4. Copy the following:
   - **Project URL**: Add to `.env` as `SUPABASE_URL`
   - **Service Role Key**: Add to `.env` as `SUPABASE_KEY`

   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_service_role_key_here
   ```

5. Set up the database table:
   ```sql
   CREATE TABLE "repo-updates" (
     id BIGSERIAL PRIMARY KEY,
     status TEXT,
     message TEXT,
     code TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

### GitHub Token

1. Go to [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "Dependify Bot"
4. Select these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `write:packages` (if you use GitHub Packages)
5. Click "Generate token"
6. Copy the token and add to `.env`:
   ```
   GITHUB_TOKEN=ghp_your_github_token_here
   ```

### GitHub OAuth (for User Authentication)

1. Go to [https://github.com/settings/developers](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - **Application name**: Dependify
   - **Homepage URL**: `http://localhost:3000` (or your frontend URL)
   - **Authorization callback URL**: `http://localhost:3000/auth/callback`
4. Click "Register application"
5. Copy the "Client ID" and generate a "Client Secret"
6. Add to `.env`:
   ```
   GITHUB_CLIENT_ID=your_client_id_here
   GITHUB_CLIENT_SECRET=your_client_secret_here
   ```

### Modal Configuration

1. Install Modal CLI:
   ```bash
   pip install modal
   ```

2. Log in to Modal:
   ```bash
   modal token new
   ```

3. Create Modal secrets:
   ```bash
   modal secret create GROQ_API_KEY GROQ_API_KEY=your_groq_key_here
   modal secret create SUPABASE_URL SUPABASE_URL=your_supabase_url_here
   modal secret create SUPABASE_KEY SUPABASE_KEY=your_supabase_key_here
   ```

### API Secret Key (for JWT)

Generate a secure random secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to `.env`:
```
API_SECRET_KEY=your_generated_secret_here
```

### Optional: Anthropic API (if using Claude instead of Groq)

1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Add to `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-your_key_here
   ```

---

## ⚙️ Configuration Options

### Frontend URL

Update this to match your frontend deployment:

```env
# Development
FRONTEND_URL=http://localhost:3000

# Production
FRONTEND_URL=https://your-app.vercel.app
```

### Rate Limiting

Adjust these based on your needs:

```env
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

### Server Port

```env
PORT=5000
```

---

## 🧪 Testing the Setup

### 1. Health Check

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "message": "Dependify API is running"
}
```

### 2. Test Modal Containers

```bash
# Test the reading container
modal run containers.py::run_script --repo-url https://github.com/your-test/repo.git

# Test the writing container
modal run modal_write.py
```

### 3. API Documentation

Visit `http://localhost:5000/docs` to see the interactive API documentation.

---

## 🔒 Security Checklist

Before deploying to production:

- [ ] All API keys are in `.env` file (not hardcoded)
- [ ] `.env` file is in `.gitignore`
- [ ] Rotated any exposed credentials from git history
- [ ] GitHub token has minimum required permissions
- [ ] Using Supabase Service Role key (not anon key) in backend
- [ ] CORS is restricted to your frontend domain
- [ ] API Secret Key is strong and random
- [ ] Rate limiting is configured appropriately

---

## 🐛 Troubleshooting

### "Missing required environment variables"

Make sure all required variables in `.env.example` are filled in your `.env` file.

### "GITHUB_TOKEN not configured"

Check that your GitHub token is:
- Valid and not expired
- Has the `repo` scope
- Properly added to `.env` file

### "Modal authentication failed"

Run `modal token new` to re-authenticate with Modal.

### "Supabase connection error"

Verify:
- Supabase project is running
- URL and key are correct
- `repo-updates` table exists

### Port already in use

Change the PORT in `.env` or kill the process using port 5000:

```bash
# Find process
lsof -i :5000

# Kill process
kill -9 <PID>
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Modal Documentation](https://modal.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Groq API Documentation](https://console.groq.com/docs)
- [GitHub API Documentation](https://docs.github.com/en/rest)

---

## 🆘 Need Help?

If you encounter issues:

1. Check the logs for error messages
2. Verify all environment variables are set correctly
3. Ensure dependencies are installed: `pip install -r requirements.txt`
4. Open an issue on [GitHub](https://github.com/kshitizz36/Dependify2.0/issues)

---

**🎉 You're all set! Your Dependify backend is ready to modernize code.**
