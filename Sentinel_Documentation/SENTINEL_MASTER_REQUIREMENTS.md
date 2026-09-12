# SENTINEL MASTER REQUIREMENTS

## 1. Executive Summary

SENTINEL is a unified CCTV intelligence and smart policing platform designed to integrate fragmented camera infrastructure, AI-based detection, Automated Number Plate Recognition (ANPR), geographic awareness, authorized watchlist correlation, and investigation workflows into a single command-centre operating system.

The platform is intended for police operations and public-safety command rooms, with a phased design that begins as a hackathon MVP and scales toward a full-state surveillance and intelligence operations platform. The solution must support real-time monitoring, historical investigation, alert generation, camera health management, and operational oversight while maintaining strict access control, auditability, and policy compliance.

The repository is created as a demo-ready foundation that reflects production-grade architecture without exposing live government data or live surveillance feeds. All sample content is synthetic demo data and should remain clearly labeled as such.

## 2. Project Vision

SENTINEL transforms raw CCTV feeds into actionable intelligence by combining:

- camera onboarding and device discovery
- live and historical video access
- AI object and event detection
- ANPR and vehicle normalization
- person/vehicle tracking across cameras
- authorized watchlist correlation
- GIS-based situational awareness
- alert orchestration and escalation
- investigation workflows and evidence review

The strategic objective is to reduce investigative time, improve situational awareness, identify high-risk entities, and enable faster response across police operations, districts, and command centres.

## 3. Problem Statement

Public safety agencies often operate a fragmented environment where CCTV feeds, VMS platforms, and police data systems are not integrated into one operational picture. This causes:

- delayed detection of suspicious vehicles or persons
- poor cross-camera correlation
- inconsistent watchlist matching
- limited alert triage and response workflows
- operational blind spots in camera health and response readiness
- dispersed evidence across multiple platforms

SENTINEL addresses this by creating a vendor-neutral intelligence platform that brings these sources together in a unified operational control layer.

## 4. Business Objectives

1. Standardize camera and VMS integrations across districts and departments.
2. Deliver a unified live monitoring and situational intelligence dashboard.
3. Improve detection speed and confidence for vehicles, persons, and events.
4. Enable ANPR normalization and cross-camera vehicle tracing.
5. Correlate detections with authorized watchlists and government data sources.
6. Prioritize and route alerts to the right operational user.
7. Support investigations with searchable historical evidence.
8. Provide GIS-based operational awareness and movement analysis.
9. Build trust through strong auditability, RBAC, and access control.
10. Create a scalable architecture capable of future expansion to statewide deployments.

## 5. Target Users

### 5.1 Control Room Operator
- monitors live camera streams
- views priority alerts
- tracks suspicious vehicles or persons
- acknowledges and escalates incidents
- coordinates operational response

### 5.2 District Operator
- monitors cameras within a district or geography
- investigates local incidents
- reviews vehicle movement patterns and alerts
- manages operational escalations

### 5.3 Investigator
- searches by person, plate, camera, date, or location
- reviews detections and evidence timelines
- traces movement across cameras
- prepares investigation reports

### 5.4 System Administrator
- manages users, roles, and permissions
- configures camera streams and VMS connectors
- maintains watchlists and alert policies
- monitors health, logs, and system resilience

## 6. Core Functional Requirements

### 6.1 Camera and Stream Integration
- support live camera registration and metadata storage
- handle RTSP and VMS adapter-based ingestion
- support camera health monitoring and heartbeat checks
- detect offline or degraded sources
- allow camera grouping by zone, district, or route
- support stream connectivity validation before activation

### 6.2 AI Detection and Analytics
- detect vehicles, persons, and relevant objects from video streams
- support object tracking across frames
- compute confidence scores and timestamps
- capture camera source and location metadata with each detection
- support configurable event rules and anomaly detection
- manage asynchronous AI processing from the event pipeline

### 6.3 ANPR and Plate Intelligence
- detect number plates from video frames
- perform OCR and normalize the result into a canonical plate format
- validate confidence and quality thresholds
- associate detections to camera, timestamp, and location
- maintain historical plate sightings across cameras

### 6.4 Watchlist Correlation
- maintain authorized vehicle/person watchlists
- compare detections against watchlists using normalized identifiers
- generate operational alerts for high-risk matches
- maintain match confidence and evidence trail
- allow watchlist administration with approval-oriented workflows

### 6.5 Alerting and Operations
- support multiple alert types with severity levels
- route alerts to command-centre dashboards and operators
- allow acknowledge, resolve, and re-open lifecycle states
- attach evidence, camera, route, and metadata to an alert
- maintain alert audit trail and timeline

### 6.6 GIS and Spatial Intelligence
- visualize camera locations on a map
- show vehicle/person sightings by region
- link alerts to spatial coordinates and participating cameras
- display movement route traces across geography
- allow queries by district, radius, and camera cluster

### 6.7 Investigation and Search
- search by vehicle plate, person, camera, date-time, route, and event
- review related alerts and detections in a timeline
- inspect evidence and source feed references
- filter investigation views by operational context
- export and report summary information

### 6.8 Audit, Governance, and Security
- enforce role-based access control
- store system and operational audit records
- ensure data retention and access control policies
- support secure storage of secrets and system credentials
- capture user actions on alerts, cases, and investigation records

## 7. Non-Functional Requirements

