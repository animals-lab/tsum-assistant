from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, AsyncGenerator
import json
import logging
import traceback
from asyncio import Queue
import uuid
from api.routers.vercel import VercelStreamResponse

from app.workflow import (
    ConciergeAgent,
    ProgressEvent,
    ToolRequestEvent,
    ToolApprovedEvent,
    ToolCallEvent,
    ToolCallResultEvent,
)
from app.agent import get_initial_state, get_agent_configs
from llama_index.llms.openai import OpenAI
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
import llama_index.core
from app.catalog.query import query_catalog, product_queue
from app.catalog.models import GenderType, Offer
from api.routers.vercel import VercelStreamResponse

# Set up root logger with custom formatter
logging.basicConfig(
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    force=True,  # Force override any existing handlers
    encoding='utf-8'
)

llama_index.core.set_global_handler(
    "arize_phoenix", endpoint="https://llamatrace.com/v1/traces"
)

# Set specific levels for different loggers
logging.getLogger('uvicorn').setLevel(logging.CRITICAL)
logging.getLogger('fastapi').setLevel(logging.CRITICAL)
logging.getLogger('vercel').setLevel(logging.CRITICAL)
logging.getLogger('api_server').setLevel(logging.CRITICAL)
logging.getLogger('workflow').setLevel(logging.INFO)  # Keep workflow logs visible

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active agent sessions and their memory
agent_sessions: Dict[str, ConciergeAgent] = {}
memory_buffers: Dict[str, ChatMemoryBuffer] = {}
chat_histories: Dict[str, List[ChatMessage]] = {}


class ChatMessage(BaseModel):
    role: str
    content: str

class CatalogQueryResponse(BaseModel):
    items: List[Offer]
    scores: List[float]

llm = OpenAI(model="gpt-4o-mini", temperature=0.4)



