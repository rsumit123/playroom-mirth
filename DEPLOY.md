# Charade Chat - Deployment Guide

## Infrastructure

| Component | URL | Hosted On |
|-----------|-----|-----------|
| Frontend | https://charade-chat.skdev.one | Vercel (project: `charade-chat`) |
| Backend API | https://charade-api.skdev.one | GCP VM (Docker + nginx) |
| Database | SQLite | GCP VM at `/app/data/charade.db` (volume-mounted) |

## Frontend Deployment (Vercel)

The frontend auto-deploys when commits are pushed to `main` on GitHub.

### Automatic (push to GitHub)

```bash
# From repo root
git add frontend/
git commit -m "feat: your change description"
git push origin main
```

Vercel will pick up the push and build automatically.

### Manual (if auto-deploy doesn't trigger)

```bash
# Trigger a redeploy of the latest main branch via Vercel CLI
cd /path/to/charade-chat
npx vercel link --yes --project charade-chat
npx vercel --prod
```

Or trigger via Vercel dashboard: Deployments > ... > Redeploy.

### Environment Variables (Vercel)

Set in Vercel project settings (or via CLI):

| Variable | Value | Scope |
|----------|-------|-------|
| `VITE_API_BASE` | `https://charade-api.skdev.one` | Production |
| `VITE_SOCKET_URL` | `https://charade-api.skdev.one` | Production |

```bash
# To update via CLI
npx vercel link --yes --project charade-chat
echo "https://charade-api.skdev.one" | npx vercel env add VITE_API_BASE production
echo "https://charade-api.skdev.one" | npx vercel env add VITE_SOCKET_URL production
```

## Backend Deployment (GCP VM)

### SSH Access

```bash
ssh-social
```

### Deploy Steps

```bash
# 1. SSH into the VM
ssh-social

# 2. Navigate to the project
cd charade-chat

# 3. Pull latest changes
git pull origin main

# 4. Rebuild and restart the container
docker compose build
docker compose up -d --force-recreate

# 5. Verify it's running
docker logs charade-backend --tail 10
curl -s -o /dev/null -w '%{http_code}' https://charade-api.skdev.one/docs
```

> **After the October 2026 history rewrite**, the VM's clone cannot fast-forward.
> Run this once on the VM instead of `git pull`:
> `cd ~/charade-chat && git fetch origin && git reset --hard origin/main`

### One-liner (from local machine)

```bash
ssh-social -- "cd charade-chat && git pull origin main && docker compose build && docker compose up -d --force-recreate"
```

### Docker Compose Config

- **Container**: `charade-backend`
- **Port**: 8005 (internal) -> 8005 (host)
- **Volume**: `./backend/data:/app/data` (persists SQLite DB)
- **Environment**:
  - `DATABASE_URL=sqlite:///./data/charade.db`
  - `JWT_SECRET_KEY` (set via env or defaults to `dev-secret-change`)

### Nginx Config

Located at `/etc/nginx/sites-available/charade-api.skdev.one`.

Proxies `https://charade-api.skdev.one` -> `http://localhost:8005` with WebSocket support.

SSL managed by Certbot (auto-renews).

```bash
# Test nginx config after changes
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### CORS Origins

If the frontend domain changes, update `backend/app/main.py` `allow_origins` list and redeploy the backend.

Current allowed origins:
- `http://localhost:5173` (local dev)
- `http://localhost:5175` (local dev)
- `https://charade-chat.skdev.one` (production)
- `https://frontend-ashen-alpha-57.vercel.app` (Vercel default)

## DNS Records (Namecheap)

| Type | Host | Value |
|------|------|-------|
| A | `charade-api` | `34.23.158.39` (GCP VM IP) |
| CNAME | `charade-chat` | `cname.vercel-dns.com.` |

## Troubleshooting

### Backend container won't start
```bash
# Check logs
docker logs charade-backend

# Check disk space (common issue on the small VM)
df -h /
# If full, clean up:
sudo journalctl --vacuum-size=50M
docker system prune -f
```

### SSL certificate issues
```bash
# Renew manually
sudo certbot renew

# Check cert status
sudo certbot certificates
```

### Verify end-to-end
```bash
# Backend health
curl https://charade-api.skdev.one/docs

# Frontend serving
curl -s -o /dev/null -w '%{http_code}' https://charade-chat.skdev.one

# Other projects still working
curl -s -o /dev/null -w '%{http_code}' https://willow-api.skdev.one
curl -s -o /dev/null -w '%{http_code}' https://chillbill-api.skdev.one
```
