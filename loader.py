import os
import time
import logging
import argparse
from src.qdrant.client import QdrantManager
from src.data.loader import Loader
from src.exceptions.common import LoadException


logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

qdrant = QdrantManager()
loader = Loader(qdrant=qdrant)


def nuke(args: any):
    logger.info("Attempting to delete all points on a Qdrant collection")
    return qdrant.delete_collection(
        collection_name=args.collection,
        timeout=args.timeout
    )


def load_bank_data(args: any):
    logger.info("Attempting file upload to Qdrant")
    retries = args.attempts
    wait = args.wait
    for i in range(retries):
        if i == retries:
            logger.error("Max attempts reached, exiting...")
            return
        try:
            loader.load_summaries()
            break
        except LoadException as le:
            logger.error(f"Upstream error occurred when attempting to load files to Qdrant {str(le)}")
            time.sleep(wait)
        except Exception as e:
            logger.error(f"Unknown error occurred when attempting to load files to Qdrant {str(e)}")
            time.sleep(wait)


def load_pdf_data(args: any):
    logger.info("Attempting file upload to Qdrant")
    retries = args.attempts
    wait = args.wait
    for i in range(retries):
        if i == retries:
            logger.error("Max attempts reached, exiting...")
            return
        try:
            loader.load_pdf(args.path)
            break
        except LoadException as le:
            logger.error(f"Upstream error occurred when attempting to load files to Qdrant {str(le)}")
            time.sleep(wait)
        except Exception as e:
            logger.error(f"Unknown error occurred when attempting to load files to Qdrant {str(e)}")
            time.sleep(wait)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        prog="loader",
        description="CLI tool to embed and load data into Qdrant"
    )
    subparsers = argparser.add_subparsers(help='subcommand help')

    parser_load = subparsers.add_parser(name="pdf_load", help="Command to load a single PDF content into Qdrant")
    parser_load.add_argument("--path", "-p", type=str, required=True)
    parser_load.add_argument("--attempts", type=int, default=3)
    parser_load.add_argument("--wait", type=int, default=3)
    parser_load.set_defaults(func=load_pdf_data)

    parser_bank = subparsers.add_parser(name="bank_data_load", help="Command to load bank statement data from Galicia or BBVA into Qdrant")
    parser_bank.add_argument("--path", "-p", type=str, required=True)
    parser_bank.add_argument("--attempts", type=int, default=3)
    parser_bank.add_argument("--wait", type=int, default=3)
    parser_bank.set_defaults(func=load_bank_data)

    parser_nuke = subparsers.add_parser(name="nuke", help="Command to delete a collection and all its data")
    parser_nuke.add_argument("--collection", "-c", type=str, required=True)
    parser_nuke.add_argument("--timeout", type=int, default=60)
    parser_nuke.set_defaults(func=nuke)

    args = argparser.parse_args()
    args.func(args)


