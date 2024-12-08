# Agent Communication and Streaming Architecture

## Overview
This document details how the agent workflow communicates and streams messages/tool calls from backend to frontend in the my-app project. It covers both the Vercel AI SDK streaming protocol and the specific implementation in this project.

## Project-Specific Implementation

### 1. Core Components

#### A. Backend Components
- **Function Calling Agent** (`app/workflows/function_calling_agent.py`)
  - Main workflow class handling agent operations
  - Key steps:
    1. `prepare_chat_history`: Sets up chat context and initial user input
    2. `handle_llm_input`: Processes input through LLM and determines tool calls
    3. `handle_tool_calls`: Executes tools and processes responses

- **Tool Handling** (`app/workflows/tools.py`)
  - `ChatWithToolsResponse`: Encapsulates tool call responses
  - `chat_with_tools`: Manages tool call streaming
  - `call_tools`: Executes tool calls and emits events
  - Tool call types:
    - Single tool calls
    - Parallel tool calls
    - Context-aware tool calls

- **Event System** (`app/workflows/events.py`)
  - Event Types:
    1. `AgentRunEventType.TEXT`: Regular text messages
    2. `AgentRunEventType.PROGRESS`: Progress updates
  - `AgentRunEvent`: Main event class for agent communications
    - Properties: name, message, event_type, data
    - Converts to frontend-compatible response format

#### B. Frontend Components
- Uses `@llamaindex/chat-ui` library
- Key Components:
  - `ChatSection`: Parent component that sets up chat handler
  - `CustomChatMessages`: Displays chat messages
  - `CustomChatInput`: Handles user input
- State Management:
  - Uses Vercel's `useChat` hook for managing chat state
  - Uses `useChatMessage` for handling individual messages

### 2. Communication Flow

#### A. Message Flow
1. User sends message to frontend
2. Frontend makes POST request to `/api/chat` endpoint
3. Backend initiates workflow
4. Agent processes message through LLM
5. Tool calls executed if needed
6. Responses streamed back to frontend
7. UI updates dynamically with streamed content

#### B. Tool Call Flow
1. Agent determines tool need
2. Tool call initiated with unique ID
3. Arguments streamed as deltas
4. Tool execution with progress tracking
5. Results streamed back
6. UI updates with tool progress and results

## Vercel AI SDK Stream Protocol

### 1. Protocol Types

#### A. Text Stream Protocol
- Simple protocol for streaming plain text
- Each chunk appended to form full response
- Used with `useChat` and `useCompletion`
- Requires `streamProtocol: 'text'` setting
- Format: Plain text chunks that are concatenated

#### B. Data Stream Protocol
- Advanced protocol for complex data streaming
- Requires `x-vercel-ai-data-stream: v1` header
- Default protocol for `useChat` and `useCompletion`
- Format: `TYPE_ID:CONTENT_JSON\n`

### 2. Stream Part Types

#### A. Basic Parts
- Text Part (`0:`)
  - Format: `0:"example"\n`
  - Used for text content chunks
  - Content is JSON-escaped to handle special characters

- Data Part (`2:`)
  - Format: `2:[{"key":"value"}]\n`
  - Used for JSON data arrays
  - Supports complex data structures

- Error Part (`3:`)
  - Format: `3:"error message"\n`
  - Used for error messages
  - Includes stack traces and error details

#### B. Message Parts
- Message Annotation (`8:`)
  - Format: `8:{"id":"message-123","other":"annotation"}\n`
  - Used for message metadata
  - Can include source references, timestamps, etc.

#### C. Tool-Related Parts
- Tool Call Start (`b:`)
  - Format: `b:{"toolCallId":"id","toolName":"name"}\n`
  - Indicates start of streaming tool call
  - Must be sent before any tool call deltas

- Tool Call Delta (`c:`)
  - Format: `c:{"toolCallId":"id","argsTextDelta":"delta"}\n`
  - Streams tool call argument updates
  - Used for real-time argument construction

- Tool Call (`9:`)
  - Format: `9:{"toolCallId":"id","toolName":"name","args":{}}\n`
  - Complete tool call information
  - Sent after streaming is finished

- Tool Result (`a:`)
  - Format: `a:{"toolCallId":"id","result":"output"}\n`
  - Tool execution results
  - Includes any return values or errors

#### D. Completion Parts
- Finish Step (`e:`)
  - Format: `e:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20},"isContinued":false}\n`
  - Indicates completion of one step
  - Includes token usage and continuation status

- Finish Message (`d:`)
  - Format: `d:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20}}\n`
  - Indicates final completion
  - Must be the last part in the stream

## Project Implementation Details

### 1. Backend Implementation

#### A. VercelStreamResponse Class
- Extends FastAPI's StreamingResponse
- Headers:
  ```python
  {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "Content-Encoding": "none",
    "Transfer-Encoding": "chunked",
    "x-vercel-ai-data-stream": "v1"
  }
  ```
- Key Methods:
  - `content_generator`: Main streaming loop
  - `_create_stream`: Combines text and event streams
  - `convert_text/data/error`: Format messages for frontend

#### B. Stream Generation Process
1. Initialize stream with request and chat data
2. Create merged stream of text and events
3. Handle stream start with blank message
4. Process text tokens and events
5. Handle cancellation and cleanup
6. Generate suggested questions if configured

### 2. Error Handling and Recovery

#### A. Stream Error Types
1. Cancellation (`asyncio.CancelledError`)
2. General exceptions
3. Tool execution errors
4. Connection errors

#### B. Error Recovery Process
1. Log error details
2. Send error message to client
3. Clean up resources
4. Cancel running workflows
5. Maintain session state

### 3. Frontend Integration

#### A. Chat UI Components
1. Configure stream protocol (default: 'data')
2. Handle streaming states:
   - Loading: Initial request
   - Streaming: Receiving chunks
   - Tool Execution: Processing tools
   - Complete: Final response
   - Error: Handle failures

#### B. Message Processing
1. Parse stream chunks by type
2. Update UI based on chunk type:
   - Text: Append to message
   - Tool Calls: Show progress
   - Errors: Display error UI
3. Handle suggested questions
4. Maintain chat history

### 4. Performance Optimizations

#### A. Stream Management with aiostream
1. **aiostream Overview**
   - Python library for asynchronous stream operations
   - Provides tools for combining and manipulating async streams
   - Used in the project to merge multiple async generators

2. **Key aiostream Features Used**
   - `stream.merge`: Combines multiple async streams into a single stream
     ```python
     # Example from the project
     combine = stream.merge(
         _chat_response_generator(),  # Text stream
         _event_generator()           # Event stream
     )
     ```
   - Concurrent processing of:
     - Text responses from LLM
     - Tool call events
     - Progress updates
     - Suggested questions

3. **Benefits in the Project**
   - Efficient parallel stream processing
   - Non-blocking stream operations
   - Proper backpressure handling
   - Automatic resource cleanup
   - Ordered message delivery

4. **Stream Handling**
   - Manages two main streams:
     1. Chat response stream (text content)
     2. Event stream (tool calls, progress)
   - Ensures proper ordering of messages
   - Handles stream cancellation gracefully
   - Maintains stream state

#### B. Memory Management
1. Stream cleanup on disconnection
2. Session state cleanup
3. Tool resource management
4. Cache management for long sessions