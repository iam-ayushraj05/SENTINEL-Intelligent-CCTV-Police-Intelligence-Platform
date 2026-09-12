import asyncio
import logging
import os
from typing import Any
import httpx
from ai.pipeline.processor import StreamProcessor
from ai.streaming.catalogue import CameraCatalogue
from ai.streaming.capture import ReconnectBackoff, RtspCapture

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel.ai_worker")


def resolve_stream_url(stream_url: str) -> str:
    if "youtube.com/" not in stream_url and "youtu.be/" not in stream_url:
        return stream_url
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("yt-dlp is required when AI_STREAM_URL is a YouTube URL") from exc
    options = {"quiet": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(stream_url, download=False)
    formats = [item for item in (info or {}).get("formats", []) if item.get("url") and item.get("vcodec") not in (None, "none")]
    formats.sort(key=lambda item: (item.get("height") or 0, item.get("tbr") or 0), reverse=True)
    resolved = formats[0].get("url") if formats else (info or {}).get("url")
    if not resolved:
        raise RuntimeError("YouTube did not return a playable video format")
    return resolved


async def process_camera_stream(camera_id: str, stream_url: str, processor: StreamProcessor, client: httpx.AsyncClient, backend_url: str, frame_interval_ms: float = 500.0):
    """Worker task loop for processing a single camera stream."""
    logger.info("Starting AI worker loop for camera %s (sampling interval: %.0f ms)", camera_id, frame_interval_ms)
    capture: RtspCapture | None = None
    backoff = ReconnectBackoff()
    last_process_time = 0.0

    while True:
        try:
            if capture is None:
                resolved_url = await asyncio.to_thread(resolve_stream_url, stream_url)
                capture = RtspCapture(resolved_url)

            if capture.capture is None and not await capture.open():
                await capture.close()
                capture = None
                delay = backoff.failure_delay()
                logger.warning("Camera stream %s unavailable; retrying in %.1fs", camera_id, delay)
                await asyncio.sleep(delay)
                continue

            backoff.reset()
            captured = await capture.read()
            if captured is None:
                await capture.close()
                capture = None
                delay = backoff.failure_delay()
                logger.warning("Camera stream %s disconnected; retrying in %.1fs", camera_id, delay)
                await asyncio.sleep(delay)
                continue

            now_ms = asyncio.get_event_loop().time() * 1000.0
            if now_ms - last_process_time < frame_interval_ms:
                await asyncio.sleep(0.02)
                continue
            last_process_time = now_ms

            result = await processor.process_frame(camera_id, captured.frame, pts_ms=captured.pts_ms)
            if result["events"] or result["detections"]:
                response = await client.post(
                    f"{backend_url}/detections/ingest",
                    json={
                        "camera_id": camera_id,
                        "detections": result["detections"],
                        "events": [
                            {
                                "camera_id": camera_id,
                                "event_type": event["event_type"],
                                "confidence": event.get("confidence", 0),
                                "metadata_json": {**event.get("metadata", {}), "pts_ms": captured.pts_ms},
                            }
                            for event in result["events"]
                        ],
                    },
                )
                response.raise_for_status()
            await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            if capture is not None:
                await capture.close()
            raise
        except Exception:
            logger.exception("AI worker error on camera %s", camera_id)
            if capture is not None:
                await capture.close()
                capture = None
            await asyncio.sleep(backoff.failure_delay())


async def main():
    logger.info("Starting Sentinel AI Analytics Worker Pool...")
    processor = StreamProcessor()
    backend_url = os.environ.get("SENTINEL_API_URL", "http://localhost:8000/api/v1")
    camera_id = os.environ.get("AI_CAMERA_ID")
    stream_url = os.environ.get("AI_STREAM_URL")
    catalogue_url = os.environ.get("AI_CATALOGUE_URL", "http://localhost:8000/api/v1/cameras/ingest")
    max_ai_cameras = int(os.environ.get("MAX_AI_CAMERAS", "4"))
    frame_interval_ms = float(os.environ.get("AI_FRAME_INTERVAL_MS", "500"))

    cameras_to_process = []

    if camera_id and stream_url:
        cameras_to_process.append((camera_id, stream_url))
    elif catalogue_url:
        try:
            catalogue = CameraCatalogue(catalogue_url)
            fetched = await catalogue.fetch()
            if camera_id and camera_id.lower() != "all":
                target = next((c for c in fetched if c.camera_id == camera_id), None)
                if target and target.rtsp_url:
                    cameras_to_process.append((target.camera_id, target.rtsp_url))
            else:
                for c in fetched[:max_ai_cameras]:
                    if c.rtsp_url:
                        cameras_to_process.append((c.camera_id, c.rtsp_url))
        except Exception as exc:
            logger.warning("Could not load catalogue from %s: %s", catalogue_url, exc)

    if not cameras_to_process:
        # Fallback to cam11
        default_email = urllib.parse.quote(os.environ.get("SENTINEL_CCTV_EMAIL", ""), safe="")
        default_pass = urllib.parse.quote(os.environ.get("SENTINEL_CCTV_PASSWORD", ""), safe="")
        host = os.environ.get("SENTINEL_CCTV_HOST", "103.250.160.189")
        port = os.environ.get("SENTINEL_CCTV_RTSP_PORT", "8554")
        fallback_url = f"rtsp://{default_email}:{default_pass}@{host}:{port}/stream/cam11"
        cameras_to_process.append(("cam11", fallback_url))

    logger.info("Launching AI workers for %d camera(s) (Max Concurrency: %d)", len(cameras_to_process), max_ai_cameras)

    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [
            asyncio.create_task(
                process_camera_stream(cam_id, url, processor, client, backend_url, frame_interval_ms)
            )
            for cam_id, url in cameras_to_process[:max_ai_cameras]
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    import urllib.parse
    asyncio.run(main())
