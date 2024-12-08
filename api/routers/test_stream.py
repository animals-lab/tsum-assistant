from fastapi import FastAPI, Request
from typing import AsyncGenerator
from .vercel import VercelStreamResponse
import asyncio
import json

async def generate_test_messages() -> AsyncGenerator[str, None]:
    """Generate test messages in various Vercel Stream Protocol formats"""
    
    # Initial response with proper message format as array
    yield '2:[{"messages":[{"role":"assistant","content":"Let me analyze your code and suggest some improvements. First, I\'ll check the code structure."}]}]\n'
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
    
    # Explain the first issue with proper message format as array
    yield '2:[{"messages":[{"role":"assistant","content":"Let me show you an example of the type definition issue I found. Here\'s a problematic code snippet:"}]}]\n'
    
    # Code block showing the issue
    code_block = [{
        "id": "code_1",
        "type": "code",
        "language": "typescript",
        "code": "function processData(data) {  // Missing type annotation\n  const results = [];\n  \n  data.forEach(item => {\n    results.push({\n      id: item.id,\n      value: item.value * 2\n    });\n  });\n  \n  return results;\n}"
    }]
    yield f'8:{json.dumps(code_block)}\n'
    yield 'e:{"finishReason":"stop","usage":{"promptTokens":30,"completionTokens":50},"isContinued":false}\n'
    await asyncio.sleep(1)
    
    # Suggest fix with proper message format as array
    yield '2:[{"messages":[{"role":"assistant","content":"I\'ll suggest a type-safe version of this code."}]}]\n'
    tool_call2 = {
        "toolCallId": "fix_1",
        "toolName": "suggest_type_fix",
        "args": {
            "function_name": "processData",
            "parameters": ["data"],
            "return_type": "array"
        }
    }
    yield f'9:{json.dumps(tool_call2)}\n'
    await asyncio.sleep(2)
    
    # Tool result with fixed code
    tool_result2 = {
        "toolCallId": "fix_1",
        "result": {
            "fixed_code": "interface DataItem {\n  id: string;\n  value: number;\n}\n\ninterface ProcessedItem {\n  id: string;\n  value: number;\n}\n\nfunction processData(data: DataItem[]): ProcessedItem[] {\n  return data.map(item => ({\n    id: item.id,\n    value: item.value * 2\n  }));\n}"
        }
    }
    yield f'a:{json.dumps(tool_result2)}\n'
    await asyncio.sleep(1)
    
    # Explain improvements with proper message format as array
    yield '2:[{"messages":[{"role":"assistant","content":"Here\'s the improved version with proper TypeScript types. I made several enhancements:"}]}]\n'
    await asyncio.sleep(1)
    
    # List improvements with markdown
    improvements = [{
        "id": "improvements_1",
        "type": "markdown",
        "content": "1. Added `DataItem` interface for input type\n2. Added `ProcessedItem` interface for output type\n3. Added proper type annotations to the function\n4. Replaced `forEach` with `map` for better functional style\n\nThe code is now:\n- ✅ Type-safe\n- 🔄 More functional\n- 📝 Self-documenting\n- 🐛 Easier to debug"
    }]
    yield f'8:{json.dumps(improvements)}\n'
    yield 'e:{"finishReason":"stop","usage":{"promptTokens":40,"completionTokens":70},"isContinued":false}\n'
    await asyncio.sleep(1)
    
    # Final message with proper message format as array
    yield '2:[{"messages":[{"role":"assistant","content":"Would you like me to continue with fixing the import style issues next?"}]}]\n'
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