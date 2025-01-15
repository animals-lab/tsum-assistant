from pathlib import Path
from typing import Optional, Callable

from dotenv import load_dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from loguru import logger
from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class TsaSettings(BaseSettings):
    """Settings for TSA."""

    model_config = SettingsConfigDict(
        case_sensitive=False, extra="ignore", env_file=".env"
    )


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
    parse_batch: int = Field(500, description="Batch size for processing items")
    check_size: int = Field(500, description="Batch size for checking processed items")

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


class DatabaseSettings(TsaSettings):
    """Settings for database connection."""

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="DB_")

    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    user: str = Field("postgres", description="Database user")
    password: str = Field(..., description="Database password")
    database: str = Field("tsa", description="Database name")
    echo: bool = Field(False, description="Enable SQL query logging")
    pool_size: int = Field(5, description="Connection pool size")
    max_overflow: int = Field(10, description="Maximum overflow connections")

    @computed_field
    def url(self) -> str:
        """Get the database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @computed_field
    def engine(self) -> AsyncEngine:
        """Initialize and get async database engine."""
        return create_async_engine(
            self.url,
            echo=self.echo,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
        )

    @computed_field
    def async_session_maker(self) -> Callable[[], AsyncSession]:
        """Get async session maker."""
        return async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

# Load environment variables from .env file for libraries that skip setting and use own env variables (like openai)
load_dotenv()

class Settings(BaseModel):
    catalog: CatalogSettings = Field(default_factory=CatalogSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)


# Create a global settings instance
settings = Settings()
settings.llm.setup_llama_settings()
