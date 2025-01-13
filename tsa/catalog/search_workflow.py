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


class ProcessedQueryEvent(Event):
    structured_query: StructuredQuery


class QueryResultsEvent(Event):
    offers: List[Offer]
    scores: List[float]


class ValidationResultEvent(Event):
    validated_offers: List[Offer]
    not_validated_offers: List[Offer]


class SearchWorkflow(Workflow):
    validation_limit = 3
    query_limit = 20
    score_threshold = 70

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = Settings.llm

    @step
    async def process_input(
        self, ev: StartEvent, ctx: Context
    ) -> ProcessedQueryEvent | StopEvent:
        """
        Processes the unstructured input and creates a structured query.
        Decides if a query is needed based on the input.
        """
        structured_query = ev.get("structured_query", None)
        input_query = ev.get("input_query", None)

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
        query = ev.structured_query
        offers, scores = await query_catalog(query)
        if len(offers) == 0:
            query.category = None
            offers, scores = await query_catalog(query)

        # reverse order for frontend
        ctx.write_event_to_stream(ev=OfferStreamEvent(offers=offers[::-1]))
       
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

        prompt = "User searched for product with query '{query_text}', please score the offer '{offer}' on how well it matches the query. score must be integer between 0 and 100. Return only the score. "

        res = []

        for offer in ev.offers:
            res.append(
                self.llm.acomplete(prompt=prompt.format(query_text=query_text, offer=offer.description))
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

        return ValidationResultEvent(
            validated_offers=validated_offers,
            not_validated_offers=not_validated_offers,
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
