import asyncio
import random
import uuid
import logging
from datetime import datetime

try:
    from sqlalchemy import select
except ImportError:
    from app.core.database import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash

from app.models.camera import Camera
from app.models.user import User
from app.models.operations import (
    Department,
    Watchlist,
    WatchlistEntry,
    Investigation,
)
from app.models.vehicle import Vehicle, VehicleSighting
from app.models.alert import Alert, AlertEvent
from app.models.detection import Detection, DetectionEvent
from app.models.audit import AuditLog

from app.services.correlation_engine import evaluate_detection_event
from app.services.websocket_manager import ws_manager


logger = logging.getLogger("sentinel.simulator")


# ============================================================
# DEMO CAMERA CONFIGURATION
# ============================================================
#
# heading:
#   0   = North
#   45  = North-East
#   90  = East
#   135 = South-East
#   180 = South
#   225 = South-West
#   270 = West
#   315 = North-West
#
# orientation:
#   Human-readable direction.
#
# These are DEMO orientations. Change the values to match
# the physical direction of your actual CCTV cameras.
# ============================================================

DEMO_CAMERAS = [
    {
        "code": "CAM-GJ01-001",
        "name": "Ring Road Junction North",
        "zone": "Ahmedabad Central",
        "lat": 23.0225,
        "lng": 72.5714,
        "type": "ANPR",
        "status": "ONLINE",
        "heading": 0.0,
        "orientation": "NORTH",
    },
    {
        "code": "CAM-GJ01-002",
        "name": "SG Highway Express Gate 4",
        "zone": "Ahmedabad West",
        "lat": 23.0900,
        "lng": 72.5342,
        "type": "PTZ",
        "status": "ONLINE",
        "heading": 90.0,
        "orientation": "EAST",
    },
    {
        "code": "CAM-GJ01-003",
        "name": "Kalupur Station Entrance",
        "zone": "Ahmedabad East",
        "lat": 23.0270,
        "lng": 72.6012,
        "type": "FIXED",
        "status": "ONLINE",
        "heading": 180.0,
        "orientation": "SOUTH",
    },
    {
        "code": "CAM-GJ05-001",
        "name": "Majura Gate Circle",
        "zone": "Surat South",
        "lat": 21.1702,
        "lng": 72.8311,
        "type": "ANPR",
        "status": "ONLINE",
        "heading": 270.0,
        "orientation": "WEST",
    },
    {
        "code": "CAM-GJ18-001",
        "name": "Sector 11 Secretariat Plaza",
        "zone": "Gandhinagar Govt Complex",
        "lat": 23.2156,
        "lng": 72.6369,
        "type": "PTZ",
        "status": "ONLINE",
        "heading": 45.0,
        "orientation": "NORTH-EAST",
    },
    {
        "code": "CAM-GJ03-001",
        "name": "Trikon Baug Junction",
        "zone": "Rajkot Center",
        "lat": 22.3039,
        "lng": 70.8022,
        "type": "FIXED",
        "status": "DEGRADED",
        "heading": 135.0,
        "orientation": "SOUTH-EAST",
    },
]


DEMO_PLATES = [
    "GJ01AB1234",
    "GJ05CD5678",
    "GJ18EF9012",
    "GJ01XY9999",
    "GJ06ZZ4321",
]


# ============================================================
# HELPER: CONVERT HEADING TO DIRECTION
# ============================================================

