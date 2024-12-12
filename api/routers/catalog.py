import json
import logging
import traceback
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.catalog.models import GenderType, Offer, StructuredQuery, CatalogQueryResponse
from app.catalog.query import product_queue, query_catalog

logger = logging.getLogger(__name__)
router = APIRouter()


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
        
        # Create StructuredQuery instance from parameters
        query = StructuredQuery(
            query_text=query_text or None,  # Convert empty string to None
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
        
        items, scores = await query_catalog(
            query
        )
        return CatalogQueryResponse(items=items, scores=scores)
    except Exception as e:
        logger.error(f"Error in catalog query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))