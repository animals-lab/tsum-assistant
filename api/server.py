from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import logging
import json

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

def stream_chat_response():
    # The content needs to be JSON-encoded
    yield f"0:{json.dumps('example')}\n"
    # This will output: 0:"example"\n
    
    # Send completion message
    yield 'd:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":5}}\n'

@app.get("/api/health")
async def health_check():
    return {"status": "ok"} 

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    logger.info(f"Received request body: {body}")
    
    try:
        response = StreamingResponse(
            stream_chat_response(),
            media_type='text/event-stream'
        )
        response.headers['x-vercel-ai-data-stream'] = 'v1'
        logger.info("Streaming response initiated")

        return response
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise

