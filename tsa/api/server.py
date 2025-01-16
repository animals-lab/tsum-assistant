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

# Set up logging
# Set up root logger with custom formatter
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    force=True,  # Force override any existing handlers
    encoding="utf-8",
    level=logging.INFO
)

LlamaSettings.llm = OpenAI(model="gpt-4o-mini", temperature=0.4)
if settings.llm.use_observability:
    llama_index.core.set_global_handler(
        "arize_phoenix", endpoint="https://llamatrace.com/v1/traces"
    )


# Set specific levels for different loggers
# logging.getLogger("uvicorn").setLevel(logging.INFO)
# logging.getLogger("fastapi").setLevel(logging.INFO)
# logging.getLogger("vercel").setLevel(logging.INFO)
# logging.getLogger("api_server").setLevel(logging.INFO)
# logging.getLogger("workflow").setLevel(logging.INFO)  # Keep workflow logs visible

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
