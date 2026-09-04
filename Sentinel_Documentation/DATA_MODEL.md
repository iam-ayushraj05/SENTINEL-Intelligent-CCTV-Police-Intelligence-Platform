# SENTINEL --- Data Model

## 1. Entity Relationship Overview

``` text
Department
    |
    +---- Camera ---- CameraStream
    |       |
    |       +---- Detection ---- Event
    |       |
    |       +---- VehicleSighting ---- Vehicle
    |
    +---- VMSSystem

Watchlist
    |
    +---- WatchlistEntry
              |
              +---- Alert

Vehicle
    |
    +---- VehicleSighting
              |
              +---- RouteSegment

User
    |
    +---- AuditLog
```

## 2. Departments

``` sql
CREATE TABLE departments (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    contact JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 3. VMS Systems

``` sql
CREATE TABLE vms_systems (
    id UUID PRIMARY KEY,
    department_id UUID REFERENCES departments(id),
    name VARCHAR(200) NOT NULL,
    vendor VARCHAR(100),
    version VARCHAR(100),
    endpoint TEXT,
    protocol VARCHAR(50),
    status VARCHAR(30) NOT NULL,
    credentials_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 4. Cameras

``` sql
CREATE TABLE cameras (
    id UUID PRIMARY KEY,
    camera_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    department_id UUID REFERENCES departments(id),
    vms_id UUID REFERENCES vms_systems(id),
    vendor VARCHAR(100),
    model VARCHAR(100),
    camera_type VARCHAR(50),
    protocol VARCHAR(50),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location GEOGRAPHY(POINT, 4326),
    status VARCHAR(30) NOT NULL DEFAULT 'UNKNOWN',
    retention_days INTEGER,
    last_heartbeat TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 5. Camera Streams

``` sql
CREATE TABLE camera_streams (
    id UUID PRIMARY KEY,
    camera_id UUID NOT NULL REFERENCES cameras(id),
    stream_type VARCHAR(30),
    protocol VARCHAR(30),
    source_url TEXT,
    resolution VARCHAR(30),
    fps NUMERIC,
    bitrate INTEGER,
    active BOOLEAN DEFAULT true
);
```

## 6. Detections

``` sql
CREATE TABLE detections (
    id UUID PRIMARY KEY,
    camera_id UUID NOT NULL REFERENCES cameras(id),
    timestamp TIMESTAMPTZ NOT NULL,
    frame_id VARCHAR(200),
    object_type VARCHAR(50) NOT NULL,
    confidence NUMERIC(5,4),
    bbox JSONB,
    track_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_detections_camera_time
ON detections(camera_id, timestamp DESC);
```

## 7. Vehicles

``` sql
CREATE TABLE vehicles (
    id UUID PRIMARY KEY,
    plate_number VARCHAR(100),
    plate_normalized VARCHAR(100) INDEX,
    vehicle_type VARCHAR(50),
    color VARCHAR(50),
    make VARCHAR(100),
    model VARCHAR(100),
    appearance_embedding JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 8. Vehicle Sightings

``` sql
CREATE TABLE vehicle_sightings (
    id UUID PRIMARY KEY,
    vehicle_id UUID REFERENCES vehicles(id),
    camera_id UUID NOT NULL REFERENCES cameras(id),
    timestamp TIMESTAMPTZ NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location GEOGRAPHY(POINT, 4326),
    plate_confidence NUMERIC(5,4),
    vehicle_confidence NUMERIC(5,4),
    frame_reference TEXT,
    track_id VARCHAR(100),
    metadata JSONB
);

CREATE INDEX idx_vehicle_sightings_vehicle_time
ON vehicle_sightings(vehicle_id, timestamp DESC);
```

## 9. Events

``` sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    camera_id UUID REFERENCES cameras(id),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(30),
    timestamp_start TIMESTAMPTZ NOT NULL,
    timestamp_end TIMESTAMPTZ,
    confidence NUMERIC(5,4),
    status VARCHAR(30) DEFAULT 'OPEN',
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 10. Watchlists

``` sql
CREATE TABLE watchlists (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE watchlist_entries (
    id UUID PRIMARY KEY,
    watchlist_id UUID NOT NULL REFERENCES watchlists(id),
    entity_type VARCHAR(50) NOT NULL,
    identifier VARCHAR(200) NOT NULL,
    display_name VARCHAR(200),
    priority VARCHAR(30),
    status VARCHAR(30) DEFAULT 'ACTIVE',
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    metadata JSONB
);

CREATE INDEX idx_watchlist_identifier
ON watchlist_entries(identifier);
```

## 11. Alerts

``` sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    alert_code VARCHAR(100) UNIQUE NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    event_id UUID REFERENCES events(id),
    watchlist_entry_id UUID REFERENCES watchlist_entries(id),
    camera_id UUID REFERENCES cameras(id),
    entity_id UUID,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    confidence NUMERIC(5,4),
    status VARCHAR(30) DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);
```

## 12. Route Segments

``` sql
CREATE TABLE route_segments (
    id UUID PRIMARY KEY,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    from_camera_id UUID REFERENCES cameras(id),
    to_camera_id UUID REFERENCES cameras(id),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    distance_meters NUMERIC,
    estimated_travel_time_seconds INTEGER,
    confidence NUMERIC(5,4),
    geometry GEOMETRY(LINESTRING, 4326)
);
```

## 13. Users and Audit

``` sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    role VARCHAR(50) NOT NULL,
    department_id UUID REFERENCES departments(id),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB
);
```

## 14. Retention and Indexing

Recommended indexes: - camera + timestamp. - vehicle + timestamp. -
normalized plate. - event type + timestamp. - alert status +
created_at. - PostGIS spatial indexes on geographic columns.

For high-volume production data, partition detections and sightings by
time.
