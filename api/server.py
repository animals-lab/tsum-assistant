from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, AsyncGenerator
import logging
import json
from .routers.vercel import VercelStreamResponse
from .routers.test_stream import test_stream
from app.agent import SimpleAgent
from app.stub_workflow import StubWorkflow

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

