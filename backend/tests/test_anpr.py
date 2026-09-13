"""
Tests for ANPR plate normalization and confidence handling.
"""
import os
import sys
import pytest

# backend/ is one level down from project root where ai/ lives
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestPlateNormalization:
    """Test Indian plate normalization rules."""

    def test_standard_plate(self):
        from ai.anpr.normalizer import normalize_plate_number
        assert normalize_plate_number("GJ01AB1234") == "GJ01AB1234"

    def test_plate_with_spaces(self):
        from ai.anpr.normalizer import normalize_plate_number
        assert normalize_plate_number("GJ 05 CD 5678") == "GJ05CD5678"

    def test_plate_with_hyphens(self):
        from ai.anpr.normalizer import normalize_plate_number
        assert normalize_plate_number("GJ-01-AB-1234") == "GJ01AB1234"

    def test_lowercase_normalized_to_upper(self):
        from ai.anpr.normalizer import normalize_plate_number
        assert normalize_plate_number("gj01ab1234") == "GJ01AB1234"

    def test_ocr_misread_O_to_0(self):
        from ai.anpr.normalizer import normalize_plate_number
        # O in digit position should become 0
        result = normalize_plate_number("GJO1AB123O")
        assert result == "GJ01AB1230"

    def test_ocr_misread_I_to_1(self):
        from ai.anpr.normalizer import normalize_plate_number
        result = normalize_plate_number("GJ0IAB12I4")
        assert result == "GJ01AB1214"

    def test_empty_input(self):
        from ai.anpr.normalizer import normalize_plate_number
        assert normalize_plate_number("") == ""

    def test_none_input(self):
        from ai.anpr.normalizer import normalize_plate_number
        assert normalize_plate_number(None) == ""

    def test_special_chars_stripped(self):
        from ai.anpr.normalizer import normalize_plate_number
        result = normalize_plate_number("GJ.01/AB#1234")
        assert result == "GJ01AB1234"

    def test_short_plate(self):
        from ai.anpr.normalizer import normalize_plate_number
        result = normalize_plate_number("AB12")
        # Short plates should still be cleaned
        assert result == "AB12"


class TestPlateConfidence:
    """Test that low confidence plates are handled correctly."""

    @pytest.mark.asyncio
    async def test_empty_crop_returns_zero_confidence(self):
        from ai.anpr.ocr import PlateOCR
        ocr = PlateOCR()
        result = await ocr.read_plate(None)
        assert result["ocr_confidence"] == 0.0
        assert result["raw_text"] == ""
        assert result["normalized_plate"] == ""

    @pytest.mark.asyncio
    async def test_plate_detector_returns_expected_fields(self):
        """PlateDetector.process_vehicle_crop should return plate_number, normalized_plate, ocr_confidence."""
        from ai.anpr.plate_detector import PlateDetector
        detector = PlateDetector()
        result = await detector.process_vehicle_crop(None)
        # With None input, OCR returns empty
        assert result is not None
        assert "plate_number" in result
        assert "normalized_plate" in result
        assert "ocr_confidence" in result
