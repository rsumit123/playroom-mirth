---
name: deploy
description: Build, test, and deploy to Vercel (frontend) and/or GCP (backend). Specify "frontend", "backend", or "all" (default).
argument-hint: <frontend|backend|all>
user-invocable: true
---

# Deploy Workflow

Deploy the Charade Chat application to production. Target: `$ARGUMENTS` (default: "all").

## Step 1: Run Full Test Suite

Before deploying anything, run tests to ensure nothing is broken.

### Backend tests:
```bash
cd /Users/rsumit123/work/charade-chat/backend && .venv/bin/python -m pytest --tb=short -q
```

### Frontend build check:
```bash
cd /Users/rsumit123/work/charade-chat/frontend && npm run build
```

If any tests fail or the build breaks, STOP and report the failures. Do not deploy broken code.

## Step 2: Deploy Backend (if target is "backend" or "all")

1. Push latest code to git (confirm with user first)
2. Deploy to GCP VM:

```bash
gcloud compute ssh socialflow --project=polar-pillar-450607-b7 --zone=us-east1-d -- "cd charade-chat && git stash 2>/dev/null; git pull origin main && export GOOGLE_CLIENT_ID='929006071236-55m4f4gujp7nnu9ldirbkrmr4qn30ng1.apps.googleusercontent.com' && cd backend && docker compose down && docker compose up --build -d"
```

3. Verify backend is running:
```bash
curl -s https://charade-api.skdev.one/health | head -20
```

## Step 3: Deploy Frontend (if target is "frontend" or "all")

1. Build with production env vars:
```bash
cd /Users/rsumit123/work/charade-chat/frontend && VITE_API_BASE=https://charade-api.skdev.one VITE_SOCKET_URL=https://charade-api.skdev.one VITE_GOOGLE_CLIENT_ID=929006071236-55m4f4gujp7nnu9ldirbkrmr4qn30ng1.apps.googleusercontent.com npm run build
```

2. Deploy to Vercel:
```bash
cd /Users/rsumit123/work/charade-chat/frontend && npx vercel --prod
```

3. Verify frontend is live:
```bash
curl -s -o /dev/null -w "%{http_code}" https://playroom.skdev.one
```

## Step 4: Report

Print a summary:
```
Deployment Summary
==================
Backend:  [deployed/skipped] - https://charade-api.skdev.one
Frontend: [deployed/skipped] - https://playroom.skdev.one
Tests:    [X/X passing]
Status:   [success/failed]
```
