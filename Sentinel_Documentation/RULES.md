# SENTINEL --- Engineering and Product Rules

## 1. Architecture Rules

1.  Keep services modular.
2.  Do not couple AI models directly to the frontend.
3.  Do not put vendor-specific logic into core business services.
4.  All integrations must go through adapters.
5.  Use versioned APIs.
6.  Use asynchronous events for high-volume analytics.
7.  Keep stateful and stateless responsibilities separated.

## 2. CCTV Rules

1.  Camera IDs must be globally unique.
2.  Every camera must have ownership/department metadata.
3.  Stream credentials must never be stored in source code.
4.  Stream URLs should be treated as secrets where applicable.
5.  Every stream should have health monitoring.
6.  Failed connections must retry with backoff.
7.  The system must tolerate cameras going offline.

## 3. AI Rules

1.  Every detection must have a timestamp.
2.  Every detection must identify its source camera.
3.  Store model name/version with AI output where practical.
4.  Store confidence scores.
5.  Never present an uncertain AI output as verified fact.
6.  ANPR should use normalization and multi-frame consistency.
7.  AI models must be replaceable without rewriting the API.

## 4. Watchlist Rules

1.  Watchlists require authorized access.
2.  Watchlist records must have a source/reference.
3.  Expired entries must not generate active matches.
4.  Matches must include confidence and evidence.
5.  A watchlist match is an alert for human verification, not an
    automatic conclusion.

## 5. Alert Rules

Severity:

``` text
LOW
MEDIUM
HIGH
CRITICAL
```

Every alert must contain: - alert ID; - alert type; - timestamp; -
source camera; - location; - confidence where applicable; - evidence
reference; - current status.

Alert lifecycle:

``` text
OPEN
 ↓
ACKNOWLEDGED
 ↓
RESOLVED
```

## 6. Data Rules

1.  Use UTC timestamps internally.
2.  Store geographic data using WGS84.
3.  Normalize vehicle identifiers before matching.
4.  Use UUIDs for primary identifiers.
5.  Use migrations for schema changes.
6.  Add indexes to high-volume query paths.
7.  Partition high-volume time-series tables at production scale.

## 7. API Rules

1.  APIs must be versioned.
2.  Validate all request payloads.
3.  Return consistent error structures.
4.  Enforce authorization server-side.
5.  Never trust frontend permission checks.
6.  Use pagination for lists.
7.  Use filtering for large datasets.
8.  Generate request IDs for tracing.

## 8. Security Rules

1.  TLS for external and inter-service traffic where supported.
2.  Secrets belong in environment/secrets management, never Git.
3.  Use least privilege.
4.  Log security-sensitive actions.
5.  Protect administrative endpoints.
6.  Rate-limit exposed APIs.
7.  Validate uploaded files.
8.  Maintain backup and recovery procedures.

## 9. Frontend Rules

1.  Dashboard must remain operationally focused.
2.  Alert information must be immediately visible.
3.  Do not hide critical metadata behind unnecessary interactions.
4.  Every status indicator needs a text label.
5.  Support responsive layouts.
6.  Loading, empty and error states are required.
7.  Avoid fake real-time behavior; use actual WebSocket/event updates in
    the PoC.

## 10. Investigation Rules

1.  Search results must show source and timestamp.
2.  Evidence must be linked to the originating event.
3.  Timeline ordering must be deterministic.
4.  Route visualizations must identify uncertainty.
5.  Exported reports must include generation time and audit information.

## 11. Testing Rules

Required tests: - unit tests; - API tests; - database tests; - connector
tests; - AI pipeline tests; - event processing tests; - WebSocket
tests; - end-to-end PoC test; - load tests.

## 12. Demo Rules

The core demo must work without manual database manipulation during the
presentation.

Preferred flow:

``` text
ONBOARD
→ VIEW
→ DETECT
→ IDENTIFY
→ CORRELATE
→ ALERT
→ TRACE
→ INVESTIGATE
```

## 13. Development Rule

Build the smallest end-to-end vertical slice first:

``` text
ONE CAMERA
→ ONE VEHICLE
→ ONE PLATE
→ ONE WATCHLIST
→ ONE ALERT
→ ONE GIS ROUTE
```

Then scale horizontally.

## 14. Production Boundary

The hackathon PoC may use representative/synthetic data and simulated
external integrations where authorized. Production deployment must use
approved government interfaces, authentication, security controls,
data-sharing agreements, retention policies, and operational procedures.
