# SENTINEL --- Implementation Phases

## Phase 0 --- Repository Foundation

### Deliverables

-   Monorepo.
-   Docker Compose.
-   Environment configuration.
-   CI. 
-   README.
-   Initial frontend/backend applications.

### Suggested structure

``` text
sentinel/
├── frontend/
├── backend/
├── ai/
├── streaming/
├── infrastructure/
└── docs/
```

------------------------------------------------------------------------

## Phase 1 --- Database and Core Models

Implement: - Department. - User. - VMSSystem. - Camera. -
CameraStream. - Detection. - Vehicle. - VehicleSighting. - Event. -
Watchlist. - WatchlistEntry. - Alert. - RouteSegment. - AuditLog.

Add PostgreSQL + PostGIS.

### Exit criteria

-   Migrations work.
-   Seed data loads.
-   CRUD tests pass.

------------------------------------------------------------------------

## Phase 2 --- Authentication and RBAC

Implement: - Login. - JWT/session handling. - Roles. - Permission
middleware. - Audit logs.

Roles: - SUPER_ADMIN - STATE_OPERATOR - DISTRICT_OPERATOR -
INVESTIGATOR - VIEW_ONLY

### Exit criteria

Unauthorized users cannot access protected operations.

------------------------------------------------------------------------

## Phase 3 --- Camera Registry

Implement: - Camera CRUD. - VMS CRUD. - Bulk import. - Camera health. -
Camera search. - GIS coordinates.

### Exit criteria

A camera can be registered and viewed on the map.

------------------------------------------------------------------------

## Phase 4 --- CCTV Stream Integration

Start with RTSP.

Implement: - Media gateway. - Stream health. - Reconnect. - Browser
playback. - Multiple camera support.

Then create the adapter interface for: - ONVIF. - VMS API. - Vendor SDK.

### Exit criteria

At least several independent feeds can be viewed simultaneously.

------------------------------------------------------------------------

## Phase 5 --- AI Detection

Implement: - vehicle detection; - person detection; - tracking.

Persist detection metadata.

### Exit criteria

Live video produces timestamped detection events.

------------------------------------------------------------------------

## Phase 6 --- ANPR

Pipeline:

``` text
Frame
→ vehicle detector
→ plate detector
→ crop
→ enhancement
→ OCR
→ normalization
→ multi-frame confidence
→ vehicle sighting
```

### Exit criteria

Demo vehicles generate stable normalized plate records.

------------------------------------------------------------------------

## Phase 7 --- Event Bus

Add Kafka.

Topics:

``` text
camera.events
detections
vehicle.sightings
watchlist.matches
alerts
system.events
```

### Exit criteria

AI services can publish events and downstream services can consume them
independently.

------------------------------------------------------------------------

## Phase 8 --- Watchlist Correlation

Implement: - watchlist CRUD; - identifier normalization; - exact
matching; - confidence thresholds; - alert creation.

### Exit criteria

A configured watchlist vehicle causes an automatic alert.

------------------------------------------------------------------------

## Phase 9 --- Real-Time Alerting

Implement: - Alert service. - WebSocket. - Dashboard notification. -
Acknowledge. - Resolve. - Audit.

### Exit criteria

A watchlist event appears in the UI without page refresh.

------------------------------------------------------------------------

## Phase 10 --- Cross-Camera Intelligence

Implement: - sighting grouping; - temporal correlation; - spatial
correlation; - vehicle history; - route segments; - route confidence.

### Exit criteria

Searching a vehicle returns:

``` text
First seen
Last seen
All sightings
Camera sequence
Map route
Related alerts
```

------------------------------------------------------------------------

## Phase 11 --- Investigation

Implement: - unified search; - timeline; - evidence viewer; - filters; -
report export.

### Exit criteria

An investigator can reconstruct a vehicle's history from stored events.

------------------------------------------------------------------------

## Phase 12 --- Observability and Security

Implement: - Prometheus. - Grafana. - structured logs. - tracing. - API
rate limits. - TLS. - secrets handling. - backup. - audit.

### Exit criteria

All core services expose health/metrics and sensitive operations are
audited.

------------------------------------------------------------------------

## Phase 13 --- Scale Testing

Test progressively:

``` text
50
→ 500
→ 1,000
→ 10,000
→ 50,000
→ 80,000 logical cameras
```

Measure: - events/sec; - API latency; - Kafka lag; - inference
throughput; - GPU utilization; - memory; - network; - storage growth.

Use synthetic streams/events for large-scale simulation.

------------------------------------------------------------------------

## Phase 14 --- Government Feed Integration

Once authorized government feeds/resources are available: - onboard
supplied feeds; - test protocols; - validate metadata; - configure
adapters; - test live analytics; - validate watchlist correlation.

Do not hard-code vendor assumptions before feed specifications are
known.

------------------------------------------------------------------------

## Phase 15 --- Final PoC

Demo sequence:

``` text
Camera onboarding
       ↓
Live CCTV
       ↓
AI detection
       ↓
ANPR
       ↓
Watchlist match
       ↓
Real-time alert
       ↓
Cross-camera history
       ↓
GIS route
       ↓
Investigation
```

## Phase 16 --- Deployment Package

Deliver: - Docker images. - Kubernetes manifests. - environment
template. - database migrations. - seed data. - API documentation. -
architecture diagram. - security document. - scalability/load-test
results. - deployment guide. - PoC video/demo.

## Priority Order

If time is limited:

``` text
P0  Camera onboarding
P0  Live feeds
P0  AI detection
P0  ANPR
P0  Watchlist
P0  Real-time alert

P1  Vehicle history
P1  GIS route
P1  Investigation

P2  Advanced event analytics
P2  Multi-vendor adapters
P2  Scale simulation
P2  Advanced observability
```
