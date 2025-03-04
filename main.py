import os
import logging

from src.manage.prompts import get_default_prompt, get_default_system_prompt
from src.manage.talker import Talker
from src.qdrant.client import QdrantManager
from src.data.loader import Loader
from src.api.models import Message
from fastapi import FastAPI

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

app = FastAPI()

@app.post("/talk/")
async def talk(message: Message):
    talker = Talker()
    message_data = message.dict()

    if os.environ.get("ENV") != "local":
        qdrant = QdrantManager()
        loader = Loader(qdrant=qdrant)
    
        query = message_data.get("content")
        context = ""
        query_embeddings = loader.embed(query)
        for _, query_embedding in enumerate(query_embeddings):
            documents = qdrant.retrieve_documents(query_embedding=query_embedding, top_k=10, collection_name="pdf_chunks")
            for _, documents in enumerate(documents):
                context += f"{documents}\n"
        prompt = get_default_prompt(context=context, query=query)
        logger.info(f"Sending the following prompt: {prompt}")
        system_prompt = message_data.get("system_prompt") if message_data.get("system_prompt") is not None else get_default_system_prompt()
        return talker.call_chat_completions(system_prompt=system_prompt, prompt=prompt)
    else:
        return {"body": "local"}
