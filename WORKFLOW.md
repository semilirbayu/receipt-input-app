# Simple Development Workflow

Quick guide for solo development with staging and production branches.

---

## 🌿 Branch Structure

```
main      → Production (auto-deploys to Render)
staging   → Pre-production testing
feature/* → Your active development work
```

---

## 🚀 Daily Workflow

### 1. Start New Feature

```bash
# Always branch from staging
git checkout staging
git pull origin staging

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Develop & Test Locally

```bash
# Make your changes
# Test locally: uvicorn frontend.src.main:app --reload

# Commit when ready
git add .
git commit -m "Add feature X"
git push origin feature/your-feature-name
```

### 3. Merge to Staging

```bash
# Switch to staging
git checkout staging
git pull origin staging

# Merge your feature
git merge feature/your-feature-name

# Push to remote
git push origin staging

# Optional: Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

### 4. Deploy to Production

```bash
# When staging is stable, merge to main
git checkout main
git pull origin main

# Merge staging
git merge staging

# Push → triggers Render deployment
git push origin main
```

---

## 🔒 GitHub Branch Protection (One-Time Setup)

Protect main branch from accidental pushes:

### Steps:

1. **Go to GitHub repository**
   - Navigate to your repo: `github.com/semilirbayu/receipt-input-app`

2. **Open Settings**
   - Click **Settings** tab (top right)

3. **Add Branch Protection**
   - Left sidebar → **Branches**
   - Click **Add branch protection rule**

4. **Configure Protection**
   ```
   Branch name pattern: main

   ✅ Require a pull request before merging
      ✅ Require approvals: 1
      ✅ Allow specified actors to bypass pull request requirements
         → Add yourself (semilirbayu)

   ✅ Require status checks to pass before merging (optional)

   ⬜ Require conversation resolution before merging (optional)

   ✅ Do not allow bypassing the above settings
   ```

5. **Save Changes**
   - Scroll down → Click **Create**

### What This Does:

- ✅ Prevents direct pushes to `main` (forces you to use PRs)
- ✅ Requires 1 approval (you can approve your own PRs as solo dev)
- ✅ Forces you to review changes before production deploy
- ✅ You can still bypass in emergencies

---

## 📝 Local Environment Setup

Keep your local development config separate from production:

### Create .env.local (Already Gitignored!)

```bash
# Copy from .env
cp .env .env.local

# Edit for local development
nano .env.local
```

**Example .env.local:**
```bash
# Local development config
GOOGLE_CLIENT_ID=your-local-or-test-client-id
GOOGLE_CLIENT_SECRET=your-local-secret
REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
SECRET_KEY=local-dev-secret-key
GEMINI_API_KEY=your-test-api-key

# Local settings
UPLOAD_DIR=shared/uploads
MAX_FILE_SIZE_MB=5
ALLOWED_ORIGINS=http://localhost:8000

# Optional: Use different Google Sheets for testing
# (Create a test spreadsheet so you don't pollute production data)
```

### Using .env.local

```bash
# Run with local config
export $(cat .env.local | xargs)
uvicorn frontend.src.main:app --reload --port 8000
```

---

## 🛠️ Common Scenarios

### Fix Bug in Production

```bash
# Branch from main (current production)
git checkout main
git pull origin main
git checkout -b hotfix/bug-name

# Fix the bug, test locally
# ...

# Merge directly to main (skip staging for critical fixes)
git checkout main
git merge hotfix/bug-name
git push origin main

# Also merge to staging to keep it in sync
git checkout staging
git merge hotfix/bug-name
git push origin staging
```

### Rollback Production

```bash
# Find the last good commit
git log --oneline

# Revert to that commit (creates new commit)
git revert <commit-hash>
git push origin main

# Render auto-deploys the rollback
```

### Keep Staging in Sync with Main

```bash
# Periodically merge main back to staging
git checkout staging
git merge main
git push origin staging
```

---

## ⚡ Quick Reference

| Task | Command |
|------|---------|
| Start feature | `git checkout -b feature/name staging` |
| Test locally | `uvicorn frontend.src.main:app --reload` |
| Merge to staging | `git checkout staging && git merge feature/name` |
| Deploy to prod | `git checkout main && git merge staging && git push` |
| Check current branch | `git branch` |
| Rollback | `git revert <commit>` |

---

## 📊 Branch Status

See what's deployed where:

```bash
# Check main (production)
git checkout main
git log --oneline -3

# Check staging
git checkout staging
git log --oneline -3

# See what's in staging but not in main
git log main..staging --oneline
```

---

## 🎯 Best Practices

### ✅ DO:
- Always branch from `staging` for new features
- Test locally before pushing
- Write clear commit messages
- Keep `main` stable (production-ready)
- Use branch protection on `main`

### ❌ DON'T:
- Don't commit directly to `main` (use PRs)
- Don't commit `.env` files (already gitignored)
- Don't push untested code to `staging`
- Don't merge `staging` to `main` if staging is broken

---

## 🔄 When to Add More

Start simple. Add these later when needed:

- **GitHub Actions** - When you want automated testing
- **PR Previews** - When you have a team reviewing PRs
- **Separate staging server** - When you need persistent staging environment
- **Automated deployments** - When manual merges feel tedious

---

**Created:** 2025-10-10
**For:** Solo development on receipt-input-app
