from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class QdrantManager:

    def __init__(self, url: str = "http://qdrant:6333"):
        self.url = url
        self.client = self._get_client()
        if not self.client.collection_exists(collection_name="default"):
            self.client.create_collection(
                collection_name="default",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
        
    def _get_client(self) -> QdrantClient:
        return QdrantClient(url=self.url)

    def upload_emdeddings(self, points: list, collection_name: str = "default"):
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def retrieve_documents(self, query_embedding, top_k=5, collection_name: str = "default"):
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        return [result.payload["text"] for result in search_result]
    
    def query(self, query_text, top_k=5, collection_name: str = "default"):
        search_result = self.client.query(
            collection_name=collection_name,
            query_text=query_text,
            limit=top_k
        )
        return [result.payload["text"] for result in search_result]
    
    def create_collection(self, name: str, vector_params: VectorParams = VectorParams(size=1024, distance=Distance.COSINE)) -> bool:
        if not self.client.collection_exists(collection_name=name):
            return self.client.create_collection(
                collection_name=name,
                vectors_config=vector_params,
            )
        return False
    
    def recreate_collection(self, collection_name: str, vector_params: VectorParams = VectorParams(size=1024, distance=Distance.COSINE)) -> bool:
        return self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=vector_params,
        )
    
    def delete_collection(self, collection_name: str, timeout: int = 60) -> bool:
        return self.client.delete_collection(
            collection_name=collection_name,
            timeout=timeout,
        )
