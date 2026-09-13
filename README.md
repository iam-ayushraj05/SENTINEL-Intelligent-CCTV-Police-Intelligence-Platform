# 🛡️ SENTINEL — Intelligent CCTV & Police Command Platform

**SENTINEL** is a state-of-the-art, vendor-neutral CCTV intelligence and smart policing platform designed for state police command centres (built for Gujarat Police Innovation Hackathon 2026). It unifies heterogeneous surveillance infrastructure, correlates AI detection events across multiple camera nodes, tracks suspect vehicle/person trajectories, and automates emergency response workflows.

> **From Fragmented Cameras to Unified Command Intelligence.**

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────────────┐
                               │     CDN / RTSP / Local CCTV Feeds      │
                               └───────────────────┬────────────────────┘
                                                   │
                                                   ▼
 ┌──────────────────────┐              ┌────────────────────────┐
 │   Next.js 14 Web     │◄────────────►│     FastAPI Backend    │
 │   Command Centre     │   REST/WS    │    (Python 3.11/Async) │
 └──────────┬───────────┘              └───────────┬────────────┘
            │                                      │
            ▼                                      ▼
 ┌──────────────────────┐              ┌────────────────────────┐
 │  HLS Video Proxy &   │              │ PostgreSQL / SQLite DB │
 │  Mux Fallback Stream │              │ & Correlation Engine   │
 └──────────────────────┘              └────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **🌐 GIS Surveillance Map** | Interactive vector GIS map displaying all live CCTV nodes, active alerts, and suspect vehicle route trajectories. |
| **📹 Multi-Camera Video Wall** | Real-time multi-camera monitoring with automatic grid layout scaling (`2×2`, `3×3`, `4×4`, `Slide`). |
| **⚡ Live HLS Proxy & Fallback** | Low-latency HLS media proxy server with automated fallbacks to 30 named Gujarat Police CCTV streams. |
| **🚗 ANPR Vehicle Intelligence** | Automatic Number Plate Recognition (ANPR) with license plate tracking, VAHAN lookup, and trajectory mapping. |
| **🔗 Multi-Camera Event Correlation**| Cross-camera event fusion engine that groups detections across cameras into unified Emergency Cases (`CASE-1000000X`). |
| **🚨 Emergency Case Management** | Case lifecycle tracking (`OPEN` ➔ `ACKNOWLEDGED` ➔ `IN_PROGRESS` ➔ `RESOLVED` ➔ `CLOSED`), timeline, and ambulance dispatch. |
| **🛡️ RBAC & Audit Logging** | Immutable audit logs tracking all camera stream accesses, searches, and document downloads for compliance. |

---

## ⚡ Quick Start

### 1. Prerequisites
- **Node.js**: v18+ or v20+
- **Python**: v3.10+ or v3.11+
- **Docker** *(optional for database & services)*

### 2. Environment Configuration
Clone the repository and prepare environment files:

```bash
# Clone repository
git clone https://github.com/iam-ayushraj05/SENTINEL-Intelligent-CCTV-Police-Intelligence-Platform.git
cd SENTINEL

# Copy environment examples
cp .env.example .env
cp frontend/.env.local .env.local
```

### 3. Start Backend Server
```bash
cd backend

# Create & activate Python virtual environment
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
> Backend API: `http://localhost:8000/api/v1`  
> Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 4. Start Frontend Application
In a new terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
> Web Application: `http://localhost:3000`

---

## 📡 API Endpoints Overview

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/cameras` | `GET` | List all active CCTV camera nodes with GIS coordinates & statuses |
| `/api/cctv/stream/{id}/index.m3u8` | `GET` | HLS video stream proxy endpoint |
| `/api/v1/detections/ingest` | `POST` | Batch ingest AI object detections and ANPR plate sightings |
| `/api/v1/emergency/correlate` | `POST` | Correlate multi-camera detection events into unified Emergency Cases |
| `/api/v1/vehicles/{plate}` | `GET` | Retrieve ANPR vehicle intelligence, sightings history, & route trajectory |
| `/api/v1/alerts` | `GET` | Fetch active alerts with severity filtering |
| `/api/v1/audit-logs` | `GET` | View system audit trail logs |

---

## 🚀 Production Deployment Guide

### Option 1: Docker Compose (Full Stack)
```bash
docker-compose up -d
```

### Option 2: Managed Cloud Services
- **Frontend**: Deploy `frontend/` to **Vercel** (`NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1`).
- **Backend**: Deploy `backend/` to **Render** / **AWS App Runner** / **Railway**.
- **Database**: Managed PostgreSQL with PostGIS extension (e.g. Supabase, Render Postgres).

---

## 🔒 Policy & Safety Note

This project includes synthetic surveillance data for demonstration and evaluation purposes during the Gujarat Police Innovation Hackathon 2026. All live CCTV streams fall back gracefully to public test video streams when external CDN credentials are absent. No actual police records or private surveillance feeds are exposed.

---

## 📄 License

Developed for the **Gujarat Police Innovation Hackathon 2026**. All rights reserved.
