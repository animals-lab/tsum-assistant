from llama_index.core.settings import Settings
from llama_index.llms.openai import OpenAI
from llama_index.core.workflow import (
    Workflow,
    Context,
    StartEvent,
    StopEvent,
    step,
)
from llama_index.core.prompts import PromptTemplate
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage

from typing import Any, Optional
from agent.events.workflow import (
    ProcessInputRequestEvent,
    ProcessInputResultEvent,
    CatalogResponseEvent,
    CatalogRequestEvent,
    FashionTrendsRequestEvent,
    FashionTrendsResponseEvent,
)


from pydantic import BaseModel, Field
from app.catalog.search_workflow import SearchWorkflow
from app.workflow_events import OfferFilteredEvent
from app.catalog.models import StructuredQuery
from app.trends.trend_perplexity import fetch_fashion_trends


class ProcessInputResult(BaseModel):
    request_summary: str = Field(description="Summary of user request")
    execution_plan: str = Field(
        description="Execution plan for the request, each step is separated by a newline"
    )

    right_away_answer: Optional[str] = Field(
        default=None,
        description="Answer to the user request right away, if nothing else needed",
    )
    catalog_search_required: bool = Field(
        description="Whether catalog search is required"
    )
    trends_search_required: bool = Field(
        description="Whether fashion trends search is required"
    )
    search_query: Optional[StructuredQuery] = Field(
        default=None, description="Structured query for catalog search"
    )
    trends_query: Optional[str] = Field(
        default=None, description="Query for fashion trends search"
    )


class MainWorkflow(Workflow):
    def __init__(self, chat_memory: ChatMemoryBuffer, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.llm = OpenAI(model="gpt-4o-mini")
        self.chat_memory = chat_memory

    @step
    async def init(self, ctx: Context, ev: StartEvent) -> ProcessInputRequestEvent:
        await ctx.set("pending_events", [])
        return ProcessInputRequestEvent(user_msg=ev.user_msg)

    @step
    async def process_input(
        self, ctx: Context, ev: ProcessInputRequestEvent
    ) -> CatalogRequestEvent | FashionTrendsRequestEvent | ProcessInputResultEvent:
        # TODO: answer right away
        # TODO: Structure streaming ?!
        """
        Process user input and emit events
        0. Create plan of execution
        1. Show user summary of request
        2. Request catalog search if required
        3. Request fashion trends search if required
        """
        prompt = f"""
            You are a helpful assistant that helps user to find the best offer for their request. Please answer in request language.
            You will be given a user request and you will need to create a plan of execution for the request and it's summary.
            You will also need to determine if catalog search is required and if fashion trends search is required.

            If catalog search is required, you will need to create a structured query for the catalog search using user request and query context.
            If fashion trends search is required, you will need to create a query for the fashion trends search using user request and query context.
            If you can answer the user request right away (user just want to chat), please do so, but remember, you are a frendly shopping assistant, not a chatbot.

            User request: {ev.user_msg}
            """

        history = self.chat_memory.get_all()
        if history:
            history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in history])
            prompt += f"\n\n Previous conversation history: {history_str}"

        res: ProcessInputResult = await self.llm.astructured_predict(
            output_cls=ProcessInputResult, prompt=PromptTemplate(prompt)
        )

        await ctx.set("processed_input", res)

        if res.right_away_answer:
            return StopEvent(result=res.right_away_answer)

        if res.catalog_search_required:
            ctx.send_event(CatalogRequestEvent(structured_query=res.search_query))
        if res.trends_search_required:
            ctx.send_event(FashionTrendsRequestEvent(query=res.trends_query))

        return ProcessInputResultEvent()

    @step
    async def execute_catalog_search(
        self, ctx: Context, ev: CatalogRequestEvent
    ) -> CatalogResponseEvent:
        """
        Execute catalog search
        """
        workflow = SearchWorkflow(timeout=30, verbose=True)
        task = workflow.run(structured_query=ev.structured_query)

        async for ev in workflow.stream_events():
            # if isinstance(ev, OfferStreamEvent):
            ctx.write_event_to_stream(ev)

        result = (await task).get("validated_offers", [])
        ctx.write_event_to_stream(ev=OfferFilteredEvent(offers=result))

        summary = "\n\n".join([offer.description for offer in result])
        print(f"Catalog summary: {summary}")
        return CatalogResponseEvent(catalog_summary=summary)

    @step
    async def execute_fashion_trends_search(
        self, ctx: Context, ev: FashionTrendsRequestEvent
    ) -> FashionTrendsResponseEvent | CatalogRequestEvent:
        """
        Execute fashion trends search
        optionnaly search catalog for examples
        """

        trends = await fetch_fashion_trends(ev.query)
        print(f"Fashion trends: {trends}")
        return FashionTrendsResponseEvent(response=trends)

    @step
    async def finalize(
        self,
        ctx: Context,
        ev: CatalogResponseEvent | FashionTrendsResponseEvent | ProcessInputResultEvent,
    ) -> StopEvent:

        pending_events = [ProcessInputResultEvent]
        input = await ctx.get("processed_input")

        if input.catalog_search_required:
            pending_events.append(CatalogResponseEvent)
        if input.trends_search_required:
            pending_events.append(FashionTrendsResponseEvent)

        res = ctx.collect_events(ev, pending_events)
        if res is None:
            return None

        context_parts = []

        for ev in res:
            if isinstance(ev, CatalogResponseEvent):
                context_parts.append(
                    f"We have executed catalog search and found the following offers: {ev.catalog_summary}, please offer client a short summary."
                )
            if isinstance(ev, FashionTrendsResponseEvent):
                context_parts.append(
                    f"We have executed fashion trends search and found the following information: {ev.response}."
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

        # TODO: stream result
        answer = await self.llm.apredict(
            prompt,
            context_placeholder="\n\n".join(context_parts),
            user_msg=input.request_summary,
        )

        return StopEvent(result=answer)


if __name__ == "__main__":
    from llama_index.utils.workflow import (
        draw_all_possible_flows,
        draw_most_recent_execution,
    )
    import asyncio

    async def main():
        memory = ChatMemoryBuffer.from_defaults(
            llm=OpenAI(model="gpt-4o-mini"),
        )

        memory.put(
            ChatMessage(
                role="user",
                content="Найди черную кепку!",
            )
        )
        memory.put(
            ChatMessage(
                role="assistant",
                content="""
                    Мы нашли несколько отличных черных кепок:
                    1. **Мягкая кепка с широким козырьком** - из эластичного хлопкового текстиля с полиэстером, хорошо пропускает воздух, регулируется узк  им ремешком.
                    2. **Кепка из регенерированного нейлона Re-Nylon** - стильная альтернатива бейсболке, с мягкой тульей и широким козырьком, брендированный патч сзади.
                    3. **Легкая кепка из нейлона и стрейчевых волокон** - защищает от ветра и дождя, идеальна для межсезонья, с вышитым логотипом спереди.
                    """,
            )
        )
        workflow = MainWorkflow(
            verbose=True,
            timeout=None,
            chat_memory=memory,
        )
        # res = await workflow.run(user_msg="Что сейчас модно в китае?")
        res = await workflow.run(user_msg="А теперь белую!")
        print(res)
        draw_all_possible_flows(MainWorkflow, filename="basic_workflow.html")
        draw_most_recent_execution(workflow, filename="basic_workflow_execution.html")

    asyncio.run(main())
