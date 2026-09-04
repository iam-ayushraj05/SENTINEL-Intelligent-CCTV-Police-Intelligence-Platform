# SENTINEL --- API Contracts

Base URL:

``` text
/api/v1
```

All APIs should return JSON and use consistent error structures.

## 1. Authentication

### POST /auth/login

Request:

``` json
{
  "username": "operator01",
  "password": "********"
}
```

Response:

``` json
{
  "access_token": "token",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "role": "STATE_OPERATOR"
  }
}
```

## 2. Cameras

### GET /cameras

Query parameters: - status - department_id - vendor - bbox - page -
limit

### POST /cameras

``` json
{
  "camera_code": "CAM-GJ-000127",
  "name": "Ring Road Junction",
  "department_id": "uuid",
  "protocol": "RTSP",
  "latitude": 23.0225,
  "longitude": 72.5714
}
```

### GET /cameras/{camera_id}

Returns camera metadata, health and available streams.

### POST /cameras/{camera_id}/health-check

Returns:

``` json
{
  "camera_id": "uuid",
  "status": "ONLINE",
  "latency_ms": 84,
  "checked_at": "2026-09-04T12:00:00Z"
}
```

### POST /cameras/bulk-import

Accepts an authorized CSV import.

## 3. Streams

### GET /cameras/{camera_id}/stream

Returns an authorized playback/live-stream descriptor.

``` json
{
  "camera_id": "uuid",
  "protocol": "WEBRTC",
  "session_url": "..."
}
```

## 4. Detections

### GET /detections

Filters: - camera_id - object_type - start_time - end_time -
minimum_confidence

### GET /detections/{detection_id}

Returns detection metadata and evidence reference.

## 5. Events

### GET /events

Filters: - event_type - severity - camera_id - start_time - end_time -
status

### GET /events/{event_id}

Returns event details and related detections.

## 6. Vehicles

### GET /vehicles/{plate}/sightings

Response:

``` json
{
  "plate": "GJXX1234",
  "sightings": [
    {
      "camera_id": "CAM008",
      "timestamp": "2026-09-04T18:21:00Z",
      "latitude": 23.02,
      "longitude": 72.57,
      "confidence": 0.94
    }
  ]
}
```

### GET /vehicles/{plate}/route

Response:

``` json
{
  "plate": "GJXX1234",
  "segments": [
    {
      "from_camera": "CAM008",
      "to_camera": "CAM014",
      "start_time": "2026-09-04T18:21:00Z",
      "end_time": "2026-09-04T18:31:00Z",
      "confidence": 0.91,
      "geometry": "..."
    }
  ]
}
```

### GET /vehicles/{plate}/timeline

Returns chronologically ordered sightings, alerts and relevant events.

## 7. Watchlists

### GET /watchlists

### POST /watchlists

``` json
{
  "name": "Stolen Vehicles",
  "type": "STOLEN_VEHICLE",
  "description": "Authorized demonstration watchlist"
}
```

### POST /watchlists/{watchlist_id}/entries

``` json
{
  "entity_type": "VEHICLE",
  "identifier": "GJXX1234",
  "display_name": "Vehicle Record",
  "priority": "HIGH"
}
```

## 8. Alerts

### GET /alerts

Filters: - severity - status - alert_type - camera_id - start_time -
end_time

### GET /alerts/{alert_id}

### POST /alerts/{alert_id}/acknowledge

### POST /alerts/{alert_id}/resolve

## 9. Real-Time Alerts

``` text
WS /ws/alerts
```

Message:

``` json
{
  "type": "ALERT_CREATED",
  "alert": {
    "id": "uuid",
    "severity": "HIGH",
    "title": "Watchlist Match",
    "plate": "GJXX1234",
    "camera_id": "CAM027",
    "confidence": 0.96
  }
}
```

## 10. Investigation

### GET /investigation/search

Parameters: - entity - plate - camera_id - start_time - end_time -
event_type - latitude - longitude - radius

Response contains detections, sightings, events and evidence references.

## 11. System Health

### GET /health

``` json
{
  "status": "healthy"
}
```

### GET /health/services

Returns health of: - PostgreSQL - Redis - Kafka - stream gateway - AI
workers - connectors

## 12. Standard Error

``` json
{
  "error": {
    "code": "CAMERA_NOT_FOUND",
    "message": "Camera does not exist",
    "request_id": "uuid"
  }
}
```

HTTP status codes: - 200 success - 201 created - 400 validation - 401
authentication - 403 authorization - 404 not found - 409 conflict - 422
invalid input - 429 rate limit - 500 internal error - 503 dependency
unavailable
