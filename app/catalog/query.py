from typing import List, Optional
from qdrant_client.models import (
    Filter,
    FieldCondition,
    Range,
    MatchValue,
    MatchText,
    MatchAny,
)
from llama_index.core import VectorStoreIndex
from . import settings
from .models import GenderType, Offer, ShortOffer
from asyncio import Queue

product_queue: Queue[Offer] = Queue()


async def query_catalog(
    query_text: str = "",
    vendor: Optional[List[str]] = None,
    category: Optional[List[str]] = None,
    color: Optional[List[str]] = None,
    gender: Optional[GenderType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    material: Optional[List[str]] = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[Offer], list[float]]:
    """
    Query the catalog.

    Args:
        query_text: Free-form text query ("элегантное платье", "черные туфли", "модный свитер", etc.)
        vendor: List of brand names ("Gucci", "Dsquared2", etc.)
        category: List of product categories, russian, plural ("Платья", "Вечерние платья", "Блузки", etc.)
        color: List of colors ("Чёрный", "Белый", "Красный", etc.)
        gender: Gender ("Мужской", "Женский", or "Унисекс")
        min_price: Minimum price
        max_price: Maximum price
        material: List of materials ("Хлопок", "Шерсть", "Кашемир", etc.)
    """
    # Initialize Qdrant store and index

    # Build filter conditions
    must_conditions = [FieldCondition(key="available", match=MatchValue(value=True))]

    # Handle price range
    if min_price is not None or max_price is not None:
        range_params = {}
        if min_price is not None:
            range_params["gte"] = min_price
        if max_price is not None:
            range_params["lte"] = max_price
        must_conditions.append(FieldCondition(key="price", range=Range(**range_params)))

    # Handle list filters
    for field, values in [
        ("vendor", vendor),
        ("color", color),
        ("material", material),
    ]:
        if not values:
            continue

        # Convert single string to list if needed
        if isinstance(values, str):
            values = [values]

        should_conditions = [
            FieldCondition(key=field, match=MatchText(text=v)) for v in values
        ]
        must_conditions.append(Filter(should=should_conditions))

    # Handle category filter separately since it's a list field in Qdrant
    if category:
        if isinstance(category, str):
            category = [category]

        # Use MatchAny to match any category from the query with any category in the document
        must_conditions.append(
            FieldCondition(key="categories", match=MatchAny(any=category))
        )

    # Handle gender filter
    if gender:
        must_conditions.append(
            FieldCondition(key="gender", match=MatchValue(value=gender))
        )

    # Create retriever with filters if any exist
    retriever_kwargs = {"similarity_top_k": limit, "sparse_top_k": limit * 10}
    if must_conditions:
        retriever_kwargs["vector_store_kwargs"] = {
            "qdrant_filters": Filter(must=must_conditions)
        }

    if query_text:
        vector_store = settings.vector_store
        index = VectorStoreIndex.from_vector_store(vector_store)
        retriever = index.as_retriever(**retriever_kwargs)

        # Perform the query
        results = retriever.retrieve(query_text)
        response = (
            [Offer(**node.metadata) for node in results],
            [node.score for node in results],
        )
    else:
        # Calculate the batch size needed to cover the requested offset + limit
        batch_size = offset + limit

        # For non-query cases, use scroll with calculated batch size
        results = settings.qdrant_client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=Filter(must=must_conditions),
            limit=batch_size,  # Use larger batch size to cover offset
            offset=0,  # Start from beginning
            with_payload=True,
        )[
            0
        ]  # Get just the points array

        # Get the requested page
        start_idx = offset
        end_idx = min(start_idx + limit, len(results))
        page_results = results[start_idx:end_idx]

        response = (
            [Offer(**point.payload) for point in page_results],
            [1.0] * len(page_results),  # Use default score for non-query results
        )

    for offer in response[0]:
        await product_queue.put(offer)

    return response


async def query_catalog_short(
    query_text: str = "",
    vendor: Optional[List[str]] = None,
    category: Optional[List[str]] = None,
    color: Optional[List[str]] = None,
    gender: Optional[GenderType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    material: Optional[List[str]] = None,
    limit: int = 10,
    offset: int = 0,
) -> list[ShortOffer]:
    """
    Query the catalog.

    Args:
        query_text: Free-form text query ("элегантное платье", "черные туфли", "модный свитер", etc.)
        vendor: List of brand names ("Gucci", "Dsquared2", etc.)
        category: List of product categories, russian, plural ("Платья", "Вечерние платья", "Блузки", etc.)
        color: List of colors ("Чёрный", "Белый", "Красный", etc.)
        gender: Gender ("Мужской", "Женский", or "Унисекс")
        min_price: Minimum price
        max_price: Maximum price
        material: List of materials ("Хлопок", "Шерсть", "Кашемир", etc.)
    """
    res = await query_catalog(
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
    return [ShortOffer.from_offer(offer) for offer in res[0]]


if __name__ == "__main__":
    # Example usage
    import time
    import asyncio

    start_time = time.time()
    results = asyncio.run(
        query_catalog_short(
            category=["Спорт", "Джоггеры"],
            limit=100,
        )
    )
    execution_time = time.time() - start_time
    print(f"Query executed in {execution_time:.2f} seconds")

    print(results)
    # for offer, score in zip(results[0], results[1]):
    #     print("\nScore:", score)
    #     print("Offer:", offer.description)