### 7.1 Availability and Resilience
- services must be restartable independently
- camera stream failures must be isolated from overall system health
- critical services should support retry and failover patterns
- health checks and operational alerts should be available for degraded systems

### 7.2 Scalability
- the platform must scale horizontally across API nodes, AI workers, and stream gateways
- event processing must support increased detection and alert throughput
- camera onboarding should not degrade investigation or dashboard workflows

### 7.3 Performance
- alert propagation should be near real time
- API operations should remain responsive under operational load
- AI inference must support configurable sampling strategies
- maps, dashboards, and search should remain usable during high activity periods

### 7.4 Security
- all network communication should be TLS-enabled in production
- RBAC and least privilege must be enforced
- secrets must be securely stored and rotated safely
- audit logs must capture access and operational decisions
- only authorized interfaces should be used for government integrations

### 7.5 Reliability
- event processing must be idempotent where possible
- failed message handling should use dead-letter or retry workflows
- stream reconnection and backend recovery must be resilient
- system health must be observable through logs, metrics, and operational checks

## 8. Data Requirements

### 8.1 Camera Data
- camera ID
- district/zone assignment
- location coordinates
- stream URL and protocol
- source type and vendor adapter
- installation status and last heartbeat

### 8.2 Detection Data
- detection ID
- camera reference
- timestamp
- object type and confidence
- bounding box metadata
- associated route or zone

### 8.3 Vehicle Data
- plate number
- normalized number format
- vehicle make/model (if available)
- color and attributes
- confidence score
- first/last sighting timestamps

### 8.4 Alert Data
- alert ID
- type and severity
- source camera and location
- linked entity (plate/person)
- status lifecycle (new/open/acknowledged/resolved)
- evidence references and timestamps

### 8.5 Investigation Data
- case ID
- associated entity or event
- investigator and permissions
- notes and timeline entries
- related evidence and alert chain

## 9. Architecture Requirements

SENTINEL should operate as a modular platform with a clear separation between ingestion, intelligence, event processing, API, and presentation layers.

### 9.1 Core Layers
- Ingestion layer: cameras, RTSP, VMS adapters, stream gateways
- AI layer: detection, OCR, object tracking, event inference
- Intelligence layer: watchlist matching, correlation, vehicle history
- Event layer: Kafka or equivalent message bus
- API layer: FastAPI microservice or modular backend
- Storage layer: relational DB, object storage, vector or search support as needed
- Presentation layer: real-time dashboard and investigation UI

### 9.2 Integration Pattern
- all external system integrations must use adapters or service interfaces
- no direct hardcoded dependency on one vendor system
- analytics outputs must be standardized into event payloads
- event-driven processing should decouple ingestion from downstream correlation

## 10. Hackathon MVP Scope

The MVP must demonstrate the following minimum capabilities:

1. Camera onboarding and camera registry
2. Multiple CCTV feeds and monitoring view
3. Vehicle and person detection
4. ANPR and plate normalization
5. Representative watchlist ingestion and matching
6. Automatic alert generation for watchlist and event matches
7. Historical vehicle sighting and movement tracking
8. Basic GIS map with camera and alert markers
9. Investigation search and evidence review
10. An operational backend with real-time command-centre presentation

## 11. Acceptance Criteria

The application is considered aligned with the SENTINEL master requirement when:

- camera feeds can be registered and health-checked
- live monitoring dashboard is available
- AI detections capture time, confidence, and camera metadata
- ANPR outputs are normalized and stored with evidence metadata
- watchlist entries can be created and matched against detections
- alerts are generated with severity and lifecycle states
- investigations can search and review historical evidence
- map-based operational views are available
- user access and audit flows follow RBAC patterns
- the solution remains demo-safe and clearly labeled with synthetic data

## 12. Compliance and Risk Controls

- no unauthorized government data sources should be used in the demo environment
- all integrations to policing systems must be reversible and governed by access policy
- sensitive identifiers must be handled with strict logging and access restrictions
- security architecture must support auditability, traceability, and accountability

## 13. Delivery Phases

### Phase 1: Foundation
- camera registry and monitoring
- backend services and APIs
- UI shell and dashboard

### Phase 2: Intelligence
- AI detection pipeline
- ANPR processing
- event generation

### Phase 3: Correlation and Operations
- watchlist matching
- alert lifecycle workflow
- investigation search

### Phase 4: GIS and Validation
- map layers, route tracking, operational reporting
- production hardening and telemetry

### Phase 5: Scale and Governance
- distributed deployment, observability, security review, and enterprise readiness

## 14. Success Metrics

- camera onboarding success rate
- stream availability and uptime
- detection throughput per stream
- ANPR confidence and accuracy
- watchlist match latency
- alert generation latency
- cross-camera correlation accuracy
- investigation search speed
- dashboard responsiveness
- system resilience under degraded conditions

## 15. Final Requirement Statement

SENTINEL must be a secure, modular, AI-enabled CCTV intelligence platform for police operations. It must bring fragmented surveillance feeds into a unified command environment, transform video into actionable intelligence, correlate detections with authorized watchlists, and enable fast operational response through alerts, GIS visibility, and investigation workflows.

The current repository is a functional PoC foundation for that vision, deliberately built with synthetic demo data and operational architecture patterns that are ready to evolve toward a larger public-safety deployment.
