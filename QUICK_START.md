# 🚀 QUICK START GUIDE — Emergency Alert System

## 5-Minute Setup

### Step 1: Get API Keys (2 minutes)

#### Google Maps API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "SENTINEL"
3. Enable "Maps JavaScript API"
4. Create API key (restrict to your domain)
5. Copy key

#### Twilio Account (Optional for Demo)
1. Go to [Twilio](https://www.twilio.com/) and create account
2. Get: Account SID, Auth Token, Phone Number
3. Skip for now (demo mode uses logs)

### Step 2: Configure Environment (2 minutes)

```bash
cd SENTINEL-Intelligent-CCTV-Police-Intelligence-Platform

# Copy and edit backend config
cp .env.example .env
nano .env  # OR: open in editor
```

Update `.env`:
```env
# Add your keys
GOOGLE_MAPS_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Keep demo mode ON for testing
DEMO_MODE=true
```

### Step 3: Frontend Config (1 minute)

```bash
cd frontend

# Create environment file
echo "NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_key_here" > .env.local
```

---

## Starting the System

### Terminal 1: Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

✅ Backend running: `http://localhost:8000`  
📚 API Docs: `http://localhost:8000/docs`

### Terminal 2: Frontend

```bash
cd frontend
npm install
npm run dev
```

✅ Frontend running: `http://localhost:3000`

---

## Accessing Features

### 🚨 Emergency Response Centre
```
http://localhost:3000/emergency
```
- Create incidents
- Manage alerts
- Verify phone numbers
- Dispatch ambulances

### 📹 Multi-Camera Monitoring
```
http://localhost:3000/emergency-cameras
```
- View all cameras on Google Map
- Monitor status
- See detections and alerts

### 📊 Main Dashboard
```
http://localhost:3000/dashboard
```
- System overview
- Alert statistics

---

## Quick Test Workflow

### 1️⃣ Add Alert Recipient

1. Open Emergency Response Centre
2. Click **+ Add New Recipient**
3. Enter phone: `+91-9999999991` (demo number)
4. Click **Send OTP**
5. Enter demo OTP (check backend console)
6. Click **Verify OTP**
7. ✅ Recipient created

### 2️⃣ Create Emergency Incident

Use API or create manually:

```bash
curl -X POST http://localhost:8000/api/v1/emergency/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "incident_type": "ACCIDENT",
    "severity": "HIGH",
    "detection_source": "AI",
    "camera_id": null,
    "location_latitude": 20.5937,
    "location_longitude": 78.9629,
    "location_name": "Highway Junction",
    "description": "Vehicle collision detected",
    "ai_confidence": 0.89
  }'
```

Or use Swagger UI: `http://localhost:8000/docs` → Try it out

### 3️⃣ Send Alert

In Emergency Response Centre:
1. Select incident from list
2. Choose alert level: **HIGH**
3. Add custom message (optional)
4. Click **📢 SEND ALERT**
5. ✅ Alert sent! (check backend logs)

### 4️⃣ Dispatch Ambulance

1. With incident selected
2. Click **🚑 DISPATCH AMBULANCE**
3. ✅ Ambulance dispatched!
4. Check timeline for events

### 5️⃣ View on Google Map

Go to Multi-Camera Monitor:
1. Cameras displayed on map
2. Click camera marker
3. View camera details
4. See status (Online/Offline)

---

## Demo Mode Behavior

✅ **SMS Alerts**: Logged to console (not actually sent)  
✅ **Voice Calls**: Logged to console (not actually placed)  
✅ **OTP**: Visible in backend console for testing  
✅ **Safe**: No real external service calls  

### See Demo Logs

Backend console shows:
```
[DEMO] SMS to +91-9999999991: Alert: ACCIDENT detected at ...
[DEMO] Voice call to +91-9999999991: Hello. This is an AI emergency alert...
2024-09-05 14:32:10 - OTP generated: 123456
```

---

## Backend Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "sentinel-api",
  "demo_mode": true
}
```

---

## Common Issues

### ❌ "Google Maps API key not found"
- **Fix**: Add `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` to `frontend/.env.local`

### ❌ "Cannot GET /emergency"
- **Fix**: Make sure frontend is running on `:3000`

### ❌ "Database connection error"
- **Fix**: Using SQLite (default), should auto-create `.db` file

### ❌ "Twilio not configured"
- **Expected**: Demo mode uses mocked SMS/calls
- Keep `DEMO_MODE=true` or configure Twilio

---

## Next Steps

### Development
- [ ] Configure real Twilio account for SMS/calls
- [ ] Add Google Maps API key
- [ ] Connect to real PostgreSQL database
- [ ] Integrate with camera streams
- [ ] Test multi-camera correlation

### Production
- [ ] Enable HTTPS/TLS
- [ ] Set up production database
- [ ] Configure monitoring and alerting
- [ ] Set up backup procedures
- [ ] Conduct security audit
- [ ] Deploy to server

---

## Documentation

📖 **Full Documentation**:
- `EMERGENCY_ALERT_IMPLEMENTATION.md` — Complete guide
- `SENTINEL_MASTER_REQUIREMENTS.md` — System requirements
- `API_CONTRACTS.md` — API specifications

📚 **In-Code Documentation**:
- Backend: `backend/app/api/v1/endpoints/emergency.py`
- Services: `backend/app/services/emergency_service.py`
- Frontend: Component JSDoc comments

---

## Support

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Backend Logs
```bash
# Watch logs (from backend terminal)
# Already displayed with --reload
```

### Frontend Logs
```bash
# Check browser console (F12)
# Check terminal where `npm run dev` is running
```

---

## Commands Reference

```bash
# Backend
cd backend
pip install -r requirements.txt              # Install deps
uvicorn app.main:app --reload               # Start server
uvicorn app.main:app --reload --port 9000   # Custom port

# Frontend
cd frontend
npm install                                  # Install deps
npm run dev                                  # Start dev server
npm run build                                # Build for production
npm run start                                # Start production

# API Testing
curl http://localhost:8000/health            # Health check
curl http://localhost:8000/docs              # Swagger UI

# Database
cd backend
alembic upgrade head                         # Apply migrations
alembic revision --autogenerate -m "msg"     # Create migration
```

---

## Emergency Response Flow

```
1. Incident Detected (AI or Manual)
   ↓
2. Create Emergency Incident
   ↓
3. Find Nearest Hospital
   ↓
4. Select Alert Level
   ├─ NORMAL → SMS to operators
   ├─ HIGH → SMS + voice to operators/police
   └─ EMERGENCY → All recipients + ambulance dispatch
   ↓
5. Dispatch Ambulance (if needed)
   ↓
6. Track on Timeline
   ↓
7. Acknowledge & Resolve
```

---

**Last Updated**: 2024-09-05  
**Version**: 1.0.0  
**Status**: Ready to use! 🚀
