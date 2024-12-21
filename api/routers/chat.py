import json
import logging
import traceback

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer

from api.lib.vercel import VercelStreamResponse
from app.agent import get_agent_configs, get_initial_state
from app.workflow import ConciergeAgent
from agent.workflows.main import MainWorkflow

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat")
async def chat_endpoint(request: Request):
    try:
        logger.info("Received request to /chat")
        body = await request.json()
        messages = body.get("messages", [])

        # Get the last message content
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        last_message = messages[-1]
        user_message = last_message.get("content", "")

        memory = ChatMemoryBuffer.from_defaults(chat_history=messages[:-1])
        agent = MainWorkflow(timeout=60, verbose=True, chat_memory=memory)

        event_handler = agent.run(
            user_msg=user_message,
            streaming=True,
        )

        return VercelStreamResponse(
            event_handler=event_handler,
            events=agent.stream_events(),
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/oldchat")
async def oldchat_endpoint(request: Request):
    try:
        logger.info("Received request to /chat")
        body = await request.json()
        messages = body.get("messages", [])

        # Get the last message content
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        last_message = messages[-1]
        user_message = last_message.get("content", "")

        agent = ConciergeAgent(timeout=60, verbose=True)

        event_handler = agent.run(
            user_msg=user_message,
            agent_configs=get_agent_configs(),
            chat_history=[
                ChatMessage(role=m["role"], content=m["content"]) for m in messages[:-1]
            ],
            initial_state=get_initial_state(),
            streaming=True,
        )

        return VercelStreamResponse(
            event_handler=event_handler,
            events=agent.stream_events(),
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)