def heading_to_direction(heading: float) -> str:
    """
    Convert compass heading into a human-readable direction.

    0   = North
    45  = North-East
    90  = East
    135 = South-East
    180 = South
    225 = South-West
    270 = West
    315 = North-West
    """

    directions = [
        "NORTH",
        "NORTH-EAST",
        "EAST",
        "SOUTH-EAST",
        "SOUTH",
        "SOUTH-WEST",
        "WEST",
        "NORTH-WEST",
    ]

    index = int((heading + 22.5) // 45) % 8

    return directions[index]


# ============================================================
# HELPER: SAFE UTC TIME
# ============================================================

def utc_now():
    """
    Centralized UTC timestamp helper.
    """
    return datetime.utcnow()


# ============================================================
# SEED DEMO DATABASE
# ============================================================

async def seed_demo_data():
    """
    Seeds initial database entries for a rich demo experience.
    """

    async with AsyncSessionLocal() as db:

        if type(db).__name__ == "DummySession":
            return

        try:

            # ------------------------------------------------
            # CHECK EXISTING CAMERAS
            # ------------------------------------------------

            result = await db.execute(select(Camera))

            cameras = (
                result.scalars().all()
                if hasattr(result, "scalars")
                else []
            )

            if cameras:
                logger.info(
                    "Cameras already exist. Skipping demo database seed."
                )
                return

            logger.info(
                "Seeding initial Sentinel database records..."
            )

            # ------------------------------------------------
            # DEPARTMENT
            # ------------------------------------------------
            #
            # IMPORTANT:
            # Department model does NOT have a `zone` field.
            # Department supports district/state instead.
            #
            # The previous:
            #
            #     zone="Statewide",
            #
            # caused:
            #
            #     'zone' is an invalid keyword argument for Department
            #
            # Therefore zone is intentionally NOT passed here.
            # Camera records below still use their zone field.
            # ------------------------------------------------

            dept = Department(
                id=uuid.uuid4(),
                name="Gujarat State Traffic Police & CCTV Command",
                code="GTP-CCTV-01",
            )

            db.add(dept)

            await db.flush()

            # ------------------------------------------------
            # ADMIN USER
            # ------------------------------------------------

            user1 = User(
                id=uuid.uuid4(),
                username="admin",
                email="admin@sentinel.police.gov.in",
                full_name="Commanding Inspector General A. Sharma",
                hashed_password=get_password_hash("admin123"),
                role="ADMIN",
                badge_number="GJ-POL-001",
                department_id=dept.id,
            )

            # ------------------------------------------------
            # OPERATOR USER
            # ------------------------------------------------

            user2 = User(
                id=uuid.uuid4(),
                username="operator01",
                email="operator01@sentinel.police.gov.in",
                full_name="Sub-Inspector Rajesh Patel",
                hashed_password=get_password_hash("operator123"),
                role="OPERATOR",
                badge_number="GJ-POL-142",
                department_id=dept.id,
            )

            db.add(user1)
            db.add(user2)

            # ------------------------------------------------
            # CREATE CAMERAS
            # ------------------------------------------------

            created_cams = []

            for cam_info in DEMO_CAMERAS:

                heading = float(
                    cam_info.get("heading", 0.0)
                )

                orientation = cam_info.get(
                    "orientation",
                    heading_to_direction(heading),
                )

                cam = Camera(
                    id=uuid.uuid4(),

                    camera_code=cam_info["code"],

                    name=cam_info["name"],

                    description=(
                        f"State Surveillance Camera "
                        f"{cam_info['code']} at "
                        f"{cam_info['zone']}. "
                        f"Camera orientation: {orientation} "
                        f"({heading} degrees)."
                    ),

                    department_id=dept.id,

                    # Camera DOES have a zone field.
                    zone=cam_info["zone"],

                    camera_type=cam_info["type"],

                    manufacturer="Hikvision Sentinel Series",

                    model="DS-2CD2043G2-I",

                    protocol="FILE" if cam_info["code"] == "CAM-GJ01-001" else "RTSP",

                    rtsp_url=(
                        f"rtsp://10.200.4."
                        f"{random.randint(10, 200)}"
                        f":554/live/stream1"
                    ),

                    stream_url=(
                        "http://localhost:8000/api/v1/feeds/local-camera-video"
                        if cam_info["code"] == "CAM-GJ01-001"
                        else "http://localhost:8889/live/"
                        f"{cam_info['code'].lower()}"
                    ),

                    vms_reference=(
                        f"VMS-GJ-{random.randint(1000, 9999)}"
                    ),

                    latitude=cam_info["lat"],

                    longitude=cam_info["lng"],

                    status=cam_info["status"],

                    is_active=True,

                    last_heartbeat=utc_now(),
                )

                # ------------------------------------------------
                # OPTIONAL ORIENTATION ATTRIBUTES
                # ------------------------------------------------

                try:
                    cam.heading = heading
                except Exception:
                    pass

                try:
                    cam.orientation = orientation
                except Exception:
                    pass

                db.add(cam)

                created_cams.append(cam)

            await db.flush()

            # ------------------------------------------------
            # WATCHLIST
            # ------------------------------------------------

            wlist1 = Watchlist(
                id=uuid.uuid4(),
                name="Stolen & Crime-Linked Vehicles",
                description=(
                    "Authorized statewide database of reported "
                    "stolen and wanted vehicles"
                ),
                entity_type="VEHICLE",
                status="ACTIVE",
            )

            db.add(wlist1)

            await db.flush()

            # ------------------------------------------------
            # WATCHLIST ENTRY 1
            # ------------------------------------------------

            wentry1 = WatchlistEntry(
                   id=uuid.uuid4(),
                   watchlist_id=wlist1.id,
                   subject_reference="GJ05CD5678",
                   normalized_reference="GJ05CD5678",
                   source_system="VAHAN_POLICE_FIR",
                   priority="HIGH",
                   active=True,
            )
            # ------------------------------------------------
            # WATCHLIST ENTRY 2
            # ------------------------------------------------

            wentry2 = WatchlistEntry(
                id=uuid.uuid4(),
                watchlist_id=wlist1.id,
                subject_reference="GJ01XY9999",
                normalized_reference="GJ01XY9999",
                source_system="CRIME_BRANCH",
                priority="CRITICAL",
                active=True,
            )   

            db.add(wentry1)
            db.add(wentry2)

            # ------------------------------------------------
            # VEHICLE
            # ------------------------------------------------

            v1 = Vehicle(
                id=uuid.uuid4(),
                plate_number="GJ05CD5678",
                normalized_plate="GJ05CD5678",
                vehicle_type="car",
                color="Silver",
                make="Mahindra",
                model="Bolero",
                first_seen=utc_now(),
                last_seen=utc_now(),
            )

            db.add(v1)

            await db.flush()

            # ------------------------------------------------
            # VEHICLE SIGHTINGS
            # ------------------------------------------------

            for cam in created_cams[:3]:

                sighting = VehicleSighting(
                    id=uuid.uuid4(),

                    vehicle_id=v1.id,

                    plate_text="GJ05CD5678",
                    normalized_plate="GJ05CD5678",

                    camera_id=cam.id,

                    confidence=0.94,

                    crop_image_url=(
                        "https://images.unsplash.com/"
                        "photo-1541872703-74c5e44368f9"
                        "?w=800&q=80"
                    ),

                    timestamp=utc_now(),
                    metadata_json={"normalized_plate": "GJ05CD5678", "vehicle_type": "car", "color": "Silver", "latitude": cam.latitude, "longitude": cam.longitude},
                )

                db.add(sighting)

            # ------------------------------------------------
            # INITIAL ALERT
            # ------------------------------------------------

            alert1 = Alert(
                id=uuid.uuid4(),

                alert_code=(
                    f"ALT-{utc_now().strftime('%Y%m%d%H%M%S')}"
                    "-0001"
                ),

                alert_type="WATCHLIST_MATCH",

                severity="HIGH",

                camera_id=created_cams[0].id,

                title="WATCHLIST MATCH: GJ05CD5678",

                description=(
                    "Sighting of flagged vehicle "
                    "'GJ05CD5678' at Ring Road Junction North. "
                    "Matched against Stolen Vehicles database."
                ),

                confidence=0.96,

                status="OPEN",

                evidence_url=(
                    "https://images.unsplash.com/"
                    "photo-1541872703-74c5e44368f9"
                    "?w=800&q=80"
                ),

                created_at=utc_now(),

                updated_at=utc_now(),
            )

            db.add(alert1)

            # ------------------------------------------------
            # INVESTIGATION
            # ------------------------------------------------

            inv1 = Investigation(
                id=uuid.uuid4(),

                case_number="CASE-2026-GJ-0091",

                title=(
                    "Investigation: Stolen Bolero "
                    "Ring Road Sighting"
                ),

                description=(
                    "Cross-referencing CCTV sightings of "
                    "GJ05CD5678 across Ring Road and "
                    "SG Highway cameras."
                ),

                status="INVESTIGATING",

                assigned_officer_name=(
                    "Sub-Inspector Rajesh Patel"
                ),

                created_at=utc_now(),

                updated_at=utc_now(),
            )

            db.add(inv1)

            # ------------------------------------------------
            # AUDIT LOG
            # ------------------------------------------------

            audit = AuditLog(
                id=uuid.uuid4(),

                username="system",

                action="SYSTEM_INIT",

                resource="DATABASE",

                result="SUCCESS",

                details=(
                    "Sentinel Command Center initialized "
                    "with demo seed data"
                ),

                timestamp=utc_now(),
            )

            db.add(audit)

            # ------------------------------------------------
            # COMMIT
            # ------------------------------------------------

            await db.commit()

            logger.info(
                "Sentinel database seeded successfully!"
            )

        except Exception as err:

            await db.rollback()

            logger.warning(
                f"Demo seeding note: {err}"
            )


# ============================================================
# EVENT SIMULATOR
# ============================================================

async def run_event_simulator_loop():
    """
    Background simulator loop that periodically emits
    demo detection events and alerts.
    """

    await asyncio.sleep(5)

    logger.info(
        "Starting background DEMO AI Event Simulator..."
    )

    event_types = [
        ("PLATE_DETECTED", "LOW"),
        ("PERSON_DETECTED", "LOW"),
        ("VEHICLE_DETECTED", "LOW"),
        ("LOITERING", "MEDIUM"),
        ("LINE_CROSSING", "LOW"),
        ("CROWD_ANOMALY", "HIGH"),
        ("INTRUSION", "HIGH"),
    ]

    while True:

        try:

            await asyncio.sleep(
                random.randint(12, 25)
            )

            async with AsyncSessionLocal() as db:

                # ====================================================
                # DUMMY DATABASE MODE
                # ====================================================

                if type(db).__name__ == "DummySession":

                    cam_index = random.randint(1, 3)

                    cam_code = (
                        f"CAM-GJ01-00{cam_index}"
                    )

                    selected_plate = random.choice(
                        DEMO_PLATES
                    )

                    # Find orientation from demo camera list
                    camera_info = next(
                        (
                            c
                            for c in DEMO_CAMERAS
                            if c["code"] == cam_code
                        ),
                        None,
                    )

                    if camera_info:

                        heading = float(
                            camera_info.get(
                                "heading",
                                0.0,
                            )
                        )

                        orientation = camera_info.get(
                            "orientation",
                            heading_to_direction(
                                heading
                            ),
                        )

                    else:

                        heading = 0.0
                        orientation = "NORTH"

                    evt = {
                        "id": str(uuid.uuid4()),

                        "camera_id": str(uuid.uuid4()),

                        "camera_code": cam_code,

                        "camera_name": (
                            f"Surveillance Node "
                            f"{cam_code}"
                        ),

                        "event_type": "PLATE_DETECTED",

                        "object_type": "car",

                        "confidence": round(
                            random.uniform(
                                0.85,
                                0.98,
                            ),
                            2,
                        ),

                        "plate_number": selected_plate,

                        "timestamp": utc_now().isoformat(),

                        "demo_mode": True,

                        "camera_heading": heading,

                        "camera_orientation": orientation,
                    }

                    await ws_manager.broadcast_event(
                        evt
                    )

                    continue

                # ====================================================
                # GET CAMERAS
                # ====================================================

                result = await db.execute(
                    select(Camera)
                )

                cameras = (
                    result.scalars().all()
                    if hasattr(result, "scalars")
                    else []
                )

                if not cameras:
                    continue

                # ====================================================
                # SELECT RANDOM CAMERA
                # ====================================================

                cam = random.choice(cameras)

                evt_type, default_sev = random.choice(
                    event_types
                )

                confidence = round(
                    random.uniform(
                        0.78,
                        0.98,
                    ),
                    2,
                )

                # ====================================================
                # CAMERA ORIENTATION
                # ====================================================

                heading = getattr(
                    cam,
                    "heading",
                    None,
                )

                orientation = getattr(
                    cam,
                    "orientation",
                    None,
                )

                if heading is None or orientation is None:

                    camera_info = next(
                        (
                            c
                            for c in DEMO_CAMERAS
                            if c["code"]
                            == cam.camera_code
                        ),
                        None,
                    )

                    if camera_info:

                        heading = float(
                            camera_info.get(
                                "heading",
                                0.0,
                            )
                        )

                        orientation = camera_info.get(
                            "orientation",
                            heading_to_direction(
                                heading
                            ),
                        )

                    else:

                        heading = 0.0
                        orientation = "NORTH"

                heading = float(heading)

                # ====================================================
                # PLATE
                # ====================================================

                selected_plate = None

                if (
                    evt_type == "PLATE_DETECTED"
                    or random.random() < 0.3
                ):

                    selected_plate = random.choice(
                        DEMO_PLATES
                    )

                # ====================================================
                # OBJECT CLASS
                # ====================================================

                if selected_plate:

                    object_class = "car"

                elif (
                    "PERSON" in evt_type
                    or "LOITER" in evt_type
                ):

                    object_class = "person"

                else:

                    object_class = "motorcycle"

                # ====================================================
                # DETECTION
                # ====================================================

                detection = Detection(
                    id=uuid.uuid4(),

                    camera_id=cam.id,

                    object_class=object_class,

                    confidence=confidence,

                    bbox={
                        "x": round(
                            random.uniform(
                                0.1,
                                0.5,
                            ),
                            2,
                        ),

                        "y": round(
                            random.uniform(
                                0.1,
                                0.5,
                            ),
                            2,
                        ),

                        "w": 0.25,

                        "h": 0.25,
                    },

                    track_id=(
                        f"TRK-{random.randint(100, 999)}"
                    ),

                    timestamp=utc_now(),
                )

                db.add(detection)

                # ====================================================
                # VEHICLE SIGHTING
                # ====================================================

                if selected_plate:

                    normalized = (
                        selected_plate
                        .replace("-", "")
                        .replace(" ", "")
                        .upper()
                    )

                    sighting = VehicleSighting(
                        id=uuid.uuid4(),

                        plate_text=selected_plate,
                        normalized_plate=normalized,

                        camera_id=cam.id,

                        confidence=confidence,

                        crop_image_url=(
                            "https://images.unsplash.com/"
                            "photo-1541872703-74c5e44368f9"
                            "?w=800&q=80"
                        ),

                        timestamp=utc_now(),
                        metadata_json={"normalized_plate": normalized, "vehicle_type": "car", "color": "Silver", "latitude": cam.latitude, "longitude": cam.longitude},
                    )

                    db.add(sighting)

                # ====================================================
                # COMMIT DETECTION
                # ====================================================

                await db.commit()

                # ====================================================
                # WEBSOCKET EVENT
                # ====================================================

                event_payload = {

                    "id": str(
                        detection.id
                    ),

                    "camera_id": str(
                        cam.id
                    ),

                    "camera_code": (
                        cam.camera_code
                    ),

                    "camera_name": (
                        cam.name
                    ),

                    "event_type": (
                        evt_type
                        if not selected_plate
                        else "PLATE_DETECTED"
                    ),

                    "object_type": (
                        getattr(
                            detection,
                            "object_class",
                            "vehicle",
                        )
                    ),

                    "confidence": confidence,

                    "plate_number": (
                        selected_plate
                    ),

                    "timestamp": (
                        utc_now().isoformat()
                    ),

                    "demo_mode": True,

                    # ==========================================
                    # ORIENTATION DATA
                    # ==========================================

                    "camera_heading": heading,

                    "camera_orientation": (
                        orientation
                    ),

                    # ==========================================
                    # GPS DATA
                    # ==========================================

                    "camera_latitude": (
                        cam.latitude
                    ),

                    "camera_longitude": (
                        cam.longitude
                    ),
                }

                await ws_manager.broadcast_event(
                    event_payload
                )

                # ====================================================
                # CORRELATION ENGINE
                # ====================================================

                await evaluate_detection_event(

                    db=db,

                    camera_id=cam.id,

                    event_type=evt_type,

                    subject_reference=(
                        selected_plate
                    ),

                    confidence=confidence,

                    evidence_url=(
                        "https://images.unsplash.com/"
                        "photo-1541872703-74c5e44368f9"
                        "?w=800&q=80"
                    ),

                    metadata_json={

                        "simulated": True,

                        "camera_heading": heading,

                        "camera_orientation": (
                            orientation
                        ),

                        "camera_latitude": (
                            cam.latitude
                        ),

                        "camera_longitude": (
                            cam.longitude
                        ),
                    },
                )

        # ============================================================
        # SHUTDOWN
        # ============================================================

        except asyncio.CancelledError:

            logger.info(
                "Event simulator cancelled."
            )

            break

        # ============================================================
        # ERROR HANDLING
        # ============================================================

        except Exception as e:

            logger.error(
                f"Error in Event Simulator: {e}",
                exc_info=True,
            )

            # Prevent a continuous error loop
            await asyncio.sleep(3)

