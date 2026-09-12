# SENTINEL — AI Alert, Emergency Response & Multi-Camera Monitoring

## Complete Feature Implementation Guide

This document describes the newly integrated AI Alert, Emergency Response, and Intelligent Multi-Camera Monitoring system for SENTINEL.

---

## 1. OVERVIEW

The SENTINEL platform now includes:

- **AI Alert System** — Intelligent alert management with severity levels
- **Emergency Response Module** — Complete incident management, ambulance dispatch, and hospital coordination
- **Phone Verification** — OTP-based secure phone number verification for recipients
- **SMS & Voice Alerts** — Send alerts via SMS and automated voice calls with TTS
- **Multi-Camera Monitoring** — View multiple camera feeds simultaneously with Google Maps integration
- **Incident Timeline** — Real-time chronological timeline of events
- **Multi-Camera Correlation** — Automatically link related events from multiple cameras
- **GIS Integration** — Google Maps-based location visualization and incident tracking

---

## 2. SYSTEM ARCHITECTURE

### Backend Services

```
app/
├── models/emergency.py               # Database models
├── schemas/emergency.py              # API request/response schemas
├── services/
│   ├── otp_service.py               # OTP management
│   ├── notification_service.py       # SMS/Voice/TTS service
│   └── emergency_service.py          # Incident management
└── api/v1/endpoints/emergency.py    # API endpoints
```

### Frontend Components

```
app/
├── emergency/page.tsx               # Emergency Response Centre
├── emergency-cameras/page.tsx       # Multi-Camera Monitoring View
components/
├── map/MultiCameraMap.tsx           # Google Maps integration
└── alerts/AIAlertPanel.tsx          # AI Alert panel component
```

---

## 3. PHONE VERIFICATION & OTP WORKFLOW

### Flow: Verify Phone Number for Alerts

1. **Request OTP**
   ```
   POST /api/v1/emergency/phone-verification/request-otp
   {
     "phone_number": "+91-9999999999"
   }
   ```
   - Generates 6-digit OTP
   - Stores OTP with 10-minute expiry
   - Sends OTP via SMS (if configured)

2. **Verify OTP**
   ```
   POST /api/v1/emergency/phone-verification/verify-otp
   {
     "phone_number": "+91-9999999999",
     "otp": "123456"
   }
   ```
   - Validates OTP and expiry
   - Marks phone as verified
   - Blocks after 3 failed attempts

3. **Check Verification Status**
   ```
   GET /api/v1/emergency/phone-verification/status/+91-9999999999
   ```
   - Returns: verified, pending, blocked, or not_registered

### Security Features
- OTPs never exposed in logs
- 10-minute expiry (configurable)
- 3-attempt block limit
- Secure SMS delivery via Twilio

---

## 4. ALERT RECIPIENT MANAGEMENT

### Create an Alert Recipient

1. **Verify phone number first** (see section 3)
2. **Create recipient**
   ```
   POST /api/v1/emergency/recipients
   {
     "name": "Officer Sharma",
     "phone_verification_id": "uuid",
     "recipient_type": "OPERATOR",
     "alert_preference": "ALL",
     "email": "officer@police.gov.in"
   }
   ```

### Recipient Types
- `OPERATOR` — Dashboard operators
- `POLICE` — Police response units
- `AMBULANCE` — Ambulance/Medical services
- `HOSPITAL` — Hospital emergency departments

### Alert Preferences
- `ALL` — Receive all alerts
- `NORMAL` — Receive normal and above
- `HIGH` — Receive high and above
- `EMERGENCY` — Emergency only

### Manage Recipients
```
GET /api/v1/emergency/recipients?recipient_type=OPERATOR
PUT /api/v1/emergency/recipients/{recipient_id}
```

---

## 5. EMERGENCY INCIDENT CREATION & MANAGEMENT

### Create Emergency Incident

```
POST /api/v1/emergency/incidents
{
  "incident_type": "ACCIDENT",
  "severity": "HIGH",
  "detection_source": "AI",
  "camera_id": "uuid",
  "location_latitude": 20.5937,
  "location_longitude": 78.9629,
  "location_name": "Highway Near City Center",
  "description": "Vehicle collision detected",
  "ai_confidence": 0.89,
  "detected_objects": {
    "vehicles": 2,
    "persons": 0
  }
}
```

### Incident Severity Levels
- `LOW` — Minor events, informational
- `MEDIUM` — Notable events, attention required
- `HIGH` — Serious incident, urgent response
- `CRITICAL` — Life-threatening, immediate action

