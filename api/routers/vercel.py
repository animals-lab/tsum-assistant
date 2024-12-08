from fastapi import Request
from fastapi.responses import StreamingResponse
import json
import logging
from typing import AsyncGenerator, Any, Dict, Optional
import uuid

# Set up logging
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VercelStreamResponse(StreamingResponse):
    """
    Class to convert the response to the streaming format expected by Vercel AI SDK.
    Implements the protocol defined at: https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol
    """
    # Stream part type prefixes
    TEXT_PART = "0:"           # Text chunks
    DATA_PART = "2:"           # Data arrays
    ERROR_PART = "3:"          # Errors
    MESSAGE_ANNOTATION_PART = "8:"        # Message annotations
    TOOL_CALL = "9:"          # Tool calls
    TOOL_RESULT = "a:"        # Tool results
    TOOL_CALL_START = "b:"    # Start of streaming tool call
    TOOL_CALL_DELTA = "c:"    # Tool call delta updates
    FINISH_MESSAGE = "d:"     # Stream completion
    FINISH_STEP = "e:"        # Step completion

    def __init__(
        self,
        request: Request,
        response_generator: AsyncGenerator[str, None],
    ):
        content = VercelStreamResponse.content_generator(request, response_generator)
        super().__init__(
            content=content,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "Content-Encoding": "none",
                "Transfer-Encoding": "chunked",
                "x-vercel-ai-data-stream": "v1"  # Required for data stream protocol
            }
        )

    @classmethod
    async def content_generator(
        cls,
        request: Request,
        response_generator: AsyncGenerator[str, None],
    ):
        try:
            async for token in response_generator:
                if await request.is_disconnected():
                    break
                
                # Check if token is already prefixed
                if isinstance(token, str) and token.startswith(('0:', '2:', '3:', '8:', '9:', 'a:', 'b:', 'c:', 'd:', 'e:')):
                    # Ensure each token is flushed immediately
                    yield f"{token}\n".encode('utf-8')
                else:
                    # Stream the text content
                    text_part = cls.text_part(token)
                    yield text_part.encode('utf-8')

        except Exception as e:
            logger.error(f"Error in stream response: {str(e)}")
            error_part = cls.error_part(str(e))
            yield error_part.encode('utf-8')

    @classmethod
    def message_part(cls, message: dict) -> str:
        """Stream message"""
        result = f"messages:{json.dumps(message)}\n"
        logger.info(f"Sending message part: {result}")
        return result        

    @classmethod
    def text_part(cls, text: str) -> str:
        """Stream text chunk"""
        result = f"{cls.TEXT_PART}{json.dumps(text)}\n"
        logger.info(f"Sending text part: {result}")
        return result

    @classmethod
    def data_part(cls, data: list) -> str:
        """Stream data array"""
        result = f"{cls.DATA_PART}{json.dumps(data)}\n"
        logger.info(f"Sending data part: {result}")
        return result

    @classmethod
    def error_part(cls, error: str) -> str:
        """Stream error message"""
        result = f"{cls.ERROR_PART}{json.dumps(error)}\n"
        logger.error(f"Sending error part: {result}")  # Use error level for errors
        return result

    @classmethod
    def message_annotation(cls, data: Dict[str, Any]) -> str:
        """Stream message annotation"""
        result = f"{cls.MESSAGE_ANNOTATION_PART}{json.dumps(data)}\n"
        logger.info(f"Sending message annotation: {result}")
        return result

    @classmethod
    def tool_call(cls, tool_id: str, name: str, args: Dict[str, Any]) -> str:
        """Stream tool call"""
        data = {
            "toolCallId": tool_id,
            "toolName": name,
            "args": args
        }
        result = f"{cls.TOOL_CALL}{json.dumps(data)}\n"
        logger.info(f"Sending tool call: {result}")
        return result

    @classmethod
    def tool_result(cls, tool_id: str, name: str, args: Dict[str, Any], result: Any) -> str:
        """Stream tool result"""
        data = {
            "toolCallId": tool_id,
            "toolName": name,
            "args": args,
            "result": result
        }
        result_str = f"{cls.TOOL_RESULT}{json.dumps(data)}\n"
        logger.info(f"Sending tool result: {result_str}")
        return result_str

    @classmethod
    def tool_call_start(cls, tool_id: str, name: str) -> str:
        """Stream start of tool call"""
        data = {
            "toolCallId": tool_id,
            "toolName": name
        }
        result = f"{cls.TOOL_CALL_START}{json.dumps(data)}\n"
        logger.info(f"Sending tool call start: {result}")
        return result

    @classmethod
    def tool_call_delta(cls, tool_id: str, delta: str) -> str:
        """Stream tool call delta"""
        data = {
            "toolCallId": tool_id,
            "argsTextDelta": delta
        }
        result = f"{cls.TOOL_CALL_DELTA}{json.dumps(data)}\n"
        logger.info(f"Sending tool call delta: {result}")
        return result

    @classmethod
    def finish_step(
        cls, 
        reason: str = "stop",
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        is_continued: bool = False
    ) -> str:
        """Stream step completion"""
        data = {
            "finishReason": reason,
            "usage": {
                "promptTokens": prompt_tokens or 0,
                "completionTokens": completion_tokens or 0
            },
            "isContinued": is_continued
        }
        result = f"{cls.FINISH_STEP}{json.dumps(data)}\n"
        logger.info(f"Sending finish step: {result}")
        return result

    @classmethod
    def finish_message(
        cls,
        reason: str = "stop",
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None
    ) -> str:
        """Stream message completion"""
        data = {
            "finishReason": reason,
            "usage": {
                "promptTokens": prompt_tokens or 0,
                "completionTokens": completion_tokens or 0
            }
        }
        result = f"{cls.FINISH_MESSAGE}{json.dumps(data)}\n"
        logger.info(f"Sending finish message: {result}")
        return result
