import json
import logging
import traceback
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.catalog.models import GenderType, Offer
from app.catalog.query import product_queue, query_catalog

logger = logging.getLogger(__name__)
router = APIRouter()


class CatalogQueryResponse(BaseModel):
    items: List[Offer]
    scores: List[float]


@router.get("/catalog", response_model=CatalogQueryResponse)
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


@router.get("/product-stream")
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