### Incident Status
- `OPEN` — New incident, requires attention
- `ACKNOWLEDGED` — Operator acknowledged
- `RESOLVED` — Incident handled
- `DISMISSED` — False alarm or resolved

### List Incidents
```
GET /api/v1/emergency/incidents?status=OPEN&severity=HIGH
```

### Update Incident
```
PUT /api/v1/emergency/incidents/{incident_id}
{
  "status": "ACKNOWLEDGED",
  "operator_comments": "Response team dispatched",
  "severity": "CRITICAL"
}
```

---

## 6. ALERT WORKFLOW BY SEVERITY LEVEL

### NORMAL ALERT (Informational)
**When to use**: Routine detections, minor issues
**Action**: Send SMS message only

```
POST /api/v1/emergency/incidents/{incident_id}/send-alert
{
  "alert_level": "NORMAL",
  "custom_message": null
}
```

**Message Format**:
```
"Alert: ACCIDENT detected at Highway Near City Center. Status: HIGH. Please check the monitoring dashboard."
```

**Recipients**: OPERATOR type only

---

### HIGH ALERT (Urgent)
**When to use**: Serious incidents, priority response needed
**Actions**:
1. Send SMS to all OPERATOR and POLICE recipients
2. Initiate phone calls with TTS message to emergency contacts
3. Include incident location and camera ID

```
POST /api/v1/emergency/incidents/{incident_id}/send-alert
{
  "alert_level": "HIGH",
  "custom_message": "Multiple vehicles involved. Traffic blocked. Immediate response required."
}
```

**TTS Message**:
```
"Hello. This is an AI emergency alert. A high-risk accident has been detected at Highway Near City Center. 
The incident was detected at 2024-09-05 14:32:08. Severity: HIGH. 
Custom message: Multiple vehicles involved. Traffic blocked. Immediate response required. 
Please check the emergency dashboard immediately."
```

**Recipients**: OPERATOR, POLICE types

---

### EMERGENCY ALERT (Critical)
**When to use**: Life-threatening, immediate action required
**Actions**:
1. Send SMS to OPERATOR, POLICE, and AMBULANCE recipients
2. Initiate voice calls with TTS to ALL recipient types
3. Trigger hospital notification workflow
4. Dispatch ambulance automatically
5. Send police high-priority alert

```
POST /api/v1/emergency/incidents/{incident_id}/send-alert
{
  "alert_level": "EMERGENCY",
  "custom_message": "Accident with critical injuries detected. Dispatch ambulance and police immediately."
}
```

**Recipients**: OPERATOR, POLICE, AMBULANCE, HOSPITAL types

---

## 7. AMBULANCE DISPATCH WORKFLOW

### Find Nearest Hospital

```
POST /api/v1/emergency/incidents/{incident_id}/find-hospital
```

**Response**:
```json
{
  "incident_id": "uuid",
  "hospital": {
    "hospital_name": "City General Hospital",
    "hospital_phone": "+91-9876543210",
    "latitude": 20.5947,
    "longitude": 78.9739,
    "distance_km": 1.2,
    "arrival_minutes": 8
  },
  "incident_location": {
    "latitude": 20.5937,
    "longitude": 78.9629,
    "name": "Highway Near City Center"
  }
}
```

### Dispatch Ambulance

```
POST /api/v1/emergency/incidents/{incident_id}/ambulance
{
  "hospital_name": "City General Hospital",
  "hospital_phone": "+91-9876543210",
  "hospital_latitude": 20.5947,
  "hospital_longitude": 78.9739,
  "ambulance_id": "AMB-001"
}
```

### Get Ambulance Status

```
GET /api/v1/emergency/incidents/{incident_id}/ambulance
```

**Ambulance Dispatch Status**:
- `DISPATCHED` — Ambulance dispatched, beginning journey
- `ENROUTE` — Ambulance traveling to scene
- `ARRIVED` — Ambulance at incident location
- `COMPLETED` — Victim transported, incident complete

---

## 8. INCIDENT TIMELINE

### Get Incident Timeline

```
GET /api/v1/emergency/incidents/{incident_id}/timeline
```

