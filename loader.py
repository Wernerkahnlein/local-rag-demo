import os
import time
import logging
from src.qdrant.client import QdrantManager
from src.data.loader import Loader
from src.exceptions.common import LoadException


logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def load():
    logger.info("Attempting file upload to Qdrant")
    retries = int(os.environ.get("LOADER_RETRY_MAX_ATTEMPTS", 3))
    wait = int(os.environ.get("LOADER_RETRY_WAIT", 2))
    for i in range(retries):
        if i == retries:
            logger.error("Max attempts reached, exiting...")
            return
        try:
            qdrant = QdrantManager()
            loader = Loader(qdrant=qdrant)
            # loader.load_summaries()
            loader.load_pdf("/pdfs/resistance_training_movement_pattern.pdf")
            break
        except LoadException as le:
            logger.error(f"Upstream error occurred when attempting to load files to Qdrant {str(le)}")
            time.sleep(wait)
        except Exception as e:
            logger.error(f"Unknown error occurred when attempting to load files to Qdrant {str(e)}")


if __name__ == "__main__":
    load()
