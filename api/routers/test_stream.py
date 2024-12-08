from fastapi import FastAPI, Request
from typing import AsyncGenerator
from .vercel import VercelStreamResponse
import asyncio
import json

async def generate_test_messages() -> AsyncGenerator[str, None]:
    """Generate test messages in various Vercel Stream Protocol formats"""
    
    # Initial response with text format
    yield '0:"Let me analyze your code and suggest some improvements. First, I\'ll check the code structure."\n'
    await asyncio.sleep(1)
    
    # Code analysis tool call
    tool_call = {
        "toolCallId": "analyze_1",
        "toolName": "analyze_code_structure",
        "args": {
            "path": "./src",
            "include_patterns": ["*.ts", "*.tsx"]
        }
    }
    yield f'9:{json.dumps(tool_call)}\n'
    await asyncio.sleep(2)
    
    # Tool result with findings
    tool_result = {
        "toolCallId": "analyze_1",
        "result": {
            "files": 15,
            "components": 8,
            "hooks": 4,
            "issues": ["Missing type definitions", "Inconsistent import style"]
        }
    }
    yield f'a:{json.dumps(tool_result)}\n'
    await asyncio.sleep(1)
    
    # Analysis summary with markdown
    markdown = [{
        "id": "summary_1",
        "type": "markdown",
        "content": "# Code Analysis Results\n\n## Structure Overview\n- Total Files: 15\n- React Components: 8\n- Custom Hooks: 4\n\n## Identified Issues\n- ⚠️ Missing type definitions\n- 🔧 Inconsistent import style"
    }]
    yield f'8:{json.dumps(markdown)}\n'
    yield 'e:{"finishReason":"stop","usage":{"promptTokens":50,"completionTokens":80},"isContinued":false}\n'
    await asyncio.sleep(1)
    
    # Final message with text format
    yield '0:"Would you like me to continue with fixing the import style issues next?"\n'
    yield 'e:{"finishReason":"stop","usage":{"promptTokens":20,"completionTokens":30},"isContinued":false}\n'
    yield 'd:{"finishReason":"stop","usage":{"promptTokens":150,"completionTokens":280}}\n'

async def test_stream(request: Request):
    """Test endpoint that generates various types of Vercel stream messages"""
    print("DEBUG: Starting test stream")
    response_generator = generate_test_messages()
    
    return VercelStreamResponse(
        request=request,
        response_generator=response_generator,
    )

# Add this to your FastAPI app routes:
# app.post("/api/test-stream")(test_stream) 