**Response**:
```json
[
  {
    "id": "uuid",
    "incident_id": "uuid",
    "event_type": "DETECTED",
    "camera_id": "uuid",
    "event_time": "2024-09-05T14:31:52Z",
    "description": "Incident detected: ACCIDENT"
  },
  {
    "id": "uuid",
    "incident_id": "uuid",
    "event_type": "ALERT_SENT",
    "camera_id": null,
    "event_time": "2024-09-05T14:32:10Z",
    "description": "Alert sent to 5 recipients at HIGH level"
  },
  {
    "id": "uuid",
    "incident_id": "uuid",
    "event_type": "AMBULANCE_DISPATCHED",
    "camera_id": null,
    "event_time": "2024-09-05T14:32:15Z",
    "description": "Ambulance dispatched to City General Hospital"
  }
]
```

**Example Timeline**:
```
14:31:52 — Vehicle detected (Confidence: 89%)
14:32:01 — Sudden movement detected
14:32:05 — Possible collision detected
14:32:08 — High-risk accident classified
14:32:10 — Police alert generated
14:32:11 — Ambulance response initiated
14:32:15 — Emergency notification delivered
14:32:30 — Ambulance en route (8 min ETA)
```

---

## 9. MULTI-CAMERA CORRELATION

### Automatic Event Correlation

When the same incident appears on multiple cameras:

**Camera C-101** → 14:31:52 — Vehicle detected
**Camera C-102** → 14:32:01 — Vehicle continues toward intersection
**Camera C-103** → 14:32:05 — Accident detected
**Camera C-104** → 14:32:30 — Traffic blockage detected

The system automatically:
1. Groups related detections
2. Creates unified incident timeline
3. Traces vehicle movement path
4. Calculates trajectory and speed
5. Provides cross-camera evidence

### API for Correlation

```
POST /api/v1/emergency/incidents/correlate
{
  "camera_events": [
    {
      "camera_id": "uuid",
      "event_type": "VEHICLE_DETECTED",
      "timestamp": "2024-09-05T14:31:52Z",
      "latitude": 20.5937,
      "longitude": 78.9629,
      "location_name": "Highway Segment 1",
      "confidence": 0.85
    },
    {
      "camera_id": "uuid",
      "event_type": "COLLISION_DETECTED",
      "timestamp": "2024-09-05T14:32:05Z",
      "latitude": 20.5945,
      "longitude": 78.9640,
      "location_name": "Intersection",
      "confidence": 0.92
    }
  ]
}
```

---

## 10. FRONTEND: EMERGENCY RESPONSE CENTRE

### Access
```
http://localhost:3000/emergency
```

### Features
- **Active Incidents List** — All open incidents with severity indicators
- **Incident Details** — Full incident information, location, detection data
- **Alert Control** — Send alerts at NORMAL, HIGH, or EMERGENCY level
- **Custom Message** — Operator can add custom message to voice calls
- **Hospital Finder** — Automatic nearest hospital detection
- **Ambulance Dispatch** — One-click ambulance dispatch with ETA
- **Recipient Management** — Add/verify alert recipients
- **Phone Verification** — OTP-based recipient verification

### Severity Color Coding
- 🔴 **CRITICAL** (Red) — Life-threatening, immediate action
- 🟠 **HIGH** (Orange) — Serious incident, urgent response
- 🟡 **MEDIUM** (Yellow) — Notable incident, attention required
- 🟢 **LOW** (Green) — Routine event, informational

---

## 11. FRONTEND: MULTI-CAMERA MONITORING

### Access
```
http://localhost:3000/emergency-cameras
```

### Features
- **Google Maps Integration** — Geovisualization of all cameras
- **Live Camera Grid** — View status of multiple cameras
- **Status Indicators** — Online/offline/degraded status
- **Location Filtering** — Filter cameras by zone/district
- **Selected Camera Details** — Full camera information
- **Live Feed Placeholder** — Ready for RTSP/HLS stream integration
- **AI Analysis Panel** — Recent detections and active alerts
- **Detection Highlights** — Real-time detection confidence scores

### Camera Status
- 🟢 **ONLINE** — Stream active, receiving data
- 🔴 **OFFLINE** — No connection, stream unavailable
- 🟡 **DEGRADED** — Intermittent connection, reduced quality

---

## 12. CONFIGURATION

### Backend Configuration (.env)

```env
# SMS & Voice Alerts (Twilio)
ENABLE_SMS_ALERTS=true
ENABLE_VOICE_CALLS=true
ENABLE_TTS=true
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# OTP Settings
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=3

# Hospital & Emergency Services
DEFAULT_HOSPITAL_API_URL=https://api.hospital-service.local/hospitals
POLICE_EMERGENCY_PHONE=+91-emergency-phone
```

