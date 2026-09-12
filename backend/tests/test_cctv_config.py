"""
Tests for CCTV configuration and credential protection.
"""
import os
import sys
import pytest

# Ensure backend is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestCCTVConfigLoading:
    """Test that CCTV settings load correctly from environment."""

    def test_settings_have_cctv_fields(self):
        from app.core.config import settings
        assert hasattr(settings, "sentinel_cctv_email")
        assert hasattr(settings, "sentinel_cctv_password")
        assert hasattr(settings, "sentinel_cctv_host")
        assert hasattr(settings, "sentinel_cctv_rtsp_port")
        assert hasattr(settings, "sentinel_cctv_whep_port")
        assert hasattr(settings, "sentinel_cctv_hls_base")

    def test_default_host_is_set(self):
        from app.core.config import settings
        assert settings.sentinel_cctv_host == "103.250.160.189"

    def test_default_hls_base(self):
        from app.core.config import settings
        assert settings.sentinel_cctv_hls_base == "https://cctv.corp8.cloud"

    def test_default_ports(self):
        from app.core.config import settings
        assert settings.sentinel_cctv_rtsp_port == 8554
        assert settings.sentinel_cctv_whep_port == 8889


class TestCredentialValidation:
    """Test credential validation returns safe status."""

    def test_missing_credentials_returns_config_missing(self):
        from app.core.config import validate_cctv_credentials, settings
        original_email = settings.sentinel_cctv_email
        original_pass = settings.sentinel_cctv_password
        try:
            settings.sentinel_cctv_email = ""
            settings.sentinel_cctv_password = ""
            result = validate_cctv_credentials()
            assert result["status"] == "CCTV_CONFIG_MISSING"
            assert result["email_configured"] is False
            assert result["password_configured"] is False
            # CRITICAL: password value must never be in the response
            assert "sentinel_cctv_password" not in str(result)
        finally:
            settings.sentinel_cctv_email = original_email
            settings.sentinel_cctv_password = original_pass

    def test_partial_credentials_reports_missing(self):
        from app.core.config import validate_cctv_credentials, settings
        original_email = settings.sentinel_cctv_email
        original_pass = settings.sentinel_cctv_password
        try:
            settings.sentinel_cctv_email = "test@example.com"
            settings.sentinel_cctv_password = ""
            result = validate_cctv_credentials()
            assert result["status"] == "CCTV_CONFIG_MISSING"
            assert result["email_configured"] is True
            assert result["password_configured"] is False
        finally:
            settings.sentinel_cctv_email = original_email
            settings.sentinel_cctv_password = original_pass

    def test_full_credentials_returns_ok(self):
        from app.core.config import validate_cctv_credentials, settings
        original_email = settings.sentinel_cctv_email
        original_pass = settings.sentinel_cctv_password
        try:
            settings.sentinel_cctv_email = "test@example.com"
            settings.sentinel_cctv_password = "XXXX-XXXX-XXXX"
            result = validate_cctv_credentials()
            assert result["status"] == "CCTV_CONFIG_OK"
            # Password must NEVER appear in the result
            assert "XXXX-XXXX-XXXX" not in str(result)
            assert "password" not in {k.lower() for k in result.keys()} - {"password_configured"}
        finally:
            settings.sentinel_cctv_email = original_email
            settings.sentinel_cctv_password = original_pass


class TestCredentialProtection:
    """Test that credentials are never exposed in unsafe ways."""

    def test_password_not_in_hls_url(self):
        from app.services.cctv_service import get_hls_url
        url = get_hls_url("cam11")
        assert "password" not in url.lower()
        assert "@" not in url

    def test_rtsp_url_not_generated_without_credentials(self):
        from app.services.cctv_service import get_safe_rtsp_url
        from app.core.config import settings
        original_email = settings.sentinel_cctv_email
        original_pass = settings.sentinel_cctv_password
        try:
            settings.sentinel_cctv_email = ""
            settings.sentinel_cctv_password = ""
            url = get_safe_rtsp_url("cam11")
            assert url is None
        finally:
            settings.sentinel_cctv_email = original_email
            settings.sentinel_cctv_password = original_pass

    def test_rtsp_url_encodes_email(self):
        from app.services.cctv_service import get_safe_rtsp_url
        from app.core.config import settings
        original_email = settings.sentinel_cctv_email
        original_pass = settings.sentinel_cctv_password
        try:
            settings.sentinel_cctv_email = "user@example.com"
            settings.sentinel_cctv_password = "testpass"
            url = get_safe_rtsp_url("cam11")
            assert url is not None
            # @ in the email must be encoded as %40
            assert "user%40example.com" in url
            # The URL should have exactly one @ separating creds from host
            parts = url.split("://", 1)[1]
            assert parts.count("@") == 1
        finally:
            settings.sentinel_cctv_email = original_email
            settings.sentinel_cctv_password = original_pass

    def test_rtsp_url_uses_tcp_port(self):
        from app.services.cctv_service import get_safe_rtsp_url
        from app.core.config import settings
        original_email = settings.sentinel_cctv_email
        original_pass = settings.sentinel_cctv_password
        try:
            settings.sentinel_cctv_email = "user@example.com"
            settings.sentinel_cctv_password = "testpass"
            url = get_safe_rtsp_url("cam11")
            assert ":8554/" in url
            assert url.startswith("rtsp://")
        finally:
            settings.sentinel_cctv_email = original_email
            settings.sentinel_cctv_password = original_pass
