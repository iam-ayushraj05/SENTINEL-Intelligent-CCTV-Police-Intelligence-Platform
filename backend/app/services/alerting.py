class AlertEngine:
    """Creates and broadcasts operational alerts."""

    async def create_alert(self, event: dict) -> dict:
        return {
            "alert_type": event.get("event_type", "UNKNOWN"),
            "severity": event.get("severity", "LOW"),
            "status": "OPEN",
        }
