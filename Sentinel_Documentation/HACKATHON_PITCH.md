# SENTINEL — Gujarat Police Hackathon Problem Statement Solution

## Project Name: SENTINEL — AI-Powered Unified CCTV Intelligence & Smart Policing Platform
**Problem Statement:** Gujarat Police Sentinel Challenge — Unified CCTV Systems Integration & Database Correlation  

---

## Executive Summary & Hackathon Pitch

**SENTINEL** is an enterprise-grade operational Command Center prototype designed to solve the critical challenges in statewide policing:
1. **Fragmentation of CCTV Infrastructure:** Integrates disparate CCTV systems (ANPR, PTZ, Fixed, multi-vendor cameras) under a unified RTSP/MediaMTX stream gateway.
2. **Automated AI Intelligence:** Employs real-time YOLOv8 object detection, ByteTrack tracking, and ANPR plate character normalization (correcting OCR misreads like O->0, I->1, Z->2).
3. **Authorized Database Correlation:** Cross-references live ANPR plate sightings in real-time with authorized government databases (VAHAN registry and Police FIR crime records).
4. **Actionable Real-time Alerting:** Instant WebSocket alert fanout to command operators with evidence frame hashing and automated incident escalation into investigation case files.
5. **Tactical GIS Command Interface:** Full operational command console with live camera stream player, AI bounding box overlays, reconstructed vehicle trajectory maps, and Prometheus system telemetry.

---

## Key Technical Achievements

- **Real-Time WebSockets:** Automated event simulator continuously emits AI detections and ANPR sightings to command screens without page refresh.
- **Robust Resilience:** Both backend and frontend include graceful fallback handling and demo simulation modes so the platform is always runnable and demonstration-ready.
- **Full Operational Workflows:** Real buttons, working API endpoints, SQLite/PostgreSQL database models, and complete UI screens with no fake placeholder buttons or static mockups.
- **Auditability:** Complete tamper-evident audit logging of operator actions and database queries for chain-of-custody compliance.
