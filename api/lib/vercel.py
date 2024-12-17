from fastapi import Request
from fastapi.responses import StreamingResponse
import json
import logging
from typing import AsyncGenerator, Any, Dict, Optional
import uuid
from typing import Awaitable
import asyncio
from aiostream import stream
from app.workflow_events import AgentRunEvent, ProgressEvent
from llama_index.core.llms import ChatMessage
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VercelStreamResponse(StreamingResponse):
    """
    Base class to convert the response from the chat engine to the streaming format expected by Vercel
    """

    TEXT_PREFIX = "0:"
    DATA_PREFIX = "2:"
    ANNOTATION_PREFIX = "8:"
    ERROR_PREFIX = "3:"

    def __init__(self, *args, **kwargs):
        content = self.content_generator(*args, **kwargs)
        super().__init__(content=content)

    async def content_generator(self, event_handler, events):
        stream = self._create_stream(
            event_handler, events
        )
        is_stream_started = False
        try:
            async with stream.stream() as streamer:
                async for output in streamer:
                    if not is_stream_started:
                        is_stream_started = True
                        # Stream a blank message to start the stream
                        yield self.convert_text("")

                    yield output
        except asyncio.CancelledError:
            logger.warning("Workflow has been cancelled!")
        except Exception as e:
            logger.error(
                f"Unexpected error in content_generator: {str(e)}", exc_info=True
            )
            yield self.convert_error(
                "An unexpected error occurred while processing your request, preventing the creation of a final answer. Please try again."
            )
        finally:
            await event_handler.cancel_run()
            logger.info("The stream has been stopped!")

    def _create_stream(
        self,
        event_handler: Awaitable,
        events: AsyncGenerator,
        verbose: bool = True,
    ):
        # Yield the text response
        async def _chat_response_generator():
            result = await event_handler
            final_response = ""

            if isinstance(result, AsyncGenerator):
                async for token in result:
                    final_response += str(token.delta)
                    yield self.convert_text(token.delta)
            else:
                if content:= result.get('response'):
                    final_response += content
                    yield self.convert_text(content)
                elif hasattr(result, "response"):
                    content = result.response.message.content
                    if content:
                        for token in content:
                            final_response += str(token)
                            yield self.convert_text(token)
                else:
                    yield self.convert_text(result)

            # Generate next questions if next question prompt is configured
            # question_data = await self._generate_next_questions(
            #     chat_data.messages, final_response
            # )
            # if question_data:
            #     yield self.convert_data(question_data)

            # TODO: stream sources

        # Yield the events from the event handler
        async def _event_generator():
            async for event in events:
                response = None
                if hasattr(event, "to_annotation"):
                    response = self.convert_object(event.to_annotation(), prefix=self.ANNOTATION_PREFIX)
                elif hasattr(event, "to_data"):
                    response = self.convert_object(event.to_data(), prefix=self.DATA_PREFIX)
                elif hasattr(event, "to_markdown"):
                    response = self.convert_text(event.to_markdown()+"\n\n")
                elif isinstance(event, ProgressEvent):
                    response = self.convert_text(event.msg + " ")

                if response is not None:
                    yield response

        combine = stream.merge(_chat_response_generator(), _event_generator())
        return combine

    @classmethod
    def convert_text(cls, token: str):
        # Escape newlines and double quotes to avoid breaking the stream
        token = json.dumps(token)
        return f"{cls.TEXT_PREFIX}{token}\n"

    @classmethod
    def convert_object(cls, data: dict, prefix: str=None):
        if prefix is None: 
            prefix = cls.ANNOTATION_PREFIX

        data_str = json.dumps(data)
        return f"{prefix}[{data_str}]\n"

    @classmethod
    def convert_error(cls, error: str):
        error_str = json.dumps(error)
        return f"{cls.ERROR_PREFIX}{error_str}\n"

    # @staticmethod
    # async def _generate_next_questions(chat_history: List[Message], response: str):
    #     questions = await NextQuestionSuggestion.suggest_next_questions(
    #         chat_history, response
    #     )
    #     if questions:
    #         return {
    #             "type": "suggested_questions",
    #             "data": questions,
    #         }
    #     return None


# class VercelStreamResponse(StreamingResponse):
#     """
#     Class to convert the response to the streaming format expected by Vercel AI SDK.
#     Implements the protocol defined at: https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol
#     """
#     # Stream part type prefixes
#     TEXT_PART = "0:"           # Text chunks
#     DATA_PART = "2:"           # Data arrays
#     ERROR_PART = "3:"          # Errors
#     MESSAGE_ANNOTATION_PART = "8:"        # Message annotations
#     TOOL_CALL = "9:"          # Tool calls
#     TOOL_RESULT = "a:"        # Tool results
#     TOOL_CALL_START = "b:"    # Start of streaming tool call
#     TOOL_CALL_DELTA = "c:"    # Tool call delta updates
#     FINISH_MESSAGE = "d:"     # Stream completion
#     FINISH_STEP = "e:"        # Step completion

