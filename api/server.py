from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, AsyncGenerator
import logging
import json
from .routers.vercel import VercelStreamResponse
from .routers.test_stream import test_stream
# from app.agent import SimpleAgent
from app.stub_workflow import StubWorkflow
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, AsyncGenerator
import json
import logging
import traceback
from asyncio import Queue
from app.catalog.models import GenderType, Offer
from app.catalog.query import query_catalog, product_queue

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
@app.get("/api/health")
async def health_check():
    return {"status": "ok"} 

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    logger.info(f"Received request body: {body}")
    
    try:
        # Extract the message from the request body
        user_message = body.get("messages", [{}])[-1].get("content", "")
        
        # Create response generator
        workflow = StubWorkflow(timeout=30).run(input=user_message, streaming=True)
        
        # Create Vercel stream response
        response = VercelStreamResponse(
            request=request,
            event_handler=workflow,
            events = workflow.stream_events()
        )
        
        logger.info("Streaming response initiated")
        return response
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise

# Add test stream endpoint
app.post("/api/test-stream")(test_stream)


class ChatMessage(BaseModel):
    role: str
    content: str

class CatalogQueryResponse(BaseModel):
    items: List[Offer]
    scores: List[float]

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


