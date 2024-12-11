import logging

import llama_index.core
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import catalog, chat

# Set up logging
# Set up root logger with custom formatter
logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    force=True,  # Force override any existing handlers
    encoding="utf-8",
)

llama_index.core.set_global_handler(
    "arize_phoenix", endpoint="https://llamatrace.com/v1/traces"
)

# Set specific levels for different loggers
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
logging.getLogger("fastapi").setLevel(logging.CRITICAL)
logging.getLogger("vercel").setLevel(logging.CRITICAL)
logging.getLogger("api_server").setLevel(logging.CRITICAL)
logging.getLogger("workflow").setLevel(logging.INFO)  # Keep workflow logs visible

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# Add the routers
app.include_router(catalog.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
