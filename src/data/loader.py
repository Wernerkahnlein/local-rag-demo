import pymupdf4llm
import pymupdf
import requests
import os
import hashlib
import uuid
import re
import json
from pathlib import Path
from src.qdrant.client import QdrantManager
from qdrant_client.models import PointStruct

# TODO refactor dates to a standard format
class Loader:

    def __init__(self, qdrant: QdrantManager):
        self.summaries = Path(os.environ.get("SUMMARY_PATH", "./summaries"))
        self.env = os.environ.get("ENV", "local")
        self.bbva_path = Path(f"{self.summaries}/bbva")
        self.galicia_path = Path(f"{self.summaries}/galicia")
        self.llama_embedding_url = "http://embedder:8080"
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
    
    def embed(self, content: str) -> list:
        if self.env != "local":
            response = self._call_embedding(content=content)
            embeddings = response[0].get("embedding")
            if embeddings is not None:
                return embeddings
            return []
        else:
            print("Not sending requests in local")
            return []

    def manage_galicia_summaries(self) -> list:
        embedded_billing_data = []
        for summary in self.galicia_path.iterdir():
            print(f"Reading summary: {summary}")
            content = pymupdf4llm.to_markdown(summary.absolute(),pages=[0,1]).splitlines()
            billing_data = {"bank": "Galicia"}
            for _, data in enumerate(content):
                if "Estado de cuenta al" in data:
                    cleaned_up_data = list(filter(None, data.split(" ")))
                    billing_data["fecha"] = cleaned_up_data[5]
                if "SUBTOTAL" in data:
                    cleaned_up_data = list(filter(None, data.split(" ")))
                    billing_data["saldo_pesos"] = cleaned_up_data[1]
                    billing_data["saldo_usd"] = cleaned_up_data[2]
            
            if self.env != "local":
                embedding = self.embed(content=json.dumps(billing_data))
                embedded_billing_data.append({"embedding": embedding, "content": json.dumps(billing_data)})
            else:
                embedded_billing_data.append({"embedding": [], "content": json.dumps(billing_data)})
            
        return embedded_billing_data

    def manage_bbva_summaries(self) -> list:
        embedded_billing_data = []
        for summary in self.bbva_path.iterdir():
            print(f"Reading summary: {summary}")
            doc = pymupdf.open(summary.absolute())
            page = doc[0]
            content =  page.get_text().splitlines()
            billing_data = {"bank": "BBVA Frances"}
            for i, value in enumerate(content):
                if value == "VENCIMIENTO ACTUAL":
                    billing_data["fecha"] = content[i + 1]
                if value == "SALDO ACTUAL $":
                    billing_data["saldo_pesos"] = re.sub('[.]', '', content[i + 1]).replace('.', ',')
                if value == "SALDO ACTUAL U$S":
                    billing_data["saldo_usd"] = re.sub('[.]', '', content[i + 1]).replace('.', ',')
            if self.env != "local":
                embedding = self.embed(content=json.dumps(billing_data))
                embedded_billing_data.append({"embedding": embedding, "content": json.dumps(billing_data)})
            else:
                embedded_billing_data.append({"embedding": [], "content": json.dumps(billing_data)})
            
        return embedded_billing_data

    def load(self):
        galicia_data = self.manage_galicia_summaries()
        bbva_data = self.manage_bbva_summaries()

        print(len(bbva_data[0]["embedding"][0]))
        
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
