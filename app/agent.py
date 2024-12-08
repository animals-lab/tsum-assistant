from llama_index.core.base.llms.types import ChatMessage
from llama_index.llms.openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

system_prompt = """
You are a helpful assistant
"""


class SimpleAgent(Workflow):
    
    @step
    async def chat_with_user(self, ev: StartEvent) -> StopEvent:
        # Create a new list with all messages plus the new input
        llm = OpenAI(model="gpt-4o")


        chat_messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=ev.input)
        ]

        response = await llm.achat(messages=chat_messages)
        
        return StopEvent(result=response.message.content)



async def main():
    w = SimpleAgent(timeout=10, verbose=True)
    result = await w.run(input="Hello, how are you?")
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())