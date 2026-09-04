# SENTINEL — AI-Powered Unified CCTV Intelligence & Smart Policing Platform

Sentinel is a modular, vendor-neutral CCTV intelligence platform for integrating camera systems, AI analytics, authorized watchlists, GIS, investigation workflows, and real-time alerts.

## Current scaffold

- Next.js + TypeScript frontend
- FastAPI + Python backend
- PostgreSQL + PostGIS
- Redis
- Kafka
- MediaMTX
- AI worker boundary for detection/ANPR
- Docker Compose
- API versioning
- Health endpoint

## Quick start

1. Copy `.env.example` to `.env`.
2. Start infrastructure:

```bash
docker compose up -d postgres redis kafka mediamtx
```

3. Start backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

4. Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000  
Backend API: http://localhost:8000  
Swagger: http://localhost:8000/docs

## Development order

Camera Registry → RTSP/Media Gateway → AI Detection → ANPR → Event Bus → Watchlist Correlation → Alerts → GIS → Investigation → Production hardening.

This repository is a foundation; government database integrations and production CCTV feeds must only be connected through authorized interfaces.
