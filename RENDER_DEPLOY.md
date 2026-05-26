# Render Deployment Plan — Carmen OpenClaw Gateway
# Date: 2026-05-26
# Goal: Chuyển OpenClaw Gateway từ Mac local lên Render 24/7

## Phase 1: Chuẩn bị (NOW)
- [x] Audit workspace size → ~5MB data thực, 610MB browser sessions (bỏ)
- [x] Audit dependencies → Python (pyswisseph, yfinance, pandas, numpy), Node (playwright), ffmpeg
- [ ] Tạo Dockerfile custom
- [ ] Tạo render.yaml
- [ ] Tạo migration script
- [ ] Clean workspace (bỏ sessions, __pycache__, output cũ)

## Phase 2: Deploy (khi Kim Ssa ready)
- [ ] Push code lên GitHub repo (hoặc Render có thể pull từ repo)
- [ ] Deploy Blueprint trên Render
- [ ] Set environment variables
- [ ] Migrate workspace files lên persistent disk
- [ ] Verify health check

## Phase 3: Post-deploy
- [ ] Update Telegram webhook → Render URL
- [ ] Update UptimeRobot → Render /health
- [ ] Verify cron jobs hoạt động
- [ ] Test full pipeline (Patreon gen → post, X/Meta, YouTube Shorts)

## Key Settings
| Item | Value |
|------|-------|
| Render plan | Starter ($7/mo) |
| Disk | 1GB (đủ cho OS + deps + 5MB data + headroom) |
| Port | 8080 (Render default) |
| Health check | /health |
| Auth | Token (auto-generate hoặc re-use) |
