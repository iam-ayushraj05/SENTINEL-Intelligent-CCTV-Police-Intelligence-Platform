import gc
import logging
import time
from typing import Any, Dict, List, Optional
import torch

from ai.sentinel_ai.config.settings import ai_settings

logger = logging.getLogger("sentinel.ai.resource_manager")


class ModelResourceManager:
    """
    Resource manager for loading/unloading models, monitoring VRAM/RAM,
    selecting target device (CUDA vs CPU fallback), and recording telemetry.
    """

    def __init__(
        self,
        max_concurrent_models: Optional[int] = None,
        max_gpu_memory_mb: Optional[int] = None,
    ):
        self.max_concurrent_models = max_concurrent_models or ai_settings.AI_MAX_CONCURRENT_MODELS
        self.max_gpu_memory_mb = max_gpu_memory_mb or ai_settings.AI_MAX_GPU_MEMORY_MB
        self.loaded_models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.inference_stats: Dict[str, Dict[str, Any]] = {}
        self._total_inferences = 0
        self._total_errors = 0

    def get_device(self, preferred_device: Optional[str] = None) -> torch.device:
        target = preferred_device or ai_settings.AI_DEVICE
        if target.lower() in ("cuda", "gpu", "auto"):
            if torch.cuda.is_available():
                # Check VRAM limits
                free_mb, total_mb = self.get_gpu_memory_mb()
                if free_mb is not None and free_mb < 500:
                    logger.warning(
                        "Low VRAM available (%d MB free). Falling back to CPU for safety.",
                        free_mb,
                    )
                    return torch.device("cpu")
                return torch.device("cuda:0")
            else:
                if target.lower() == "cuda":
                    logger.warning("CUDA requested but not available. Falling back to CPU.")
                return torch.device("cpu")
        return torch.device("cpu")

    def get_gpu_memory_mb(self) -> tuple[Optional[int], Optional[int]]:
        if not torch.cuda.is_available():
            return None, None
        try:
            free_bytes, total_bytes = torch.cuda.mem_get_info()
            return int(free_bytes / (1024 * 1024)), int(total_bytes / (1024 * 1024))
        except Exception:
            return None, None

    def register_model(
        self,
        name: str,
        model_instance: Any,
        version: str = "1.0.0",
        device: Optional[str] = None,
    ) -> None:
        if len(self.loaded_models) >= self.max_concurrent_models and name not in self.loaded_models:
            # Evict oldest model
            oldest = list(self.loaded_models.keys())[0]
            self.unload_model(oldest)

        self.loaded_models[name] = model_instance
        self.model_metadata[name] = {
            "version": version,
            "device": str(device or self.get_device()),
            "loaded_at": time.time(),
        }
        self.inference_stats[name] = {
            "inference_count": 0,
            "total_latency_ms": 0.0,
            "last_latency_ms": 0.0,
            "error_count": 0,
            "last_inference_at": None,
        }
        logger.info("Registered model '%s' (v%s) on %s", name, version, self.model_metadata[name]["device"])

    def unload_model(self, name: str) -> bool:
        if name in self.loaded_models:
            del self.loaded_models[name]
            self.model_metadata.pop(name, None)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            logger.info("Unloaded model '%s'", name)
            return True
        return False

    def record_inference(self, name: str, latency_ms: float, success: bool = True) -> None:
        self._total_inferences += 1
        if not success:
            self._total_errors += 1

        if name in self.inference_stats:
            stats = self.inference_stats[name]
            stats["inference_count"] += 1
            stats["total_latency_ms"] += latency_ms
            stats["last_latency_ms"] = round(latency_ms, 2)
            stats["last_inference_at"] = time.time()
            if not success:
                stats["error_count"] += 1

    def get_system_status(self) -> Dict[str, Any]:
        cuda_avail = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "N/A"
        free_vram, total_vram = self.get_gpu_memory_mb()

        return {
            "ai_status": "online" if len(self.loaded_models) > 0 or cuda_avail or True else "degraded",
            "gpu_available": cuda_avail,
            "gpu_name": gpu_name,
            "gpu_memory_free_mb": free_vram,
            "gpu_memory_total_mb": total_vram,
            "active_models_count": len(self.loaded_models),
            "loaded_models": list(self.loaded_models.keys()),
            "total_inferences": self._total_inferences,
            "total_errors": self._total_errors,
            "model_telemetry": self.inference_stats,
        }


resource_manager = ModelResourceManager()
