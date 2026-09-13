# SENTINEL — Unified CCTV Intelligence & Smart Policing Platform

SENTINEL is a modular, vendor-neutral CCTV intelligence platform built to unify fragmented surveillance infrastructure across Gujarat departments, correlate detections with authorized watchlists, and support real-time investigation workflows.

> From Fragmented Cameras to Unified Intelligence.

## Platform purpose

SENTINEL integrates:

- heterogeneous CCTV infrastructure
- GIS-based camera registry
- AI analytics and ANPR
- vehicle/person detection and tracking
- event correlation and watchlist matching
- operational alerts and investigation workflows
- camera health, auditability, and role-based access control

The repository is structured as a production-oriented PoC foundation for the Gujarat Police Innovation Hackathon 2026, designed to scale toward a statewide network of approximately 80,000 cameras.

## Demo safety and policy

This project includes demo data and synthetic surveillance scenarios for product demonstration and testing.

- All demo records are clearly labeled as SYNTHETIC DEMO DATA.
- No real government feed, database, or live police data is claimed.
- Government database integrations are implemented as authorized adapter interfaces only.

## Current implementation scope

- Next.js + TypeScript command-centre frontend
- FastAPI backend with versioned API routes
- PostgreSQL + PostGIS-ready models
- Redis caching and state management
- Kafka/event bus foundation
- MediaMTX stream gateway integration boundary
- AI worker and detection boundaries
- Docker Compose local infrastructure stack
- Health, dashboard, camera, vehicle, alert, watchlist, and investigation APIs

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

fix
Backend API: http://localhost:8000  
Swagger: htt:800p://localhost0/docs

### AI camera worker (Windows PowerShell)

Install the backend requirements in the project virtual environment, then configure one authorized camera stream before starting the worker:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:AI_CAMERA_ID = "your-camera-id"
$env:AI_STREAM_URL = "your-camera-stream-url"
$env:AI_CATALOGUE_URL = "http://localhost:8000/api/v1/cameras/ingest"
$env:AI_FACE_DETECTION_ENABLED = "true"
cd ..
python ai\worker.py
```

The configured local camera feed resolves the YouTube source `https://www.youtube.com/watch?v=Jlvh_KxHl40` through `/api/v1/feeds/local-camera-video`. Set `LOCAL_CAMERA_YOUTUBE_URL=` to disable YouTube and use the local MP4 at `LOCAL_CAMERA_VIDEO_PATH` instead. YouTube media URLs are temporary and may expire; `yt-dlp` must be installed in the backend environment.

Face detection uses the OpenCV cascade bundled with the installed package when available. The repository Caffe model is the fallback and can be relocated with `AI_FACE_MODEL_DIR`; a custom cascade can be supplied with `AI_FACE_CASCADE_PATH`. Face detection identifies face regions only; identity matching requires a separate recognition service and is not inferred by this detector.

For live RTSP cameras, the worker prefers `AI_CATALOGUE_URL`, reads the camera's RTSP URL from that catalogue, forces FFmpeg RTSP transport over TCP, preserves `CAP_PROP_POS_MSEC` timestamps, and reconnects with 2/4/8/16/30 second backoff. Browser previews must use the catalogue's WebRTC/WHEP or HLS URL; RTSP is never opened directly by the browser.

## Target operational flow

CCTV → INGESTION → AI → ANPR → TRACKING → WATCHLIST → CORRELATION → ALERT → GIS → INVESTIGATION → REPORT

## Development order

Camera Registry → RTSP/Media Gateway → AI Detection → ANPR → Event Bus → Watchlist Correlation → Alerts → GIS → Investigation → Production hardening.

## Important implementation note

This repository is the foundation for the SENTINEL proof of concept. Government database integrations, production CCTV feeds, and live surveillance access must be connected only through authorized interfaces, with strict RBAC and audit controls.
