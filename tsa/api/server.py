import logging

import llama_index.core
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from tsa.models.customer import Customer
from tsa.api.lib.db import get_current_customer

from tsa.api.routers import catalog, chat
from llama_index.llms.openai import OpenAI
from llama_index.core.settings import Settings as LlamaSettings
from tsa.config import settings
from loguru import logger

# Set up logging
# Set up root logger with custom formatter
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    force=True,  # Force override any existing handlers
    encoding="utf-8",
    level=logging.INFO
)

if settings.llm.use_observability:
    logger.info("Setting up observability")
    from phoenix.otel import register
    from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

    tracer_provider = register(
        project_name=settings.llm.observability_project_name
    ) 
    LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)


logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# Add the routers with dependencies
app.include_router(
    catalog.router,
    prefix="/api",
    dependencies=[Depends(get_current_customer)]
)
app.include_router(
    chat.router,
    prefix="/api",
    dependencies=[Depends(get_current_customer)]
)

from .routers.test_stream import test_stream
app.post("/api/test-stream")(test_stream)
