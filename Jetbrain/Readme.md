📖 Unified README – Jules / GenX FX

🚀 Overview
Jules is a multi‑agent trading environment combining:
- Python FastAPI backend (trading bot, risk daemon)
- Node.js scheduler for tasks
- React dashboard for monitoring
- MT4/MT5 EA integration for execution
- Docker Compose orchestration for reproducible environments
- VSCode + JetBrains configs for seamless development

---

🖥️ Environment Setup
- Install Python 3.11+, Node.js 18+, Docker, and GitHub CLI (gh)
- Clone repo:
  `bash
  git clone https://github.com/Mouy-leng172/A6..9V-GenX_FX.main
  cd A6..9V-GenX_FX.main
  `

---

🐳 Docker Deployment
- Build and run Jules:
  `bash
  docker-compose up --build
  `
- Override for production:
  `bash
  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  `

---

⚙️ VSCode Integration
- .vscode/launch.json → Debug Jules locally or in Docker
- .vscode/tasks.json → Run GitHub workflows, Docker Compose, and agents
- Example:
  - Run Jules Bot (Local) → Python trading bot
  - Debug Jules Scheduler (Local) → Node.js scheduler
  - Launch Jules in Docker → Containerized bot
  - Run All Agents → Orchestrator script

---

🧩 JetBrains Integration
- Drop configs into .idea/runConfigurations/
- Files:
  - Jules.xml → Local + Docker Run/Debug configs
  - JulesDockerCompose.xml → Docker Compose orchestration
- Run/Debug dropdown will show:
  - Run Jules Bot (Local)
  - Debug Jules Scheduler
  - Launch Jules in Docker
  - Run All Agents
  - Jules Docker Compose
  - Agents Docker Compose

---

🐙 GitHub Workflows
- Trigger CI/CD pipelines from VSCode or JetBrains terminal:
  `bash
  gh workflow run deploy.yml
  `
- Workflows include:
  - Lint + Tests
  - Docker Build + Push
  - Deployment to Cloud (Railway/Vercel/AWS)

---

📊 Monitoring
- Prometheus + Grafana integration recommended
- Dashboards: monitoring-dashboard.json and monitoring_dashboard.html

---

🛡️ Security & Compliance
- Secrets managed via .env (local) or Vault/AWS Secrets Manager (production)
- Audit logs: append‑only, stored in logs/audit/
- Compliance: Tier III/IV data center alignment

---

🧪 Testing
- Run unit tests:
  `bash
  pytest tests/
  `
- Run backtests:
  `bash
  python scripts/backtest.py --config config/backtest.json
  `

---
