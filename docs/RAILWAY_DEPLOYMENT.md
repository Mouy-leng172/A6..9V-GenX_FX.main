# 🚢 Railway Deployment Guide

This guide provides step-by-step instructions for deploying the GenX_FX Trading System to [Railway](https://railway.com?referralCode=AHRe-w).

## 📋 Prerequisites

- A Railway account. If you don't have one, you can [sign up here](https://railway.com?referralCode=AHRe-w).
- GitHub repository with the GenX_FX source code.
- Required API keys (FXCM, Bybit, etc.) for live trading features.

## 🚀 Quick Deploy

1.  **Connect your Repository**: Log in to Railway and click "New Project" -> "Deploy from GitHub repo".
2.  **Configure Environment Variables**: Railway will automatically detect the `app.json` file and prompt you for the required environment variables.
3.  **Automatic Build**: Railway uses the Nixpacks builder (as configured in `railway.json`) to build and deploy both the Node.js frontend/proxy and the Python backend.

## ⚙️ Manual Configuration

If you prefer to configure the project manually, ensure the following settings are applied:

### Build & Deploy Settings
- **Builder**: Nixpacks
- **Start Command**: `npm run start:prod`
- **Port**: Railway automatically sets the `PORT` environment variable. The Node.js server listens on this port and proxies API requests to the Python backend.

### Environment Variables
The following variables should be set in the Railway dashboard:

| Variable | Description | Required |
|----------|-------------|----------|
| `NODE_ENV` | Set to `production` | Yes |
| `SECRET_KEY` | Secret key for session/cookie security | Yes |
| `JWT_SECRET` | Secret key for JWT tokens | Yes |
| `FXCM_ACCESS_TOKEN` | Your FXCM API access token | No |
| `BYBIT_API_KEY` | Your Bybit API key | No |
| `BYBIT_API_SECRET` | Your Bybit API secret | No |
| `DATABASE_URL` | PostgreSQL or other database URL | No |

## 📊 Monitoring

Once deployed, you can access the following:
- **Web Dashboard**: `https://your-project-name.up.railway.app/`
- **API Health**: `https://your-project-name.up.railway.app/health`
- **System Monitor**: `https://your-project-name.up.railway.app/monitor`

## 🤝 Referral Program

Support the project by using our referral link when signing up for Railway:
[https://railway.com?referralCode=AHRe-w](https://railway.com?referralCode=AHRe-w)

---
**Last Updated**: 2026-02-04
