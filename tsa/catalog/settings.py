import os
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

load_dotenv()

DATA_URL = "https://st.tsum.com/feeds/diginetica_search.xml"
DATA_FOLDER = Path("data")
CATALOG_FILE = DATA_FOLDER / "catalog.xml"
QDRANT_COLLECTION = "tsum_catalog_openai_small"

# limit the number of items to process, None for no limit
ITEMS_TO_PROCESS = None
BATCH_SIZE = 100
CHECK_BATCH_SIZE = 5000

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

if os.getenv("QDRANT_URL", None):
    qdrant_client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY", None),
    )
    print(f"using Qdrant at {os.getenv('QDRANT_URL')}")
else:
    qdrant_client = QdrantClient(
        host=os.getenv("QDRANT_HOST", "localhost"),
        grpc_port=os.getenv("QDRANT_GRPC_PORT", 6334),
        prefer_grpc=True,
        api_key=os.getenv("QDRANT_API_KEY", None),
    )
    print(f"using Qdrant at {os.getenv('QDRANT_HOST')}:{os.getenv('QDRANT_GRPC_PORT')}")


vector_store = QdrantVectorStore(
    client=qdrant_client, collection_name=QDRANT_COLLECTION
)