### Frontend Configuration (.env.local)

```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 13. DEMO MODE & SAFETY

### Demo Configuration
- **Demo Mode Enabled**: `DEMO_MODE=true` in .env
- **SMS Alerts**: Logged but not actually sent
- **Voice Calls**: Logged but not actually placed
- **Demo Recipients**: Pre-created in seed data
- **Synthetic Incidents**: Demo data for testing

### Demo Recipients
```json
{
  "name": "Demo Operator 1",
  "phone_number": "+91-9999999991",
  "recipient_type": "OPERATOR",
  "is_verified": true
}
```

### Important Notes
- All SMS/calls are **logged** but not actually sent in demo mode
- **No real government databases** are connected
- **No live surveillance feeds** are processed
- **Safe for demonstration** without real alerts

---

## 14. INSTALLATION & SETUP

### Backend Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure .env**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start backend**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure .env.local**:
   ```bash
   cp .env.example .env.local
   # Edit with your Google Maps API key
   ```

3. **Start frontend**:
   ```bash
   npm run dev
   ```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Emergency Centre**: http://localhost:3000/emergency
- **Multi-Camera View**: http://localhost:3000/emergency-cameras

---

## 15. API ENDPOINTS SUMMARY

### Phone Verification
- `POST /emergency/phone-verification/request-otp` — Request OTP
- `POST /emergency/phone-verification/verify-otp` — Verify OTP
- `GET /emergency/phone-verification/status/{phone}` — Get status

### Recipients
- `POST /emergency/recipients` — Create recipient
- `GET /emergency/recipients` — List recipients
- `PUT /emergency/recipients/{id}` — Update recipient

### Incidents
- `POST /emergency/incidents` — Create incident
- `GET /emergency/incidents` — List incidents
- `GET /emergency/incidents/{id}` — Get incident
- `PUT /emergency/incidents/{id}` — Update incident

### Timeline & Status
- `GET /emergency/incidents/{id}/timeline` — Get timeline
- `GET /emergency/incidents/{id}/ambulance` — Get ambulance status

### Actions
- `POST /emergency/incidents/{id}/send-alert` — Send alert
- `POST /emergency/incidents/{id}/ambulance` — Dispatch ambulance
- `POST /emergency/incidents/{id}/find-hospital` — Find hospital

---

## 16. TROUBLESHOOTING

### SMS Not Sending
- Check Twilio credentials in .env
- Verify phone number format (+country-code)
- Confirm Twilio account has funds

### Voice Calls Not Working
- Ensure TTS is enabled (`ENABLE_TTS=true`)
- Check Twilio account settings
- Verify recipient phone is verified

### Google Maps Not Loading
- Add API key to .env (`GOOGLE_MAPS_API_KEY=...`)
- Enable Maps JavaScript API in Google Cloud Console
- Check browser console for errors

### OTP Issues
- OTP expires after 10 minutes (configurable)
- Maximum 3 failed attempts before block
- Check SMS delivery logs

---

## 17. COMPLIANCE & SECURITY

✅ **Implemented**:
- Role-based access control (RBAC)
- Phone number verification with OTP
- Secure credential storage
- Audit logging for all actions
- Encrypted communication (TLS)
- OTP security (not exposed in logs)
- Recipient verification before alerts

⚠️ **Important**:
- Never store sensitive data in plain text
- Always use HTTPS in production
- Rotate API keys regularly
- Monitor alert delivery logs
- Maintain government compliance
- Document all integrations with real systems

---

## 18. PRODUCTION DEPLOYMENT CHECKLIST

- [ ] Update .env with production credentials
- [ ] Enable TLS/HTTPS
- [ ] Configure real Twilio account
- [ ] Set up Google Maps API with restrictions
- [ ] Enable database encryption
- [ ] Set up audit logging and monitoring
- [ ] Configure backup and recovery procedures
- [ ] Test alert delivery end-to-end
- [ ] Train operators on emergency procedures
- [ ] Document SLAs and escalation procedures
- [ ] Set up 24/7 monitoring and alerting
- [ ] Conduct security audit
- [ ] Obtain government approval for live operation

---

## 19. ADDITIONAL RESOURCES

- [Twilio Documentation](https://www.twilio.com/docs)
- [Google Maps API](https://developers.google.com/maps)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

**Version**: 1.0.0  
**Last Updated**: 2024-09-05  
**Status**: Ready for Demo & Integration
