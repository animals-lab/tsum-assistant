import json
import logging
import traceback
from typing import List, Optional, Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Depends, Cookie
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from tsa.catalog.models import GenderType, StructuredQuery, CatalogQueryResponse
from tsa.catalog.query import query_catalog
from tsa.models.customer import Customer, CustomerGender
from tsa.api.lib.db import get_current_customer

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/catalog", response_model=CatalogQueryResponse)
async def get_catalog(
    query_text: str = Query(default="", description="Free-form text query"),
    brands: Optional[List[str]] = Query(
        default=None, description="List of brand names"
    ),
    categories: Optional[List[str]] = Query(
        default=None, description="List of product categories"
    ),
    colors: Optional[List[str]] = Query(default=None, description="List of colors"),
    gender: Optional[GenderType] = Query(default=None, description="Gender filter"),
    min_price: Optional[float] = Query(default=None, description="Minimum price"),
    max_price: Optional[float] = Query(default=None, description="Maximum price"),
    materials: Optional[List[str]] = Query(
        default=None, description="List of materials"
    ),
    has_discount: Optional[bool] = Query(
        default=None, description="Whether the product has a discount."
    ),
    limit: int = Query(
        default=10, ge=1, le=100, description="Number of results to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    customer: Customer | None = Depends(get_current_customer),
):
    """
    sample query:
    http://localhost:8000/api/catalog?query_text=элегантное%20платье&gender=Женский&limit=5
    http://localhost:8000/api/catalog?category=Брюки&category=Джинсы&color=Чёрный&color=Синий&gender=Мужской&min_price=5000&max_price=15000
    http://localhost:8000/api/catalog?vendor=Gucci&vendor=Prada&material=Кашемир&material=Шерсть&offset=20&limit=20
    http://localhost:8000/api/catalog?query_text=кожаная%20сумка&color=Чёрный&min_price=50000&max_price=200000&vendor=Prada
    """
    if customer and not brands:
        brands = customer.liked_brand_names
    if customer and not gender:
        gender = customer.gender_literal

    try:
        logger.info(f"Querying catalog with parameters: {locals()}")

        # Create StructuredQuery instance from parameters
        query = StructuredQuery(
            query_text=query_text or None,  # Convert empty string to None
            brands=brands,
            categories=categories,
            colors=colors,
            gender=gender,
            min_price=min_price,
            max_price=max_price,
            materials=materials,
            has_discount=has_discount
        )

        items, scores = await query_catalog(query, limit=limit)
        return CatalogQueryResponse(items=items, scores=scores)
    except Exception as e:
        logger.error(f"Error in catalog query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))