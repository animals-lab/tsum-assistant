from typing import List, Optional

from llama_index.core import VectorStoreIndex
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchAny,
    MatchText,
    MatchValue,
    Range,
)

from tsa.catalog.models import GenderType, Offer, StructuredQuery
from tsa.config import settings


async def query_catalog(
    structured_query: StructuredQuery,
    limit: int = 20,
) -> tuple[list[Offer], list[float]]:
    """
    Query the catalog.

    Args:
        structured_query: Structured query object containing all query parameters.
    """
    # Initialize Qdrant store and index

    # Build filter conditions
    must_conditions = [FieldCondition(key="available", match=MatchValue(value=True))]

    # Handle price range
    if structured_query.min_price is not None or structured_query.max_price is not None:
        range_params = {}
        if structured_query.min_price is not None:
            range_params["gte"] = structured_query.min_price
        if structured_query.max_price is not None:
            range_params["lte"] = structured_query.max_price
        must_conditions.append(FieldCondition(key="price", range=Range(**range_params)))

    # Handle list filters
    for field, values in [
        ("vendor", structured_query.brands),
        ("color", structured_query.colors),
        ("material", structured_query.materials),
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

    if structured_query.blocked_brands:
        must_conditions.append(Filter(must_not=[FieldCondition(key="vendor", match=MatchAny(any=structured_query.blocked_brands))]))

    # Handle category filter separately since it's a list field in Qdrant
    if structured_query.categories:
        if isinstance(structured_query.categories, str):
            structured_query.categories = [structured_query.categories]

        # Use MatchAny to match any category from the query with any category in the document
        must_conditions.append(
            FieldCondition(
                key="categories", match=MatchAny(any=structured_query.categories)
            )
        )

    # Handle gender filter
    if structured_query.gender:
        must_conditions.append(
            FieldCondition(
                key="gender", match=MatchValue(value=structured_query.gender)
            )
        )

    # handle has_discount
    if structured_query.has_discount:
        must_conditions.append(FieldCondition(key="has_discount", match=MatchValue(value=True)))

    # Create retriever with filters if any exist
    retriever_kwargs = {
        "similarity_top_k": limit,
        "sparse_top_k": limit * 10,
    }
    if must_conditions:
        retriever_kwargs["vector_store_kwargs"] = {
            "qdrant_filters": Filter(must=must_conditions)
        }

    if structured_query.query_text:
        vector_store = settings.qdrant.vector_store
        index = VectorStoreIndex.from_vector_store(vector_store)
        retriever = index.as_retriever(**retriever_kwargs)

        # Perform the query
        results = retriever.retrieve(structured_query.query_text)
        response = (
            [Offer(**node.metadata) for node in results],
            [node.score for node in results],
        )
    else:
        # Calculate the batch size needed to cover the requested offset + limit | TODO: check if this is correct
        batch_size =  limit

        # For non-query cases, use scroll with calculated batch size
        results = settings.qdrant.client.scroll(
            collection_name=settings.qdrant.collection,
            scroll_filter=Filter(must=must_conditions),
            limit=batch_size,  # Use larger batch size to cover offset
            offset=0,  # Start from beginning
            with_payload=True,
        )[
            0
        ]  # Get just the points array

        # Get the requested page
        # start_idx = structured_query.offset
        # end_idx = min(start_idx + limit, len(results))
        # page_results = results[start_idx:end_idx]

        response = (
            [Offer(**point.payload) for point in results],
            [1.0] * len(results),  # Use default score for non-query results
        )

    return response


async def query_catalog_by_sku(sku: str) -> List[Offer] | None:
    """
    Query the catalog by SKU (id or vendor_id).
    Performs a case-insensitive exact match search.

    Args:
        sku: The SKU string to search for (matches against id or vendor_id)

    Returns:
        Optional[Offer]: The matching offer if found, None otherwise
    """
    # Build filter conditions for case-insensitive match on either id or vendor_id
    filter_conditions = Filter(
        should=[
            FieldCondition(key="tsum_sku", match=MatchText(text=sku)),
            FieldCondition(key="vendor_sku", match=MatchText(text=sku)),
        ],
        must=[FieldCondition(key="available", match=MatchValue(value=True))],
    )

    # Query Qdrant directly
    results, _ = settings.qdrant.client.scroll(
        collection_name=settings.qdrant.collection,
        scroll_filter=filter_conditions,
        limit=5,
        with_payload=True,
    )
    return [Offer(**res.payload) for res in results]


if __name__ == "__main__":
    # Example usage
    import asyncio
    import time

    start_time = time.time()
    results = asyncio.run(
        query_catalog(
            StructuredQuery(
                category=["Спорт", "Джоггеры"],
                gender="Мужской",
                limit=100,
            )
        )
    )
    execution_time = time.time() - start_time
    print(f"Query executed in {execution_time:.2f} seconds")

    print(results)
    # for offer, score in zip(results[0], results[1]):
    #     print("\nScore:", score)
    #     print("Offer:", offer.description)
