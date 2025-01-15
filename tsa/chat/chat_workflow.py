import datetime
import re
from typing import Any, Optional

from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.prompts import PromptTemplate
from llama_index.core.workflow import Context, StartEvent, StopEvent, Workflow, step
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from loguru import logger
from pydantic import BaseModel, Field

from tsa.catalog.models import StructuredQuery
from tsa.catalog.search_workflow import SearchWorkflow
from tsa.catalog.query import query_catalog_by_sku
from tsa.chat.chat_events import (
    AgentRunEvent,
    CatalogRequestEvent,
    CatalogResponseEvent,
    FashionTrendsRequestEvent,
    FashionTrendsResponseEvent,
    OfferFilteredEvent,
    OfferStreamEvent,
    ProcessInputRequestEvent,
    ProcessInputResultEvent,
    ProgressEvent,
    SKURequestEvent,
    SKUResponseEvent,
)
from tsa.models.customer import Customer
from tsa.styleguide.trend_perplexity import fetch_fashion_trends


class ProcessInputResult(BaseModel):
    request_summary: str = Field(description="Summary of user request")
    # execution_plan: str = Field(
    #     description="Execution plan for the request, each step is separated by a newline"
    # )

    right_away_answer: Optional[str] = Field(
        default=None,
        description="Answer to the user request right away, if nothing else needed. If you want to execute catalog search, fashion trends search or itemid search, do not include this field.",
    )
    catalog_search_required: bool = Field(
        description="Whether catalog search is required"
    )
    trends_search_required: bool = Field(
        description="Whether fashion trends search is required"
    )
    sku_search_required: bool = Field(description="Whether sku search is required")
    search_query: Optional[StructuredQuery] = Field(
        default=None, description="Structured query for catalog search"
    )
    trends_query: Optional[str] = Field(
        default=None, description="Query for fashion trends search"
    )
    sku_query: Optional[list[str]] = Field(
        default=None,
        description="List of product article numbers, item ids, skus or product codes customer is asking for (like 6999030, APT0118570, 10128-PG, HE00416466 etc.)",
    )


