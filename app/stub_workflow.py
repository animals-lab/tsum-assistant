import asyncio

from enum import Enum
from typing import Optional

from llama_index.core.workflow import (
    Event,
    Workflow,
    step,
    Context,
    StartEvent,
    StopEvent,
    draw_all_possible_flows,
)


class AgentRunEventType(Enum):
    TEXT = "text"
    PROGRESS = "progress"


class ProgressEvent(Event):
    msg: str


class AgentRunEvent(Event):
    name: str
    msg: str
    event_type: AgentRunEventType = AgentRunEventType.TEXT
    data: Optional[dict] = None

    def to_response(self) -> dict:
        return {
            "type": "agent",
            "data": {
                "agent": self.name,
                "type": self.event_type.value,
                "text": self.msg,
                "data": self.data,
            },
        }


class InputEvent(Event): ...


class ResearchEvent(Event): ...


class AnalyzeEvent(Event):
    result: str


class SummarizeEvent(Event): ...


class StubWorkflow(Workflow):
    @step
    async def handle_input(self, ctx: Context, ev: StartEvent) -> InputEvent:
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Консультант",
                msg="Привлекаем экспертов",
            )
        )

        for i in range(4):
            await asyncio.sleep(1)
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Консультант",
                    msg="Собираем информацию",
                    event_type=AgentRunEventType.PROGRESS,
                    data={
                        "id": 0,
                        "total": 4,
                        "current": i,
                    },
                )
            )
        return InputEvent()

    @step
    async def research(self, ctx: Context, ev: InputEvent) -> ResearchEvent:
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Поиск",
                msg="Ищем информацию о модных тенденциях в южной корее",
            )
        )
        await asyncio.sleep(2)

        for i in range(4):
            await asyncio.sleep(1)
            ctx.write_event_to_stream(
                AgentRunEvent(
                    name="Поиск",
                    msg="Собираем информацию",
                    event_type=AgentRunEventType.PROGRESS,
                    data={
                        "id": 0,
                        "total": 3,
                        "current": i,
                    },
                )
            )


        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Поиск",
                msg="Прочитали статьи и собрали информацию",
            )
        )
        await asyncio.sleep(2)
        return ResearchEvent()

    @step
    async def analyze(self, ctx: Context, ev: ResearchEvent) -> AnalyzeEvent:
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Эксперт по моде",
                msg="Формируем рекомендации",
            )
        )

        response = "В Южной Корее мода постоянно эволюционирует, и 2024 год не стал исключением. Тенденции формируются под влиянием K-pop, уличной моды и традиционных элементов, создавая уникальный стиль. Вот основные модные направления, которые актуальны в Южной Корее на данный момент."
        await asyncio.sleep(2)

        for word in response.split(" "):
            await asyncio.sleep(0.1)
            ctx.write_event_to_stream(ProgressEvent(msg=word))

        await asyncio.sleep(2)

        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Эксперт по моде",
                msg="Рекомендации готовы",
            )
        )
        return AnalyzeEvent(result=response)

    @step
    async def summarize(self, ctx: Context, ev: AnalyzeEvent) -> StopEvent:
        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Консультант",
                msg="Ищем примеры в нашем каталоге",
            )
        )
        return StopEvent(result="FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")


async def main():
    w = StubWorkflow(timeout=30, verbose=True)
    handler = w.run(first_input="Что модно в Южной Корее?", streaming=True)

    async for ev in handler.stream_events():
        if isinstance(ev, ProgressEvent):
            print(ev.msg)

    final_result = await handler
    print("Final result", final_result)

    # draw_all_possible_flows(StubWorkflow, filename="streaming_workflow.html")


if __name__ == "__main__":
    asyncio.run(main())