#     def __init__(
#         self,
#         request: Request,
#         response_generator: AsyncGenerator[str, None],
#     ):
#         content = self.content_generator(request, response_generator)
#         super().__init__(
#             content=content,
#             media_type="text/event-stream",
#             headers={
#                 "Cache-Control": "no-cache, no-transform",
#                 "Connection": "keep-alive",
#                 "Content-Encoding": "none",
#                 "Transfer-Encoding": "chunked",
#                 "x-vercel-ai-data-stream": "v1"  # Required for data stream protocol
#             }
#         )

#     @classmethod
#     async def content_generator(
#         cls,
#         request: Request,
#         response_generator: AsyncGenerator[str, None],
#     ):
#         try:
#             async for token in response_generator:
#                 if await request.is_disconnected():
#                     break

#                 # Check if token is already prefixed
#                 if isinstance(token, str) and token.startswith(('0:', '2:', '3:', '8:', '9:', 'a:', 'b:', 'c:', 'd:', 'e:')):
#                     # Ensure each token is flushed immediately
#                     yield f"{token}\n".encode('utf-8')
#                 else:
#                     # Stream the text content
#                     text_part = cls.text_part(token)
#                     yield text_part.encode('utf-8')

#         except Exception as e:
#             logger.error(f"Error in stream response: {str(e)}")
#             error_part = cls.error_part(str(e))
#             yield error_part.encode('utf-8')

#     @classmethod
#     def message_part(cls, message: dict) -> str:
#         """Stream message"""
#         result = f"messages:{json.dumps(message)}\n"
#         logger.info(f"Sending message part: {result}")
#         return result

#     @classmethod
#     def text_part(cls, text: str) -> str:
#         """Stream text chunk"""
#         result = f"{cls.TEXT_PART}{json.dumps(text)}\n"
#         logger.info(f"Sending text part: {result}")
#         return result

#     @classmethod
#     def data_part(cls, data: list) -> str:
#         """Stream data array"""
#         result = f"{cls.DATA_PART}{json.dumps(data)}\n"
#         logger.info(f"Sending data part: {result}")
#         return result

#     @classmethod
#     def error_part(cls, error: str) -> str:
#         """Stream error message"""
#         result = f"{cls.ERROR_PART}{json.dumps(error)}\n"
#         logger.error(f"Sending error part: {result}")  # Use error level for errors
#         return result

#     @classmethod
#     def message_annotation(cls, data: Dict[str, Any]) -> str:
#         """Stream message annotation"""
#         result = f"{cls.MESSAGE_ANNOTATION_PART}{json.dumps(data)}\n"
#         logger.info(f"Sending message annotation: {result}")
#         return result

#     @classmethod
#     def tool_call(cls, tool_id: str, name: str, args: Dict[str, Any]) -> str:
#         """Stream tool call"""
#         data = {
#             "toolCallId": tool_id,
#             "toolName": name,
#             "args": args
#         }
#         result = f"{cls.TOOL_CALL}{json.dumps(data)}\n"
#         logger.info(f"Sending tool call: {result}")
#         return result

#     @classmethod
#     def tool_result(cls, tool_id: str, name: str, args: Dict[str, Any], result: Any) -> str:
#         """Stream tool result"""
#         data = {
#             "toolCallId": tool_id,
#             "toolName": name,
#             "args": args,
#             "result": result
#         }
#         result_str = f"{cls.TOOL_RESULT}{json.dumps(data)}\n"
#         logger.info(f"Sending tool result: {result_str}")
#         return result_str

#     @classmethod
#     def tool_call_start(cls, tool_id: str, name: str) -> str:
#         """Stream start of tool call"""
#         data = {
#             "toolCallId": tool_id,
#             "toolName": name
#         }
#         result = f"{cls.TOOL_CALL_START}{json.dumps(data)}\n"
#         logger.info(f"Sending tool call start: {result}")
#         return result

#     @classmethod
#     def tool_call_delta(cls, tool_id: str, delta: str) -> str:
#         """Stream tool call delta"""
#         data = {
#             "toolCallId": tool_id,
#             "argsTextDelta": delta
#         }
#         result = f"{cls.TOOL_CALL_DELTA}{json.dumps(data)}\n"
#         logger.info(f"Sending tool call delta: {result}")
#         return result

#     @classmethod
#     def finish_step(
#         cls,
#         reason: str = "stop",
#         prompt_tokens: Optional[int] = None,
#         completion_tokens: Optional[int] = None,
#         is_continued: bool = False
#     ) -> str:
#         """Stream step completion"""
#         data = {
#             "finishReason": reason,
#             "usage": {
#                 "promptTokens": prompt_tokens or 0,
#                 "completionTokens": completion_tokens or 0
#             },
#             "isContinued": is_continued
#         }
#         result = f"{cls.FINISH_STEP}{json.dumps(data)}\n"
#         logger.info(f"Sending finish step: {result}")
#         return result

#     @classmethod
#     def finish_message(
#         cls,
#         reason: str = "stop",
#         prompt_tokens: Optional[int] = None,
#         completion_tokens: Optional[int] = None
#     ) -> str:
#         """Stream message completion"""
#         data = {
#             "finishReason": reason,
#             "usage": {
#                 "promptTokens": prompt_tokens or 0,
#                 "completionTokens": completion_tokens or 0
#             }
#         }
#         result = f"{cls.FINISH_MESSAGE}{json.dumps(data)}\n"
#         logger.info(f"Sending finish message: {result}")
#         return result
