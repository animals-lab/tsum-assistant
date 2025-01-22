from typing import List, Optional, Tuple

from pydantic import BaseModel, ValidationError, Field

from llama_index.core.workflow import (
    Workflow,
    step,
    StartEvent,
    StopEvent,
    Event,
    Context,
)
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

from .query import query_catalog
from .models import Offer, StructuredQuery
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.settings import Settings

# TODO isolate own events!
from tsa.chat.chat_events import OfferStreamEvent, OfferFilteredEvent
import asyncio
from loguru import logger
from tsa.models.customer import Customer
from tsa.models.catalog import Category
from tsa.config import settings

class ProcessedQueryEvent(Event):
    structured_query: StructuredQuery


class QueryResultsEvent(Event):
    offers: List[Offer]
    scores: List[float]


class ValidationResultEvent(Event):
    validated_offers: List[Offer]
    not_validated_offers: List[Offer]


class SearchWorkflow(Workflow):
    validation_limit = 5
    query_limit = 20
    score_threshold = 70
    customer: Customer | None = None

    def __init__(self, customer: Customer | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = Settings.llm
        self.customer = customer

    @step
    async def process_input(
        self, ev: StartEvent, ctx: Context
    ) -> ProcessedQueryEvent | StopEvent:
        """
        Processes the unstructured input and creates a structured query.
        Decides if a query is needed based on the input.
        """
        structured_query: StructuredQuery | None = ev.get("structured_query", None)
        input_query: str | None = ev.get("input_query", None)

        if not structured_query:
            input_query = ev.get("input_query")

            sllm = self.llm.as_structured_llm(StructuredQuery)
            query: StructuredQuery = await sllm.achat(
                [
                    ChatMessage(
                        role=MessageRole.SYSTEM,
                        content="From user input create a structured query for the catalog search.",
                    ),
                    ChatMessage(
                        role=MessageRole.USER,
                        content=input_query,
                    ),
                ]
            )

            structured_query = query.raw
            structured_query.limit = self.query_limit

        if not structured_query:
            return StopEvent(result="No query provided.")

        if self.customer:
            # mix customer brand preferences with query brands
            for brand in self.customer.disliked_brand_names:
                if brand not in structured_query.brands:
                    structured_query.blocked_brands.append(brand)

            if self.customer.gender and not structured_query.gender:
                structured_query.gender = self.customer.gender_literal



        await ctx.set("structured_query", structured_query)
        await ctx.set("input_query", input_query)

        return ProcessedQueryEvent(structured_query=structured_query)

    @step
    async def call_query_catalog(
        self, ev: ProcessedQueryEvent, ctx: Context
    ) -> QueryResultsEvent:
        """
        Calls the query_catalog function with the structured query.
        """
        # copy query to avoid mutating the original
        query = StructuredQuery(**ev.structured_query.model_dump())
        
        if query.categories:
            async with settings.db.async_session_maker() as session:
                for category in query.categories:
                    if not await Category.exists_by_name(session, category):
                        logger.info(f"Category {category} not found in database, moving from parameter to text query")
                        query.categories.remove(category)
                        query.query_text = f"{query.query_text if query.query_text else ''} {category}"

        offers, scores = await query_catalog(query)
        logger.debug(f"{"Query executed successfully" if offers else "Query returned no results"}: {query.to_short_description()}")

        if offers:
            ctx.write_event_to_stream(ev=OfferStreamEvent(offers=offers[::-1]))

        #  fallback to query with category moved to text query 
        # if not offers and query.categories:
        #         query.query_text = f"{query.query_text if query.query_text else ''} {', '.join(query.categories)}"
        #         query.categories = None

        #         logger.debug(f"Fallback to query with category moved to text query: {query.query_text}")
        #         offers, scores = await query_catalog(query)
        #         if offers:
        #             logger.debug(f"Fallback query executed successfully: {query.to_short_description()}")
        #             ctx.write_event_to_stream(ev=OfferStreamEvent(offers=offers[::-1]))

        # fallback to query with colors moved to text query
        if not offers and query.colors:
            query.query_text = f"{query.query_text if query.query_text else ''} {', '.join(query.colors)}"
            query.colors = None
            logger.debug(f"Fallback to query with colors moved to text query: {query.query_text}")
            offers, scores = await query_catalog(query)
            if offers:
                logger.debug(f"Fallback query executed successfully: {query.to_short_description()}")
                ctx.write_event_to_stream(ev=OfferStreamEvent(offers=offers[::-1]))

        # if not offers:
        #     query.brands = None
        #     logger.info(
        #         f"Querying catalog with reduced query: {query.to_short_description()}"
        #     )
        #     _offers, _scores = await query_catalog(query)
        #     ctx.write_event_to_stream(ev=OfferStreamEvent(offers=_offers[::-1]))
        #     offers.extend(_offers)
        #     scores.extend(_scores)

        # # reverse order for frontend
        

        return QueryResultsEvent(
            offers=offers[: self.validation_limit],
            scores=scores[: self.validation_limit],
        )

    @step
    async def validate_results(
        self, ev: QueryResultsEvent, ctx: Context
    ) -> ValidationResultEvent:
        """
        Validates each offer using the LLM and separates them into validated and not validated lists.
        """
        validated_offers = []
        not_validated_offers = []

        # Get the query text in a safer way
        structured_query = await ctx.get("structured_query")
        input_query = await ctx.get("input_query")
        query_text = input_query if input_query else structured_query.model_dump_json()

        prompt = "User searched for product with query '{structured_query}', please score the offer '{offer}' on how well it matches the query. score must be integer between 0 and 100. Return only the score. "

        res = []

        for offer in ev.offers:
            res.append(
                self.llm.acomplete(
                    prompt=prompt.format(
                        structured_query=structured_query.to_short_description(),
                        offer=offer.to_summary(),
                    )
                )
            )
        scores = [int(res.text) for res in await asyncio.gather(*res)]
        
        threshhold = 50
        validated_offers = [
            offer
            for offer, score in sorted(
                zip(ev.offers, scores), key=lambda x: x[1], reverse=True
            )
            if score >= threshhold
        ]

        not_validated_offers = [
            offer for offer, score in zip(ev.offers, scores) if score < threshhold
        ]
        logger.info(f"validation scores: {scores}")

        return ValidationResultEvent(
            validated_offers=validated_offers[:3],
            not_validated_offers=validated_offers[3:] + not_validated_offers,
        )

    @step
    async def return_results(self, ev: ValidationResultEvent) -> StopEvent:
        """
        Returns the list of validated and not validated items.
        """
        result = {
            "validated_offers": ev.validated_offers,
            "not_validated_offers": ev.not_validated_offers,
        }
        return StopEvent(result=result)


if __name__ == "__main__":
    # Example usage
    async def main():
        workflow = SearchWorkflow(timeout=20, verbose=True)
        result = await workflow.run(input_query="Белые кеды, мужские", streaming=True)
        print(result)

    import asyncio

    asyncio.run(main())