@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        logger.info("Received request to /api/chat")
        body = await request.json()
        messages = body.get("messages", [])
        session_id = body.get("session_id", "default")
        
        # Get the last message content
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        last_message = messages[-1]
        user_message = last_message.get("content", "")
        
        logger.info(f"Processing message: {user_message[:100]}...")

        # Create new agent session and memory if doesn't exist
        if session_id not in agent_sessions:
            logger.info(f"Creating new agent session for {session_id}")
            
            memory_buffers[session_id] = ChatMemoryBuffer.from_defaults(llm=llm)
            chat_histories[session_id] = []
            agent_sessions[session_id] = ConciergeAgent(timeout=None)

        agent = agent_sessions[session_id]
        memory = memory_buffers[session_id]
        chat_history = chat_histories[session_id]

        async def event_stream():
            try:
                logger.info("Starting agent")
                handler = agent.run(
                    user_msg=user_message,
                    agent_configs=get_agent_configs(),
                    llm=llm,
                    chat_history=memory.get(),
                    initial_state=get_initial_state()
                )
                logger.info("Agent handler created")

                async for event in handler.stream_events():
                    logger.info(f"Processing event: {event}")
                    
                    if isinstance(event, ProgressEvent):
                        # Stream progress message as text (0: prefix)
                        yield VercelStreamResponse.text_part(event.msg)
                    
                    elif isinstance(event, ToolRequestEvent):
                        # Tool request event (9: prefix)
                        logger.info(f"Tool request: {event.tool_name}")
                        yield VercelStreamResponse.tool_call(
                            tool_id=event.tool_id,
                            name=event.tool_name,
                            args=event.tool_kwargs
                        )
                        
                        # Auto-approve tool
                        handler.ctx.send_event(
                            ToolApprovedEvent(
                                tool_id=event.tool_id,
                                tool_name=event.tool_name,
                                tool_kwargs=event.tool_kwargs,
                                approved=True,
                            )
                        )
                        
                    elif isinstance(event, ToolApprovedEvent):
                        # Tool approved event - no stream output needed
                        logger.info(f"Tool approved: {event.tool_name}")
                        
                    elif isinstance(event, ToolCallEvent):
                        # Tool call event (9: prefix)
                        logger.info(f"Tool call: {event.tool_name}")
                        yield VercelStreamResponse.tool_call(
                            tool_id=event.tool_id,
                            name=event.tool_name,
                            args=event.args
                        )
                        
                    elif isinstance(event, ToolCallResultEvent):
                        # Tool result event (a: prefix)
                        logger.info(f"Tool result: {event.tool_id}")
                        # Include msg in the result output
                        result_data = {
                            "result": event.result,
                            "text": event.msg if event.msg else "Tool completed"
                        }
                        yield VercelStreamResponse.tool_result(
                            tool_id=event.tool_id,
                            name=event.tool_name,
                            args=event.args,
                            result=result_data
                        )

                # Get final result
                result = await handler
                response = result.get('response', 'No response generated')
                logger.info(f"Final response: {response[:100]}...")

                # Stream final response as text (0: prefix)
                yield VercelStreamResponse.text_part(response)

                # Send finish message (e: prefix)
                yield VercelStreamResponse.finish_step(
                    reason="stop",
                    prompt_tokens=0,
                    completion_tokens=0
                )

            except Exception as e:
                logger.error(f"Error in event stream: {str(e)}")
                logger.error(traceback.format_exc())
                raise e

        return VercelStreamResponse(request, event_stream())

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/api/chat-debug")
async def chat_stub_endpoint(request: Request):
    try:
        logger.info("Received request to /api/chat")
        body = await request.json()
        messages = body.get("messages", [])
        
        # Get the last message content
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        last_message = messages[-1]
        user_message = last_message.get("content", "")
        
        logger.info(f"Echoing message: {user_message[:100]}...")

        async def event_stream():
            # Stream the user's message back as text
            
            #yield {"id":"message-123", "role":"user", "content":"user message yo!!!"}
            # yield '0:"just a text message"\n'
            # yield '2:[{"id":"message-123", "role":"user", "content":"user message"}, {"anotherKey":"object2"}]\n'
            # yield '8:[{"id":"message-123","other":"annotation"}]\n'

            # # this works, raises error in js, breaks execution       
            # #yield '3:"error message"\n'
        
            
            # # this works, works, but not doesnt call onToolCall in js
            # yield 'b:{"toolCallId":"call-456","toolName":"streaming-tool"}\n'
            # yield 'c:{"toolCallId":"call-456","argsTextDelta":"partial arg"}\n'
            # yield 'a:{"toolCallId":"call-456","result":"tool output", "text":"call a"}\n'
            # yield 'e:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20}, "isContinued":false}\n'
            
            # this works, calls onToolCall in js
            yield '9:{"toolCallId":"call-123","toolName":"my-tool","args":{"some":"argument"}, "text":"call 9"}\n'
            yield 'a:{"toolCallId":"call-123","result":"tool output", "text":"call a"}\n'
            # this kinda works
            yield 'e:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20, "toolCalls":["call-123"]},"isContinued":false}\n'
            
            # # # this raises error: must be array, wrapped in array shows nothing
            # # yield '8:{"id":"message-123","other":"annotation"}\n'
            
            yield '0:"' + user_message + "sasa"'"\n'
      
            yield 'd:{"finishReason":"stop"}\n'

            # yield VercelStreamResponse.text_part(user_message)
            
            # # Send finish message
            # yield VercelStreamResponse.finish_message(
            #     reason="stop",
            #     prompt_tokens=0,
            #     completion_tokens=0
            # )

        return VercelStreamResponse(request, event_stream())

    except Exception as e:
        logger.error(f"Error in chat stub endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

"""
sample query:
http://localhost:8000/api/catalog?query_text=элегантное%20платье&gender=Женский&limit=5
http://localhost:8000/api/catalog?category=Брюки&category=Джинсы&color=Чёрный&color=Синий&gender=Мужской&min_price=5000&max_price=15000
http://localhost:8000/api/catalog?vendor=Gucci&vendor=Prada&material=Кашемир&material=Шерсть&offset=20&limit=20
http://localhost:8000/api/catalog?query_text=кожаная%20сумка&color=Чёрный&min_price=50000&max_price=200000&vendor=Prada
"""
@app.get("/api/catalog", response_model=CatalogQueryResponse)
async def get_catalog(
    query_text: str = Query(default="", description="Free-form text query"),
    vendor: Optional[List[str]] = Query(default=None, description="List of brand names"),
    category: Optional[List[str]] = Query(default=None, description="List of product categories"),
    color: Optional[List[str]] = Query(default=None, description="List of colors"),
    gender: Optional[GenderType] = Query(default=None, description="Gender filter"),
    min_price: Optional[float] = Query(default=None, description="Minimum price"),
    max_price: Optional[float] = Query(default=None, description="Maximum price"),
    material: Optional[List[str]] = Query(default=None, description="List of materials"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
):
    try:
        logger.info(f"Querying catalog with parameters: {locals()}")
        items, scores = await query_catalog(
            query_text=query_text,
            vendor=vendor,
            category=category,
            color=color,
            gender=gender,
            min_price=min_price,
            max_price=max_price,
            material=material,
            limit=limit,
            offset=offset,
        )
        return CatalogQueryResponse(items=items, scores=scores)
    except Exception as e:
        logger.error(f"Error in catalog query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/product-stream")
async def stream_products(request: Request):
    """
    Streams products from the product queue as Server-Sent Events.
    Each event contains a JSON-serialized Offer object.
    """
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("Client disconnected from product stream")
                    break

                # Wait for the next item from the queue
                offer: Offer = await product_queue.get()
                
                # Convert the Offer to JSON and format as SSE
                json_data = offer.model_dump_json()
                yield f"event: product\ndata: {json_data}\n\n"
                
                # Mark the task as done
                product_queue.task_done()

        except Exception as e:
            logger.error(f"Error in product stream: {str(e)}")
            logger.error(traceback.format_exc())
            yield f"event: error\ndata: {json.dumps(str(e))}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

