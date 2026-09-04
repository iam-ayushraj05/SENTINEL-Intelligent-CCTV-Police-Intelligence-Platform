# SENTINEL --- UI/UX Design

## 1. Design Direction

Sentinel should feel like a professional police command-and-control
product rather than a generic AI dashboard.

Design priorities: - information density without clutter; - fast
recognition of alerts; - GIS-first operational context; - clear
hierarchy; - keyboard-friendly workflows; - responsive layouts; -
accessible contrast; - consistent status indicators.

## 2. Navigation

``` text
SENTINEL
|
+-- Dashboard
+-- Live Cameras
+-- Map / GIS
+-- Alerts
+-- Vehicles
+-- Investigation
+-- Reports
+-- Camera Registry
+-- Watchlists
+-- System Health
+-- Administration
```

## 3. Dashboard

Top cards: - Cameras online. - Cameras degraded. - Active alerts. - AI
events. - Vehicles tracked.

Main layout: - Large GIS map. - Active alert panel. - Recent events. -
Camera health.

## 4. Live Camera Screen

Features: - Camera grid. - Full-screen viewer. - Search. -
District/department filter. - Online/offline filter. - AI overlays. -
Camera metadata.

Overlay example:

``` text
VEHICLE
GJXX1234
96%
TRACK: T-8921
```

## 5. GIS Screen

Layers: - Cameras. - Alerts. - Vehicle sightings. - Vehicle routes. -
District boundaries.

Interactions: - click camera; - click alert; - search vehicle; - time
slider; - filter by event; - fit route.

## 6. Alert Center

Alert card:

``` text
HIGH PRIORITY
WATCHLIST MATCH

Vehicle: GJXX1234
Camera: CAM027
Time: 18:42:16
Confidence: 96%

[OPEN] [ACKNOWLEDGE]
```

Alert details should show: - source camera; - timestamp; - detection
evidence; - matched record; - previous sightings; - map location; -
related events; - audit history.

## 7. Vehicle Investigation

Search bar:

``` text
[ Enter vehicle number ] [ SEARCH ]
```

Results: - first seen; - last seen; - number of sightings; - cameras; -
timeline; - map route; - associated alerts.

## 8. Camera Registry

Table:

``` text
Camera       Location       Status     Vendor
CAM-001      Ahmedabad      ONLINE     Vendor A
CAM-002      Ahmedabad      ONLINE     Vendor B
CAM-003      Vadodara       DEGRADED   Vendor C
```

Actions: - add; - edit; - health check; - stream test; - disable; - view
details.

## 9. Watchlist Management

Only authorized roles should access watchlist administration.

Fields: - watchlist name; - entity type; - identifier; - priority; -
validity; - status; - source/reference.

## 10. Investigation Workflow

``` text
SEARCH
  |
  v
RESULTS
  |
  v
ENTITY
  |
  +--> TIMELINE
  |
  +--> GIS ROUTE
  |
  +--> CAMERA EVIDENCE
  |
  +--> RELATED ALERTS
  |
  v
REPORT
```

## 11. Responsive Design

Desktop: - three-column operational layout where useful.

Tablet: - two-column layout.

Mobile: - alert-first layout; - map and camera viewer as full-screen
panels; - bottom navigation or compact navigation; - avoid dense tables.

## 12. Accessibility

-   keyboard navigation;
-   semantic controls;
-   sufficient contrast;
-   text labels in addition to status icons;
-   focus states;
-   scalable typography.

## 13. Visual Status System

Use consistent semantic indicators: - ONLINE - OFFLINE - DEGRADED -
LOW - MEDIUM - HIGH - CRITICAL - ACKNOWLEDGED - RESOLVED

Avoid relying on color alone.

## 14. Evidence Viewer

Show: - video/frame; - camera; - exact timestamp; - detection bounding
box; - confidence; - event ID; - chain/audit reference.

The UI should clearly distinguish: **AI observation** from **verified
police information**.
