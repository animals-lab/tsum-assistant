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
from tsa.config import settings
from tsa.catalog.models import GenderType, Offer, StructuredQuery


async def query_catalog(
    structured_query: StructuredQuery,
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
        ("vendor", structured_query.brand),
        ("color", structured_query.color),
        ("material", structured_query.material),
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
    if structured_query.category:
        if isinstance(structured_query.category, str):
            structured_query.category = [structured_query.category]

        # Use MatchAny to match any category from the query with any category in the document
        must_conditions.append(
            FieldCondition(
                key="categories", match=MatchAny(any=structured_query.category)
            )
        )

    # Handle gender filter
    if structured_query.gender:
        must_conditions.append(
            FieldCondition(
                key="gender", match=MatchValue(value=structured_query.gender)
            )
        )

    # Create retriever with filters if any exist
    retriever_kwargs = {
        "similarity_top_k": structured_query.limit,
        "sparse_top_k": structured_query.limit * 10,
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
        # Calculate the batch size needed to cover the requested offset + limit
        batch_size = structured_query.offset + structured_query.limit

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
        start_idx = structured_query.offset
        end_idx = min(start_idx + structured_query.limit, len(results))
        page_results = results[start_idx:end_idx]

        response = (
            [Offer(**point.payload) for point in page_results],
            [1.0] * len(page_results),  # Use default score for non-query results
        )

    return response


if __name__ == "__main__":
    # Example usage
    import time
    import asyncio

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
