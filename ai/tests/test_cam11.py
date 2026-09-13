import asyncio
import logging
import os
import sys
import time
import urllib.parse

from ai.streaming.capture import ReconnectBackoff, RtspCapture, sanitize_url_for_logging
from ai.streaming.catalogue import CameraCatalogue

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sentinel.test_cam11")


async def run_cam11_diagnostic(timeout_seconds: float = 15.0) -> dict:
    """
    Diagnostic E2E test runner for CAM11:
    1. Fetch / construct authorized RTSP URL for cam11
    2. Force RTSP TCP mode
    3. Open stream connection
    4. Capture frames and measure presentation timestamps (PTS)
    5. Safely report result without printing secrets
    """
    logger.info("==================================================")
    logger.info("SENTINEL CAM11 END-TO-END STREAM DIAGNOSTIC TEST")
    logger.info("==================================================")

    camera_id = os.environ.get("AI_CAMERA_ID", "cam11")
    email = os.environ.get("SENTINEL_CCTV_EMAIL", "")
    password = os.environ.get("SENTINEL_CCTV_PASSWORD", "")
    host = os.environ.get("SENTINEL_CCTV_HOST", "103.250.160.189")
    port = os.environ.get("SENTINEL_CCTV_RTSP_PORT", "8554")
    catalogue_url = os.environ.get("AI_CATALOGUE_URL")

    stream_url = None

    if catalogue_url:
        logger.info("Fetching camera stream descriptor from catalogue: %s", catalogue_url)
        try:
            catalogue = CameraCatalogue(catalogue_url)
            camera = await catalogue.get(camera_id)
            stream_url = camera.rtsp_url
            logger.info("Resolved stream URL from catalogue for %s", camera_id)
        except Exception as exc:
            logger.warning("Catalogue lookup failed: %s", exc)

    if not stream_url:
        if email and password:
            encoded_email = urllib.parse.quote(email, safe="")
            encoded_pass = urllib.parse.quote(password, safe="")
            stream_url = f"rtsp://{encoded_email}:{encoded_pass}@{host}:{port}/stream/{camera_id}"
            logger.info("Constructed direct authorized RTSP URL for camera %s", camera_id)
        else:
            safe_url = f"rtsp://***:***@{host}:{port}/stream/{camera_id}"
            logger.error("No CCTV email/password provided in environment settings. Safe target URL: %s", safe_url)
            return {
                "success": False,
                "camera_id": camera_id,
                "error": "AUTHENTICATION_CREDENTIALS_MISSING",
                "details": "SENTINEL_CCTV_EMAIL or SENTINEL_CCTV_PASSWORD is not set in environment settings",
                "safe_url": safe_url,
            }

    safe_log_url = sanitize_url_for_logging(stream_url)
    logger.info("Target RTSP endpoint: %s (Transport: TCP)", safe_log_url)

    # Force RTSP TCP transport option in environment
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    capture = RtspCapture(stream_url)
    frames_received = 0
    pts_values = []
    start_time = time.monotonic()

    logger.info("Attempting RTSP TCP connection to %s...", camera_id)

    try:
        is_open = await asyncio.wait_for(capture.open(), timeout=8.0)
        if not is_open:
            logger.warning("RTSP connection to %s failed or 401 Unauthorized. Testing HLS fallback...", camera_id)
            hls_url = f"https://cctv.corp8.cloud/{camera_id}/index.m3u8"
            return await _test_hls_fallback(camera_id, hls_url, safe_log_url, "RTSP_401_UNAUTHORIZED_OR_CLOSED")

        logger.info("Stream opened successfully! Starting frame capture probe...")

        while time.monotonic() - start_time < timeout_seconds and frames_received < 10:
            captured = await capture.read()
            if captured is None or captured.frame is None:
                await asyncio.sleep(0.1)
                continue

            frames_received += 1
            pts = captured.pts_ms
            pts_values.append(pts)

            h, w = captured.frame.shape[:2]
            logger.info("Frame #%d received! Size: %dx%d, PTS: %s ms", frames_received, w, h, f"{pts:.2f}" if pts else "N/A")

        await capture.close()

        if frames_received > 0:
            logger.info("TEST SUCCESS! Captured %d real frames from %s via RTSP TCP", frames_received, camera_id)
            return {
                "success": True,
                "camera_id": camera_id,
                "protocol": "RTSP/TCP",
                "frames_received": frames_received,
                "pts_sample": pts_values,
                "safe_url": safe_log_url,
            }
        else:
            logger.warning("RTSP stream opened but no valid video frames received. Testing HLS fallback...")
            hls_url = f"https://cctv.corp8.cloud/{camera_id}/index.m3u8"
            return await _test_hls_fallback(camera_id, hls_url, safe_log_url, "NO_FRAMES_DELIVERED")

    except asyncio.TimeoutError:
        logger.error("Connection attempt timed out for %s at %s. Testing HLS fallback...", camera_id, safe_log_url)
        await capture.close()
        hls_url = f"https://cctv.corp8.cloud/{camera_id}/index.m3u8"
        return await _test_hls_fallback(camera_id, hls_url, safe_log_url, "NETWORK_TIMEOUT")
    except Exception as exc:
        logger.error("RTSP connection error for %s: %s. Testing HLS fallback...", camera_id, exc)
        await capture.close()
        hls_url = f"https://cctv.corp8.cloud/{camera_id}/index.m3u8"
        return await _test_hls_fallback(camera_id, hls_url, safe_log_url, str(exc))


async def _test_hls_fallback(camera_id: str, hls_url: str, safe_rtsp_url: str, rtsp_error: str) -> dict:
    import httpx
    logger.info("Testing HLS fallback endpoint: %s", hls_url)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(hls_url)
            if resp.status_code == 200 and "#EXTM3U" in resp.text:
                logger.info("HLS Fallback SUCCESS! M3U8 manifest available for %s", camera_id)
                return {
                    "success": True,
                    "camera_id": camera_id,
                    "protocol": "HLS_FALLBACK",
                    "hls_url": hls_url,
                    "safe_rtsp_url": safe_rtsp_url,
                    "rtsp_error": rtsp_error,
                    "manifest_status": 200,
                }
            else:
                logger.warning("HLS Fallback returned HTTP %d for %s", resp.status_code, camera_id)
                return {
                    "success": False,
                    "camera_id": camera_id,
                    "error": f"RTSP: {rtsp_error} | HLS: HTTP {resp.status_code}",
                    "hls_url": hls_url,
                    "safe_rtsp_url": safe_rtsp_url,
                }
    except Exception as exc:
        logger.error("HLS Fallback request error: %s", exc)
        return {
            "success": False,
            "camera_id": camera_id,
            "error": f"RTSP: {rtsp_error} | HLS: {exc}",
            "hls_url": hls_url,
            "safe_rtsp_url": safe_rtsp_url,
        }


def main():
    result = asyncio.run(run_cam11_diagnostic())
    print("\n--- DIAGNOSTIC SUMMARY ---")
    print(f"Camera ID:       {result.get('camera_id')}")
    print(f"Success:         {result.get('success')}")
    print(f"Safe URL:        {result.get('safe_url')}")
    if result.get("success"):
        print(f"Frames Received: {result.get('frames_received')}")
        print(f"PTS Timestamps:  {result.get('pts_sample')}")
    else:
        print(f"Error Code:      {result.get('error')}")
        print(f"Details:         {result.get('details')}")
    print("---------------------------\n")

    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
