import pymupdf4llm
import pymupdf
import requests
import os
import hashlib
import uuid
import re
import json
import logging

from pathlib import Path
from src.qdrant.client import QdrantManager
from src.exceptions.common import GaliciaParsingException, BBVAParsingException, LoadException
from src.utils.date_conversion import convert_date
from datetime import datetime
from qdrant_client.models import PointStruct, Distance, VectorParams

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

class Loader:

    def __init__(self, qdrant: QdrantManager):
        self.summaries = Path(os.environ.get("SUMMARY_PATH", "./summaries"))
        self.bbva_path = Path(f"{self.summaries}/bbva")
        self.galicia_path = Path(f"{self.summaries}/galicia")
        self.llama_embedding_url = os.environ.get("EMBEDDER_URL", "http://embedder:8080")
        self.qdrant = qdrant

    def _call_embedding(self, content: str):
        payload = {
            "content": content
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(f"{self.llama_embedding_url}/embedding", json=payload, headers=headers)
        return response.json()
    
    def _split_text_into_chunks(self, text, chunk_size=500, overlap=50):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks
    
    def embed(self, content: str) -> list:
        if os.environ.get("ENV", "local") != "local":
            response = self._call_embedding(content=content)
            embeddings = response[0].get("embedding")
            if embeddings is not None:
                return embeddings
            return []
        else:
            logger.warning("Not sending requests in local")
            return []

    def _manage_galicia_summaries(self) -> list:
        try: 
            embedded_billing_data = []
            for summary in self.galicia_path.iterdir():
                logger.info(f"Reading summary: {summary}")
                content = pymupdf4llm.to_markdown(summary.absolute(),pages=[0,1]).splitlines()
                billing_data = {"bank": "Galicia"}
                for _, data in enumerate(content):
                    if "Estado de cuenta al" in data:
                        cleaned_up_data = list(filter(None, data.split(" ")))
                        billing_data["date"] = convert_date(cleaned_up_data[5])
                    if "SUBTOTAL" in data:
                        cleaned_up_data = list(filter(None, data.split(" ")))
                        billing_data["balance_pesos"] = cleaned_up_data[1].replace(',', '.')
                        billing_data["balance_usd"] = cleaned_up_data[2].replace(',', '.')
                
                if os.environ.get("ENV", "local") != "local":
                    embedding = self.embed(content=json.dumps(billing_data))
                    embedded_billing_data.append({"embedding": embedding, "content": json.dumps(billing_data)})
                else:
                    embedded_billing_data.append({"embedding": [], "content": json.dumps(billing_data)})
                
            return embedded_billing_data
        except Exception as e:
            logger.error(f"Unknown error occurred when parsing Galicia files: {str(e)}")
            raise GaliciaParsingException
            

    def _manage_bbva_summaries(self) -> list:
        try:
            embedded_billing_data = []
            for summary in self.bbva_path.iterdir():
                logger.info(f"Reading summary: {summary}")
                doc = pymupdf.open(summary.absolute())
                page = doc[0]
                content =  page.get_text().splitlines()
                billing_data = {"bank": "BBVA Frances"}
                for i, value in enumerate(content):
                    if value == "VENCIMIENTO ACTUAL":
                        billing_data["date"] = convert_date(content[i + 1])
                    if value == "SALDO ACTUAL $":
                        billing_data["balance_pesos"] = re.sub('[.]', '', content[i + 1]).replace(',', '.')
                    if value == "SALDO ACTUAL U$S":
                        billing_data["balance_usd"] = re.sub('[.]', '', content[i + 1]).replace(',', '.')
                if os.environ.get("ENV", "local") != "local":
                    embedding = self.embed(content=json.dumps(billing_data))
                    embedded_billing_data.append({"embedding": embedding, "content": json.dumps(billing_data)})
                else:
                    embedded_billing_data.append({"embedding": [], "content": json.dumps(billing_data)})
            return embedded_billing_data
        except Exception as e:
            logger.error(f"Unknown error occurred when parsing BBVA files: {str(e)}")
            raise BBVAParsingException


    def load_summaries(self):
        try: 
            galicia_data = self._manage_galicia_summaries()
            bbva_data = self._manage_bbva_summaries()
            
            bbva_points = [
                PointStruct(
                    id=str(uuid.UUID(hex=hashlib.md5(bbva_data[i]["content"].encode("utf-8")).hexdigest())),
                    vector=bbva_data[i]["embedding"][0] if len(bbva_data[i]["embedding"]) == 1 else bbva_data[i]["embedding"],
                    payload={"text": bbva_data[i]["content"], "bank": "bbva"}
                ) for i, _ in enumerate(bbva_data)
            ]
            galicia_points = [
                PointStruct(
                    id=str(uuid.UUID(hex=hashlib.md5(galicia_data[i]["content"].encode("utf-8")).hexdigest())),
                    vector=galicia_data[i]["embedding"][0] if len(galicia_data[i]["embedding"]) == 1 else galicia_data[i]["embedding"],
                    payload={"text": galicia_data[i]["content"], "bank": "galicia"}
                ) for i, _ in enumerate(galicia_data)
            ]

            self.qdrant.upload_emdeddings(
                points=bbva_points
            )

            self.qdrant.upload_emdeddings(
                points=galicia_points
            )
        except GaliciaParsingException|BBVAParsingException as pe:
            logger.error(f"Unknown error occurred when parsing summaries: {str(pe)}")
            raise LoadException
        except Exception as e:
            logger.error(f"Unknown error: {str(e)}")
            raise Exception


    def load_pdf(self, path: str):
        try:
            collection_name = "pdf_chunks"
            doc = pymupdf.open(Path(path).absolute())
            for page in doc:
                content =  page.get_text()
                content = re.sub(r"\s+", " ", content)  # Replace multiple spaces with a single space
                content = re.sub(r"[^\w\s.,;!?]", "", content)  # Remove special characters except punctuation
                chunks = self._split_text_into_chunks(content)
                for _, chunk in enumerate(chunks):
                    embedded_chunk = self.embed(chunk)
                    self.qdrant.create_collection(
                        name=collection_name,
                        vector_params=VectorParams(size=len(embedded_chunk[0]), distance=Distance.COSINE)
                    )

                    points = [
                        PointStruct(
                            id=str(uuid.UUID(hex=hashlib.md5(chunk.encode("utf-8")).hexdigest())),
                            vector=embedded_chunk[0],
                            payload={"text": chunk}
                        ) for _, chunk in enumerate(chunks)
                    ]

                    self.qdrant.upload_emdeddings(
                        points=points,
                        collection_name=collection_name
                    )
            
            logger.info(f"Uploaded PDF {path} to Qdrant")
                
        except Exception as e:
            logger.error(f"Unknown exception ocurred while loading PDF {str(e)}")
