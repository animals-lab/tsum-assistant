from fastapi import FastAPI, Request
from typing import AsyncGenerator
from .vercel import VercelStreamResponse
import asyncio
import json

async def generate_test_messages() -> AsyncGenerator[str, None]:
    """Generate test messages in various Vercel Stream Protocol formats"""
    
    def format_message(content: str, message_type: str = "text") -> str:
        if message_type == "text":
            return f'0:"{content}"\n'
        elif message_type == "tool_call":
            return f'9:{json.dumps(content)}\n'
        elif message_type == "tool_result":
            return f'a:{json.dumps(content)}\n'
        elif message_type == "markdown":
            return f'8:{json.dumps([{"type": "markdown", "content": content}])}\n'
        elif message_type == "annotations":
            return f'8:{json.dumps(content)}\n'
        return ""
    
    # Initial message with completion
    yield format_message("Hello, let's start with a simple task.")
    yield 'e:{"finishReason":"stop", "usage":{"promptTokens":100,"completionTokens":150},"isContinued":true}\n'
    await asyncio.sleep(0.5)

    # Tool call
    tool_call = {
        "toolCallId": "analyze_1",
        "toolName": "analyze_code",
        "args": {
            "code": "sample code",
            "language": "python"
        }
    }
    yield format_message(tool_call, "tool_call")
    yield 'e:{"finishReason":"tool_calls","usage":{"promptTokens":100,"completionTokens":150},"isContinued":true}\n'
    await asyncio.sleep(0.5)

    # Tool result
    tool_result = {
        "toolCallId": "analyze_1",
        "result": {
            "analysis": "Code analysis complete",
            "suggestions": ["Suggestion 1", "Suggestion 2"]
        }
    }
    yield format_message(tool_result, "tool_result")
    yield 'e:{"finishReason":"tool_calls","usage":{"promptTokens":100,"completionTokens":150},"isContinued":true}\n'
    await asyncio.sleep(0.5)

    # Add annotations (code block, markdown, and image)
    annotations = [
        {
            "type": "code",
            "id": "code-1",
            "language": "python",
            "code": """def example_function():
    # This is a sample code block
    print("Hello, World!")
    
    # Using some keywords
    for i in range(10):
        if i % 2 == 0:
            print(f"Number {i} is even")
            """
        },
        {
            "type": "markdown",
            "id": "md-1",
            "content": """# Example ANNOTATIONS
## Features
- **Bold text** for emphasis
- *Italic text* for style
- `inline code` for technical terms

### Code Example
```python
print("Hello from markdown!")
```"""
        },
        {
            "type": "image",
            "id": "img-1",
            "url": "https://picsum.photos/200/300",
            "title": "Sample Image",
            "caption": "This is a sample image from Lorem Picsum"
        }
    ]
    
    yield format_message(annotations, "annotations")
    yield 'e:{"finishReason":"stop","usage":{"promptTokens":100,"completionTokens":150},"isContinued":true}\n'
    await asyncio.sleep(1.5)

    # Final response with completion
    yield format_message("Here are the suggestions for improving your code, along with some examples and documentation. Would you like to proceed with implementing them?")
    yield 'd:{"finishReason":"stop","usage":{"promptTokens":100,"completionTokens":150}}\n'


async def test_stream(request: Request):
    """Test endpoint that generates various types of Vercel stream messages"""
    request_id = id(request)  # Get a unique ID for this request
    print(f"DEBUG: Starting test stream for request {request_id}")
    
    response_generator = generate_test_messages()
    
    return VercelStreamResponse(
        request=request,
        response_generator=response_generator,
    )

# Add this to your FastAPI app routes:
# app.post("/api/test-stream")(test_stream) 