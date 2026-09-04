# SENTINEL --- Product Requirements Document

## 1. Product Overview

**Sentinel** is a unified, vendor-neutral CCTV video intelligence
platform designed for police operations.

The platform brings heterogeneous CCTV feeds, AI video analytics,
authorized government/watchlist data, GIS, event correlation, and
real-time alerts into one operational interface.

### Core proposition

> Connect fragmented CCTV infrastructure, convert video into structured
> intelligence, correlate that intelligence with authorized data, and
> deliver actionable alerts to police operators.

## 2. Goals

1.  Integrate CCTV cameras and existing VMS platforms through
    standards-based adapters.
2.  Provide a unified live-camera and camera-health view.
3.  Detect vehicles, persons, and configurable events using AI.
4.  Perform Automatic Number Plate Recognition (ANPR).
5.  Maintain historical vehicle sightings across cameras.
6.  Correlate detections with authorized watchlists/databases.
7.  Generate real-time, prioritized alerts.
8.  Visualize camera locations, alerts, and vehicle movement on GIS.
9.  Provide investigation/search capabilities.
10. Support a path from a hackathon proof of concept to a large
    distributed deployment.

## 3. Target Users

### State Control Room Operator

-   Monitor alerts.
-   View cameras.
-   Search entities.
-   Acknowledge and escalate alerts.

### District Operator

-   Monitor cameras within assigned geography.
-   Investigate local incidents.
-   Review vehicle sightings.

### Investigator

-   Search historical detections.
-   Trace vehicle movement.
-   Review evidence and timestamps.
-   Generate investigation reports.

### System Administrator

-   Manage cameras, VMS connectors, users, roles, watchlists, and system
    health.

## 4. Primary Use Cases

### UC-01: CCTV onboarding

An authorized administrator registers a camera/VMS, verifies
connectivity, and makes it available to Sentinel.

### UC-02: Live monitoring

An operator opens a camera or camera grid and views the available live
stream.

### UC-03: Vehicle detection

The AI engine detects a vehicle, extracts metadata, and creates a
timestamped detection.

### UC-04: ANPR

The system detects a number plate, performs OCR, normalizes the result,
calculates confidence, and records the sighting.

### UC-05: Watchlist match

A detected identifier is checked against an authorized representative
watchlist. A match creates an alert.

### UC-06: Cross-camera vehicle tracing

The system groups compatible sightings of the same vehicle and presents
a chronological movement timeline and GIS route.

### UC-07: Investigation

An authorized user searches by plate, time, camera, location, or event
and reviews related evidence.

### UC-08: Camera health

The system reports online/offline/degraded status and last heartbeat.

## 5. Functional Requirements

### CCTV Integration

-   Support RTSP for the PoC.
-   Provide an adapter architecture for ONVIF, VMS APIs, and vendor
    SDKs.
-   Store camera metadata.
-   Test stream connectivity.
-   Detect camera health changes.
-   Support reconnect logic.

### AI Analytics

-   Vehicle detection.
-   Person detection.
-   Object tracking.
-   ANPR.
-   Configurable event detection.
-   Timestamp every detection.
-   Store confidence and source-camera information.

### Intelligence

-   Normalize identifiers.
-   Correlate detections with watchlists.
-   Maintain vehicle sighting history.
-   Build chronological timelines.
-   Calculate correlation confidence.
-   Preserve source evidence.

### Alerts

-   Alert types.
-   Severity levels.
-   Real-time delivery.
-   Acknowledge/resolve workflow.
-   Alert audit trail.
-   Evidence attachment.

### GIS

-   Camera markers.
-   Alert markers.
-   Vehicle sighting markers.
-   Route visualization.
-   Spatial filtering.

### Investigation

-   Entity search.
-   Date/time filters.
-   Camera filters.
-   Location filters.
-   Timeline.
-   Evidence viewer.
-   Report export.

## 6. Non-Functional Requirements

### Availability

Services should be independently restartable and designed for high
availability in production.

### Scalability

The architecture must support horizontal scaling of stream gateways, AI
workers, event processing, and APIs.

### Performance

-   Alert propagation should be near real time.
-   API responses should remain responsive under normal operational
    load.
-   AI inference should support configurable frame sampling.

### Security

-   TLS for network communication.
-   Role-based access control.
-   Secure credential references.
-   Audit logging.
-   API authentication.
-   Least-privilege service access.
-   Data retention policies.

### Reliability

-   Retry failed stream connections.
-   Idempotent event processing.
-   Dead-letter handling for failed events.
-   Health checks and observability.

## 7. Hackathon MVP

The MVP should demonstrate:

1.  Camera onboarding.
2.  Multiple CCTV feeds.
3.  Vehicle/person detection.
4.  ANPR.
5.  Representative watchlist.
6.  Automatic alert generation.
7.  Vehicle historical sightings.
8.  Cross-camera route visualization.
9.  Investigation search.
10. Operational backend rather than a static UI.

## 8. Success Metrics

-   Camera connection success rate.
-   Stream availability.
-   Detection throughput.
-   ANPR read confidence.
-   Watchlist matching latency.
-   Alert delivery latency.
-   Cross-camera correlation accuracy.
-   API latency.
-   AI worker utilization.
-   Number of cameras/events processed in load testing.

## 9. Constraints and Responsible Use

Sentinel is an operational decision-support system. AI matches must be
treated as evidence requiring authorized human verification, not as
automatic determinations of guilt or identity.

The system should collect and retain only data required for the approved
operational purpose and should enforce role-based access and
auditability.
