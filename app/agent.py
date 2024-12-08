from llama_index.core.base.llms.types import ChatMessage
from llama_index.llms.openai import OpenAI

from enum import Enum
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
    Context,
    Event,
)

system_prompt = """
You are a helpful assistant
"""

class AgentRunEventType(Enum):
    TEXT = "text"
    PROGRESS = "progress"

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

class SimpleAgent(Workflow):
    
    @step
    async def chat_with_user(self, ctx: Context, ev: StartEvent) -> StopEvent:
        # Create a new list with all messages plus the new input
        llm = OpenAI(model="gpt-4o-mini")


        chat_messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=ev.input)
        ]

        ctx.write_event_to_stream(
            AgentRunEvent(
                name="Researcher",
                msg="Finding answers for missing cells",
            )
        )

        response = await llm.achat(messages=chat_messages)
        
        return StopEvent(result=response.message.content)



async def main():
    w = SimpleAgent(timeout=10, verbose=True)
    result = await w.run(input="Hello, how are you?")
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())