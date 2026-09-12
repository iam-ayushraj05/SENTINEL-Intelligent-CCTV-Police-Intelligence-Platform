import sys
import os
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("sentinel.ai.third_party_bridge")

# Add third-party ai-surveillance-system path
THIRD_PARTY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ai-surveillance-system" / "surveillance-platform"
ALT_THIRD_PARTY_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "ai-surveillance-system" / "surveillance-platform"

if THIRD_PARTY_PATH.exists() and str(THIRD_PARTY_PATH) not in sys.path:
    sys.path.append(str(THIRD_PARTY_PATH))
    logger.info("Added third-party path: %s", THIRD_PARTY_PATH)
elif ALT_THIRD_PARTY_PATH.exists() and str(ALT_THIRD_PARTY_PATH) not in sys.path:
    sys.path.append(str(ALT_THIRD_PARTY_PATH))
    logger.info("Added third-party path: %s", ALT_THIRD_PARTY_PATH)



class AISurveillanceBridge:
    """
    Bridge to third-party AI surveillance repository components.
    Safely handles module availability and initialization.
    """

    def __init__(self):
        self.available_modules = {}
        self._inspect_and_bind()

    def _inspect_and_bind(self):
        # 1. Weapon Detection System
        try:
            from weapon_detection_system import WeaponDetectionSystem
            self.available_modules["weapon"] = WeaponDetectionSystem
            logger.info("Third-party WeaponDetectionSystem available")
        except Exception as e:
            logger.debug("Third-party WeaponDetectionSystem not loaded: %s", e)

        # 2. Fire Detection System
        try:
            from fire_detection_system import FireDetectionSystem
            self.available_modules["fire"] = FireDetectionSystem
            logger.info("Third-party FireDetectionSystem available")
        except Exception as e:
            logger.debug("Third-party FireDetectionSystem not loaded: %s", e)

        # 3. HAR System
        try:
            from har_system import HumanActionRecognitionSystem
            self.available_modules["har"] = HumanActionRecognitionSystem
            logger.info("Third-party HAR System available")
        except Exception as e:
            logger.debug("Third-party HAR System not loaded: %s", e)

        # 4. Facial Recognition System
        try:
            from facial_recognition_system import FacialRecognitionSystem
            self.available_modules["face"] = FacialRecognitionSystem
            logger.info("Third-party FacialRecognitionSystem available")
        except Exception as e:
            logger.debug("Third-party FacialRecognitionSystem not loaded: %s", e)

        # 5. License Plate Recognition System
        try:
            from license_plate_recognition_system import LicensePlateRecognitionSystem
            self.available_modules["anpr"] = LicensePlateRecognitionSystem
            logger.info("Third-party LicensePlateRecognitionSystem available")
        except Exception as e:
            logger.debug("Third-party LicensePlateRecognitionSystem not loaded: %s", e)

    def is_available(self, module_key: str) -> bool:
        return module_key in self.available_modules

    def get_module_class(self, module_key: str) -> Optional[Any]:
        return self.available_modules.get(module_key)


ai_bridge = AISurveillanceBridge()
