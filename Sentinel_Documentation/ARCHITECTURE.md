# SENTINEL --- System Architecture

## 1. Architecture Principles

1.  Vendor neutral.
2.  Modular adapters.
3.  Event-driven processing.
4.  Edge/regional/central scalability.
5.  API-first backend.
6.  GIS-native metadata.
7.  AI as a pluggable capability.
8.  Security by design.
9.  Human verification for high-impact alerts.
10. Observable and auditable operations.

## 2. High-Level Architecture

``` text
CCTV / NVR / VMS
       |
       v
+-------------------------+
| VMS / Camera Adapters   |
| RTSP | ONVIF | SDK | API|
+------------+------------+
             |
             v
+-------------------------+
| Stream Gateway          |
| MediaMTX / GStreamer    |
+------------+------------+
             |
        +----+----+
        |         |
        v         v
     Browser     AI Workers
                   |
                   v
          +------------------+
          | AI Analytics     |
          | Detection        |
          | ANPR             |
          | Tracking         |
          | Events           |
          +--------+---------+
                   |
                   v
             Event Bus
              Kafka
                   |
        +----------+-----------+
        |                      |
        v                      v
+---------------+      +----------------+
| Correlation   |      | Alert Engine   |
| Engine        |      |                |
| History       |      | Priority       |
| Watchlists    |      | WebSocket      |
| GIS           |      | Notifications  |
+-------+-------+      +--------+-------+
        |                       |
        +-----------+-----------+
                    |
                    v
          +---------------------+
          | Sentinel API        |
          | FastAPI             |
          +----------+----------+
                     |
                     v
          +---------------------+
          | Police Dashboard    |
          | Next.js / React      |
          +---------------------+

Persistent Data:
PostgreSQL + PostGIS
Redis
Object Storage
OpenSearch (scale option)
```

## 3. Core Services

### API Gateway

Responsibilities: - Authentication. - Rate limiting. - Request
routing. - API versioning. - Security headers.

### Camera Registry Service

Owns: - Camera metadata. - VMS metadata. - Stream profiles. - Camera
health. - GIS coordinates.

### VMS Connector Service

Uses adapter interfaces so vendor-specific integrations do not leak into
the rest of the platform.

``` python
class VMSAdapter:
    async def authenticate(self): ...
    async def get_cameras(self): ...
    async def get_stream(self, camera_id): ...
    async def get_events(self): ...
    async def get_recording(self, camera_id, start, end): ...
```

### Stream Gateway

Responsibilities: - RTSP ingestion. - Stream relay. - WebRTC/HLS
conversion. - Connection lifecycle. - Access control.

### AI Inference Service

Responsibilities: - Frame acquisition. - Detection. - ANPR. -
Tracking. - Event classification. - Confidence generation.

### Correlation Service

Combines: - AI detections. - Camera location. - Time. - Historical
sightings. - Watchlist entries. - Event context.

### Alert Service

Creates, prioritizes, broadcasts, acknowledges, and resolves alerts.

### Investigation Service

Provides historical search and evidence retrieval.

## 4. Data Flow

``` text
1. Camera sends stream
2. Adapter/gateway receives stream
3. AI worker samples frames
4. Detector finds objects
5. Tracker associates objects
6. ANPR reads plate where applicable
7. Detection becomes an event
8. Event enters Kafka
9. Correlation engine checks history/watchlists
10. Alert engine creates alert when rules match
11. WebSocket broadcasts alert
12. Dashboard updates immediately
13. Event/evidence is persisted
```

## 5. Edge / Regional / Central Deployment

``` text
CAMERAS
  |
  v
EDGE SITE
- stream gateway
- optional lightweight inference
- local buffering
  |
  v
REGIONAL CLUSTER
- GPU inference
- event processing
- regional storage
  |
  v
STATE COMMAND
- correlation
- GIS
- alerts
- investigation
- administration
```

This avoids requiring all raw video to traverse the central network
continuously.

## 6. Scaling Strategy

### Stateless services

Scale horizontally: - API - alert consumers - correlation workers -
authentication - investigation API

### Stateful systems

Use: - PostgreSQL replication. - Partitioned event/sighting tables. -
Redis replication. - Kafka partitions. - Object storage lifecycle
policies.

### AI scaling

Use GPU worker pools:

``` text
Camera partitions
       |
       v
Kafka
       |
+------+------+------+
| GPU1 | GPU2 | GPU3 |
+------+------+------+
       |
       v
Detection events
```

## 7. Video Storage

### Hot

Recent footage/events for fast investigation.

### Warm

Historical footage accessed less frequently.

### Cold

Long-term archival according to approved retention policies.

## 8. Reliability

-   Health endpoints for every service.
-   Retry with exponential backoff.
-   Circuit breakers for external connectors.
-   Kafka consumer offsets.
-   Idempotency keys.
-   Dead-letter queues.
-   Database backups.
-   Regional failover.
-   Disaster recovery procedures.

## 9. Observability

Recommended stack:

``` text
Prometheus -> metrics
Grafana    -> dashboards
Loki       -> logs
OpenTelemetry -> traces
```

Key metrics: - camera_online_count - stream_reconnect_count -
inference_fps - inference_latency_ms - anpr_confidence -
events_per_second - alerts_per_minute - kafka_lag - api_latency_ms