class MainWorkflow(Workflow):
    _streaming = False
    _start_time: datetime.datetime | None = None
    customer: Customer | None = None

    def __init__(
        self,
        chat_memory: ChatMemoryBuffer,
        customer: Customer | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.llm = OpenAI(model="gpt-4o-mini")
        self.chat_memory = chat_memory
        self.customer = customer

    @step
    async def init(self, ctx: Context, ev: StartEvent) -> ProcessInputRequestEvent:
        await ctx.set("pending_events", [])
        self._start_time = datetime.datetime.now()
        return ProcessInputRequestEvent(user_msg=ev.user_msg)

    @step
    async def process_input(
        self, ctx: Context, ev: ProcessInputRequestEvent
    ) -> (
        CatalogRequestEvent
        | FashionTrendsRequestEvent
        | ProcessInputResultEvent
        | SKURequestEvent
    ):
        # TODO: Structure streaming ?!

        # preprocess user message without LLM
        # TODO: move to separate function
        user_msg = ev.user_msg
        user_msg = re.sub(r"https://www\.tsum\.ru/product/(\w+)-.*?/", r"\1", user_msg)

        logger.debug(f"Processed user message: {user_msg}")

        """
        Process user input and emit events
        0. Create plan of execution
        1. Show user summary of request
        2. Request catalog search if required
        3. Request fashion trends search if required
        """
        prompt = """
            You are a helpful shopping assistant that helps user to find the best offer for their request. Please answer in request language.
            You will be given a user request and you will need to create a plan of execution for the request and it's summary.
            You will also need to determine if search by sku is required, catalog search is required and if fashion trends search is required (choose one).

            If sku search is required, you will need set sku_query to the sku customer is asking for and skip catalog search and fashion trends search.
            If catalog search is required, you will need to create a structured query for the catalog search using user request and query context.
            If fashion trends search is required, you will need to create a query for the fashion trends search using user request and query context.
            If you can answer the user request right away (user just want to chat), please do so, but remember, you are a frendly shopping assistant, not a chatbot.
            """
        ctx.write_event_to_stream(
            ev=AgentRunEvent(name="main", msg="Обрабатываем ваш запрос...")
        )
        if self.customer and self.customer.prompt:
            prompt += f"\n\n{self.customer.prompt}"

        messages = [
            ChatMessage(role="system", content=prompt),
        ]

        history = self.chat_memory.get_all()
        if history:
            for msg in history:
                messages.append(ChatMessage(role=msg.role, content=msg.content))
            # history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in history])
            # prompt += f"\n\n Previous conversation history, use it to understand user requests better: ------ \n{history_str} ------ \n"
        
        messages.append(ChatMessage(role="user", content=user_msg))
        sllm = self.llm.as_structured_llm(output_cls=ProcessInputResult)
        res = (await sllm.achat(messages=messages)).raw

        # if self._streaming:
            # @TODO STREAMING IS DISABLED FOR NOW, RESURECT WHEN SCAFFOLDING IS DONE
            # res = await self.llm.astream_structured_predict(
            #     output_cls=ProcessInputResult, prompt=PromptTemplate(prompt)
            # )

            # search_launched = False

            # async for token in res:
            #     if not search_launched:
            #         q = token.search_query
            #         print(q)
            #         if q and q.complete and token.catalog_search_required:
            #             ctx.send_event(CatalogRequestEvent(structured_query=q))
            #             search_launched = True

            # res = token
        # else:
            # res = await self.llm.astructured_predict(
            #     output_cls=ProcessInputResult, prompt=PromptTemplate(prompt)
            # )

        print(f"Processed input: {res}")

        await ctx.set("processed_input", res)

        if res.right_away_answer:
            return StopEvent(result=res.right_away_answer)

        if not self._streaming:
            if res.catalog_search_required:
                ctx.send_event(CatalogRequestEvent(structured_query=res.search_query))
            if res.trends_search_required:
                ctx.send_event(FashionTrendsRequestEvent(query=res.trends_query))
            if res.sku_search_required:
                for sku in res.sku_query:
                    ctx.send_event(SKURequestEvent(query=sku))

        return ProcessInputResultEvent()

    @step
    async def execute_catalog_search(
        self, ctx: Context, ev: CatalogRequestEvent
    ) -> CatalogResponseEvent:
        """
        Execute catalog search
        """
        ctx.write_event_to_stream(
            ev=AgentRunEvent(name="query_catalog_tool", msg="Начинаем поиск.")
        )
        workflow = SearchWorkflow(timeout=30, verbose=True)
        task = workflow.run(structured_query=ev.structured_query, stream=True)

        ctx.write_event_to_stream(
            ev=AgentRunEvent(
                name="query_catalog_tool", msg="Отбираем лучшие предложения."
            )
        )

        async for ev in workflow.stream_events():
            # if isinstance(ev, OfferStreamEvent):
            ctx.write_event_to_stream(ev)

        result = (await task).get("validated_offers", [])
        summary = None

        # found some offers
        if result:
            ctx.write_event_to_stream(ev=OfferFilteredEvent(offers=result))
            summary = "\n\n".join([offer.description for offer in result])
            logger.info(f"Catalog summary: {summary}")

        ctx.write_event_to_stream(
            ev=AgentRunEvent(name="query_catalog_tool", msg="Завершаем поиск.")
        )

        return CatalogResponseEvent(catalog_summary=summary)

    @step
    async def execute_sku_search(
        self, ctx: Context, ev: SKURequestEvent
    ) -> SKUResponseEvent:
        """
        Execute sku search
        """
        offers = await query_catalog_by_sku(ev.query)
        ctx.write_event_to_stream(ev=OfferStreamEvent(offers=offers))
        ctx.write_event_to_stream(ev=OfferFilteredEvent(offers=offers))
        logger.info(f"Found {offers} offers for sku {ev.query}")

        summary = (
            "\n\n".join([offer.description for offer in offers]) if offers else None
        )
        logger.info(f"SKU search summary: {summary}")
        return SKUResponseEvent(offers=offers, summary=summary)

    @step
    async def execute_fashion_trends_search(
        self, ctx: Context, ev: FashionTrendsRequestEvent
    ) -> FashionTrendsResponseEvent | CatalogRequestEvent:
        """
        Execute fashion trends search
        optionnaly search catalog for examples
        """
        ctx.write_event_to_stream(
            ev=AgentRunEvent(
                name="fetch_fashion_trends",
                msg="Начинаем поиск информации о модных трендах.",
            )
        )
        trends = await fetch_fashion_trends(ev.query)
        print(f"Fashion trends: {trends}")
        ctx.write_event_to_stream(
            ev=AgentRunEvent(name="fetch_fashion_trends", msg="Завершаем поиск.")
        )
        return FashionTrendsResponseEvent(response=trends)

    @step
    async def finalize(
        self,
        ctx: Context,
        ev: (
            CatalogResponseEvent
            | FashionTrendsResponseEvent
            | ProcessInputResultEvent
            | SKUResponseEvent
        ),
    ) -> StopEvent:

        pending_events = [ProcessInputResultEvent]
        input = await ctx.get("processed_input")

        # TODO this can lead to infinite wait if we manually skip some (for example skip catalog search if sku search was called)
        if input.catalog_search_required:
            pending_events.append(CatalogResponseEvent)
        if input.trends_search_required:
            pending_events.append(FashionTrendsResponseEvent)
        if input.sku_search_required:
            for _ in input.sku_query:
                pending_events.append(SKUResponseEvent)

        res = ctx.collect_events(ev, pending_events)
        if res is None:
            return None

        ctx.write_event_to_stream(ev=AgentRunEvent(name="main", msg="Подводим итоги."))
        context_parts = []

        for ev in res:
            if isinstance(ev, CatalogResponseEvent):
                if ev.catalog_summary:
                    context_parts.append(
                        f"We have executed catalog search and found the following offers: {ev.catalog_summary},we already showed them to the client, please add short summary."
                    )
                else:
                    context_parts.append(
                        f"We have executed catalog search and found no offers. Please tell user that there's now offers with this sku available."
                    )

            if isinstance(ev, FashionTrendsResponseEvent):
                context_parts.append(
                    f"We have executed fashion trends search and found the following information: {ev.response}."
                )

            if isinstance(ev, SKUResponseEvent):
                if ev.summary:
                    context_parts.append(
                        f"We  have executed sku search and found the following: {ev.summary}, we already showed them to the client, please add short summary."
                    )
                else:
                    context_parts.append(
                        f"We have executed sku search and found no offers. Please apologize to user and offer to try again with less specific request."
                    )

        prompt = PromptTemplate(
            """
            You are a helpful assistant that helps user to find the best offer for their request.
            Please create short and concise answer to the user request.

            User request was: {user_msg}
            
            {context_placeholder}

            Your answer:
            """
        )

        resp = await self.llm.astream(
            prompt,
            context_placeholder="\n\n".join(context_parts),
            user_msg=input.request_summary,
        )

        answer = ""

        async for token in resp:
            answer += token
            # streaming breaks frontend for now
            # ctx.write_event_to_stream(ev=ProgressEvent(msg=token))

        elapsed_seconds = (datetime.datetime.now() - self._start_time).total_seconds()
        elapsed_str = f"{elapsed_seconds:.2f} секунд"
        ctx.write_event_to_stream(
            ev=AgentRunEvent(
                name="main", msg=f"Завершаем работу. Запрос выполнен за {elapsed_str}."
            )
        )
        return StopEvent(result=answer)


if __name__ == "__main__":
    import asyncio

    from llama_index.utils.workflow import (
        draw_all_possible_flows,
        draw_most_recent_execution,
    )

    async def main():
        memory = ChatMemoryBuffer.from_defaults(
            llm=OpenAI(model="gpt-4o-mini"),
        )

        # memory.put(
        #     ChatMessage(
        #         role="user",
        #         content="Найди черную кепку!",
        #     )
        # )
        # memory.put(
        #     ChatMessage(
        #         role="assistant",
        #         content="""
        #             Мы нашли несколько отличных черных кепок:
        #             1. **Мягкая кепка с широким козырьком** - из эластичного хлопкового текстиля с полиэстером, хорошо пропускает воздух, регулируется узк  им ремешком.
        #             2. **Кепка из регенерированного нейлона Re-Nylon** - стильная альтернатива бейсболке, с мягкой тульей и широким козырьком, брендированный патч сзади.
        #             3. **Легкая кепка из нейлона и стрейчевых волокон** - защищает от ветра и дождя, идеальна для межсезонья, с вышитым логотипом спереди.
        #             """,
        #     )
        # )
        workflow = MainWorkflow(
            verbose=True,
            timeout=None,
            chat_memory=memory,
        )
        # res = await workflow.run(user_msg="Что сейчас модно в китае?")
        res = await workflow.run(user_msg="Найди белую кепку!")
        print(res)
        draw_all_possible_flows(MainWorkflow, filename="basic_workflow.html")
        draw_most_recent_execution(workflow, filename="basic_workflow_execution.html")

    asyncio.run(main())
