import asyncio
import logging
from pathlib import Path

from data_layer_manager.application.factories import get_ingestion_service

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("seed_sample")


async def seed_data() -> None:
    """
    Seeds the system with meaningful data from tests/data.
    """
    logger.info("Initializing Ingestion Service...")
    service = get_ingestion_service()

    data_dir = Path("tests/data")
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} not found!")
        return

    # Files to ingest
    sample_files = ["sample.md", "sample.html", "sample.txt"]

    for filename in sample_files:
        file_path = data_dir / filename
        if not file_path.exists():
            logger.warning(f"File {filename} not found in {data_dir}, skipping.")
            continue

        logger.info(f"🚀 Ingesting {filename}...")
        try:
            doc = await service.ingest_file(
                file_path=str(file_path.absolute()),
                source_metadata={
                    "source_category": "sample_seed",
                    "importance": "high",
                },
            )
            logger.info(
                f"✅ Successfully ingested {filename}. Doc ID: {doc.id}, Chunks: {len(doc.chunks)}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to ingest {filename}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(seed_data())
