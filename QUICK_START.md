# 🚀 SENTINEL — Quick Start & Verification Guide

This guide will help you set up, run, and verify **SENTINEL** locally in under 3 minutes.

---

## 📋 Prerequisites

- **Node.js** v18+ (`node -v`)
- **Python** v3.10+ (`python --version`)
- **Git** (`git --version`)

---

## ⚡ 1-Minute Local Setup

### Step 1: Start the Backend (Port 8000)

```bash
cd backend

# Create & activate virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start backend API
uvicorn app.main:app --reload --port 8000
```

Verify backend health:
```bash
curl http://localhost:8000/health
```
*(Expected response: `{"status":"ok", ...}`)*

---

### Step 2: Start the Frontend (Port 3000)

Open a second terminal window:

```bash
cd frontend

# Install Node modules
npm install

# Start Next.js server
npm run dev
```

Open your browser to: **`http://localhost:3000`**

---

## 🧪 Verifying Key Features

### 1. CCTV Video Wall & Live Streams (`/cameras`)
- Navigate to `http://localhost:3000/cameras`.
- Click on any camera card or switch grid layouts (`2×2`, `3×3`, `4×4`) to view active HLS video streams.

### 2. Multi-Camera Intelligence View (`/emergency-cameras`)
- Navigate to `http://localhost:3000/emergency-cameras`.
- View all 30 Gujarat Police CCTV nodes on the interactive GIS Map.
- Touch or click any camera node in the feed list — watch its pin highlight on the map with an animated blue pulse ring while streaming live video below!

### 3. ANPR Vehicle Intelligence (`/vehicles`)
- Navigate to `http://localhost:3000/vehicles`.
- Search for plate number `GJ05CD5678` to view the vehicle's historical sightings timeline, VAHAN registry details, and GIS route trajectory.

### 4. Emergency Case Management (`/emergency`)
- Navigate to `http://localhost:3000/emergency`.
- View active emergency cases (`CASE-1000000X`), timeline updates, ambulance dispatch status, and audit logs.

---

## 🛠️ Testing API Endpoints via cURL

### Ingest AI Detection & ANPR Sightings
```bash
curl -X POST "http://localhost:8000/api/v1/detections/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "cam01",
    "detections": [
      {"object_type": "person", "confidence": 0.95, "bbox": {"x1": 100, "y1": 100, "x2": 200, "y2": 300}}
    ],
    "events": [
      {"camera_id": "cam01", "event_type": "SUSPICIOUS_ACTIVITY", "confidence": 0.88}
    ]
  }'
```

### Trigger Multi-Camera Correlation
```bash
curl -X POST "http://localhost:8000/api/v1/emergency/correlate" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_events": [
      {"camera_id": "cam01", "event_type": "ANPR_WATCHLIST_HIT", "timestamp": "2026-09-13T23:00:00Z"},
      {"camera_id": "cam02", "event_type": "WEAPON_DETECTED", "timestamp": "2026-09-13T23:02:00Z"}
    ]
  }'
```

---

## 🛠️ Deployment Summary

To build the production bundle for deployment:

```bash
# Frontend production build check
cd frontend
npm run build
npm run start

# Backend production test
cd backend
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```
