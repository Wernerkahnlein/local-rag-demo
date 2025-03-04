from src.qdrant.client import QdrantManager
from src.data.loader import Loader

def load():
    qdrant = QdrantManager()
    loader = Loader(qdrant=qdrant)
    loader.load()

if __name__ == "__main__":
    load()
