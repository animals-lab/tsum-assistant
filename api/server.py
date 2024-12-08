from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, AsyncGenerator
import logging
import json
from .routers.vercel import VercelStreamResponse
from .routers.test_stream import test_stream
from app.agent import SimpleAgent

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

async def generate_agent_response(message: str) -> AsyncGenerator[str, None]:
    agent = SimpleAgent(timeout=30, verbose=True)
    result = await agent.run(input=message)
    
    # Stream the response
    yield result
    
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
        response_generator = generate_agent_response(user_message)
        
        # Create Vercel stream response
        response = VercelStreamResponse(
            request=request,
            response_generator=response_generator,
        )
        
        logger.info("Streaming response initiated")
        return response
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise

# Add test stream endpoint
app.post("/api/test-stream")(test_stream)

