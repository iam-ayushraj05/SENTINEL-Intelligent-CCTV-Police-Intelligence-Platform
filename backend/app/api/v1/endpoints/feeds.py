import uuid
import mimetypes
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    from app.core.database import select, AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.camera import Camera, DriveFile
from app.models.alert import Alert
from app.models.audit import AuditLog

router = APIRouter()


def _resolve_youtube_url(source_url: str) -> str:
    try:
        import yt_dlp
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="yt-dlp is required for the configured YouTube camera source") from exc
    try:
        options = {"quiet": True, "noplaylist": True}
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(source_url, download=False)
        formats = (info or {}).get("formats", [])
        candidates = [item for item in formats if item.get("url") and item.get("vcodec") not in (None, "none")]
        candidates.sort(key=lambda item: (item.get("height") or 0, item.get("tbr") or 0), reverse=True)
        resolved = candidates[0].get("url") if candidates else (info or {}).get("url")
        if not resolved:
            raise ValueError("No playable media URL returned")
        return resolved
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to resolve YouTube camera source: {exc}") from exc


@router.get("/local-camera-video")
async def local_camera_video():
    if settings.local_camera_youtube_url:
        return RedirectResponse(_resolve_youtube_url(settings.local_camera_youtube_url))
    video_path = Path(settings.local_camera_video_path)
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Configured local camera video was not found")
    media_type = mimetypes.guess_type(video_path.name)[0] or "application/octet-stream"
    return FileResponse(video_path, media_type=media_type, filename=video_path.name)


@router.get("/drive-videos", response_model=list[dict])
async def list_drive_videos(db: AsyncSession = Depends(get_db)):
    stmt = select(DriveFile).order_by(DriveFile.created_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all() if hasattr(result, "scalars") else []
    return [{
        "id": str(item.id),
        "file_name": item.file_name,
        "file_type": item.file_type,
        "drive_path": item.drive_path,
        "thumbnail_url": item.thumbnail_url,
        "processing_status": item.processing_status,
        "ai_status": item.ai_status,
        "uploaded_at": item.uploaded_at.isoformat() if item.uploaded_at else None,
    } for item in rows]


@router.post("/drive-videos/{drive_id}/add-to-analysis")
async def add_drive_video_to_analysis(drive_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    drive_file = await db.get(DriveFile, drive_id)
    if not drive_file:
        raise HTTPException(status_code=404, detail="Drive file not found")
    camera_code = f"CAM-DRIVE-{uuid.uuid4().hex[:4].upper()}"
    camera = Camera(
        id=uuid.uuid4(),
        camera_code=camera_code,
        name=drive_file.file_name,
        description="Imported Google Drive video feed",
        zone="Drive Import",
        camera_type="VIDEO_FILE",
        protocol="FILE",
        feed_type="VIDEO_FILE",
        source_url=drive_file.drive_path,
        stream_url=drive_file.drive_path,
        status="ONLINE",
        is_active=True,
        fps=24,
        resolution="1080p",
        ai_detection_status="READY",
        metadata_json={"drive_file_id": str(drive_file.id), "source": "google_drive"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(camera)
    drive_file.processing_status = "ADDED_TO_ANALYSIS"
    drive_file.ai_status = "QUEUED"
    db.add(AuditLog(
        id=uuid.uuid4(),
        username="operator",
        action="DRIVE_VIDEO_ACCEPTED",
        resource=f"Drive:{drive_file.file_name}",
        result="SUCCESS",
        timestamp=datetime.utcnow(),
    ))
    await db.commit()
    return {"camera_id": str(camera.id), "camera_code": camera_code, "status": "analysis_started"}


@router.post("/drive-videos/{drive_id}/ignore")
async def ignore_drive_video(drive_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    drive_file = await db.get(DriveFile, drive_id)
    if not drive_file:
        raise HTTPException(status_code=404, detail="Drive file not found")
    drive_file.is_ignored = True
    drive_file.processing_status = "IGNORED"
    await db.commit()
    return {"status": "ignored", "drive_id": str(drive_file.id)}


@router.post("/alerts/{alert_id}/verify")
async def verify_alert(alert_id: uuid.UUID, payload: dict, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.verification_status = payload.get("verification_status") or "VERIFIED"
    alert.status = "ACKNOWLEDGED"
    alert.metadata_json = {**(alert.metadata_json or {}), "verification_status": alert.verification_status}
    await db.commit()
    return {"status": "updated", "alert_id": str(alert.id), "verification_status": alert.verification_status}
