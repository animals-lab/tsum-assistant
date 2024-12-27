from pathlib import Path
from typing import Optional
from loguru import logger
from dotenv import load_dotenv

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from pydantic import Field, computed_field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client import QdrantClient


class TsaSettings(BaseSettings):
    """Settings for TSA."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore", env_file=".env")


class CatalogSettings(TsaSettings):
    """Settings for catalog data processing."""

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="CATALOG_")

    data_url: str = Field(
        "https://st.tsum.com/feeds/diginetica_search.xml",
        description="URL to fetch catalog data from",
    )
    data_folder: Path = Field(
        Path("data"),
        description="Folder to temporarily store data files, used only for parsing",
    )

    parse_limit: Optional[int] = Field(
        None, description="Limit number of items to process, None for no limit"
    )
    parse_batch: int = Field(100, description="Batch size for processing items")
    check_size: int = Field(5000, description="Batch size for checking processed items")

    @computed_field
    def catalog_file_path(self) -> Path:
        """Get the catalog file path."""
        return self.data_folder / "catalog.xml"


class QdrantSettings(TsaSettings):
    """Settings for Qdrant vector store."""

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="QDRANT_")

    collection: str = Field(
        "tsum_catalog_openai_small",
        description="Name of the Qdrant collection",
    )

    url: Optional[str] = Field(None, description="server URL, gRPC used if not set")
    grpc_host: str = Field("localhost", description="gRPC server host")
    grpc_port: int = Field(6334, description="gRPC port")
    api_key: Optional[str] = Field(None, description="API key")

    @computed_field
    def client(self) -> QdrantClient:
        """Initialize and get Qdrant client."""
        if self.url:
            client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
            )
            logger.info(f"Using Qdrant at {self.url}")
        else:
            client = QdrantClient(
                host=self.grpc_host,
                grpc_port=self.grpc_port,
                prefer_grpc=True,
                api_key=self.api_key,
            )
            logger.info(f"Using Qdrant at {self.grpc_host}:{self.grpc_port}")
        return client

    @computed_field
    def vector_store(self) -> QdrantVectorStore:
        """Initialize and get Qdrant vector store."""
        return QdrantVectorStore(
            client=self.client,
            collection_name=self.collection,
        )


class LLMSettings(TsaSettings):
    """Settings for LLM and embeddings."""

    model_config = SettingsConfigDict(case_sensitive=False)

    embedding_model: str = Field(
        "text-embedding-3-small",
        description="OpenAI embedding model name",
        env="OPENAI_EMBEDDING_MODEL",
    )

    llm_model: str = Field(
        "gpt-4o-mini",
        description="OpenAI LLM model name",
        env="OPENAI_LLM_MODEL",
    )

    def setup_llama_settings(self) -> None:
        """Configure LlamaIndex settings."""
        from llama_index.core import Settings as _settings
        from llama_index.llms.openai import OpenAI

        _settings.embed_model = OpenAIEmbedding(model=self.embedding_model)
        _settings.llm = OpenAI(model=self.llm_model)


class Settings(BaseModel):
    catalog: CatalogSettings = Field(default_factory=CatalogSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)


# Create a global settings instance
settings = Settings()
settings.llm.setup_llama_settings()
