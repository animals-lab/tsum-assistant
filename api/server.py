import json
import logging
import traceback
from typing import List, Optional

import llama_index.core
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from llama_index.core.llms import ChatMessage
from pydantic import BaseModel

from api.routers.vercel import VercelStreamResponse
from app.agent import get_agent_configs, get_initial_state
from app.catalog.models import GenderType, Offer
from app.catalog.query import product_queue, query_catalog
from app.workflow import ConciergeAgent

from .routers.vercel import VercelStreamResponse

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


class CatalogQueryResponse(BaseModel):
    items: List[Offer]
    scores: List[float]


@app.get("/api/catalog", response_model=CatalogQueryResponse)
async def get_catalog(
    query_text: str = Query(default="", description="Free-form text query"),
    vendor: Optional[List[str]] = Query(
        default=None, description="List of brand names"
    ),
    category: Optional[List[str]] = Query(
        default=None, description="List of product categories"
    ),
    color: Optional[List[str]] = Query(default=None, description="List of colors"),
    gender: Optional[GenderType] = Query(default=None, description="Gender filter"),
    min_price: Optional[float] = Query(default=None, description="Minimum price"),
    max_price: Optional[float] = Query(default=None, description="Maximum price"),
    material: Optional[List[str]] = Query(
        default=None, description="List of materials"
    ),
    limit: int = Query(
        default=10, ge=1, le=100, description="Number of results to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
):
    """
    sample query:
    http://localhost:8000/api/catalog?query_text=элегантное%20платье&gender=Женский&limit=5
    http://localhost:8000/api/catalog?category=Брюки&category=Джинсы&color=Чёрный&color=Синий&gender=Мужской&min_price=5000&max_price=15000
    http://localhost:8000/api/catalog?vendor=Gucci&vendor=Prada&material=Кашемир&material=Шерсть&offset=20&limit=20
    http://localhost:8000/api/catalog?query_text=кожаная%20сумка&color=Чёрный&min_price=50000&max_price=200000&vendor=Prada
    """
    try:
        logger.info(f"Querying catalog with parameters: {locals()}")
        items, scores = await query_catalog(
            query_text=query_text,
            vendor=vendor,
            category=category,
            color=color,
            gender=gender,
            min_price=min_price,
            max_price=max_price,
            material=material,
            limit=limit,
            offset=offset,
        )
        return CatalogQueryResponse(items=items, scores=scores)
    except Exception as e:
        logger.error(f"Error in catalog query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/product-stream")
async def stream_products(request: Request):
    """
    Streams products from the product queue as Server-Sent Events.
    Each event contains a JSON-serialized Offer object.
    """

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("Client disconnected from product stream")
                    break

                # Wait for the next item from the queue
                offer: Offer = await product_queue.get()

                # Convert the Offer to JSON and format as SSE
                json_data = offer.model_dump_json()
                yield f"event: product\ndata: {json_data}\n\n"

                # Mark the task as done
                product_queue.task_done()

        except Exception as e:
            logger.error(f"Error in product stream: {str(e)}")
            logger.error(traceback.format_exc())
            yield f"event: error\ndata: {json.dumps(str(e))}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        logger.info("Received request to /api/chat")
        body = await request.json()
        messages = body.get("messages", [])

        # Get the last message content
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        last_message = messages[-1]
        user_message = last_message.get("content", "")

        agent = ConciergeAgent(timeout=60)

        event_handler = agent.run(
            user_msg=user_message,
            agent_configs=get_agent_configs(),
            chat_history=[
                ChatMessage(role=m["role"], content=m["content"]) for m in messages[:-1]
            ],
            initial_state=get_initial_state(),
            streaming=True,
        )

        return VercelStreamResponse(
            request=request,
            # chat_data=data,
            event_handler=event_handler,
            events=agent.stream_events(),
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)
