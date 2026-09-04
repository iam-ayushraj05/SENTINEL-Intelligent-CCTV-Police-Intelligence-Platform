import asyncio
import logging
from ai.pipeline.processor import StreamProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel.ai_worker")


async def main():
    logger.info("Starting Sentinel AI Analytics Worker...")
    processor = StreamProcessor()
    
    while True:
        try:
            # Simulated frame loop
            result = await processor.process_frame("CAM-GJ01-001", frame=None)
            logger.info(f"Processed stream frame: {len(result['detections'])} detections, {len(result['events'])} events generated")
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in AI Worker loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
