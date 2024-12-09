"use client";

import { PreviewMessage, ThinkingMessage } from "@/components/message";
import { MultimodalInput } from "@/components/multimodal-input";
import { Overview } from "@/components/overview";
import { useScrollToBottom } from "@/hooks/use-scroll-to-bottom";
import { Message } from "ai";
import { useChat } from "ai/react";
import { ChatSection, ChatMessages as CustomChatMessages, ChatInput as CustomChatInput } from '@llamaindex/chat-ui'

const ChatUI = () => {
  const handler = useChat({ api: "/api/chat" })
  return (
    <ChatSection handler={handler} className="w-full h-full">
      <CustomChatMessages />
      <CustomChatInput />
    </ChatSection>
  )
}

export function Chat() {
  return <ChatUI />
}


// Internal component that handles the chat UI
// Dependencies:
// - PreviewMessage: Renders individual messages with support for markdown, code blocks, and tool calls
// - ThinkingMessage: Shows loading state while AI is responding
// - MultimodalInput: Handles user input, file attachments, and message submission
// - Overview: Displays initial state when no messages exist
// function ChatUI() {
//   // Static chat ID used by:
//   // - PreviewMessage for message identification
//   // - MultimodalInput for attachment handling
//   const chatId = "001";

//   // Vercel AI SDK chat hook
//   // Used by:
//   // - PreviewMessage: messages for rendering
//   // - MultimodalInput: input, setInput for text control
//   // - ThinkingMessage: isLoading for loading state
//   const {
//     messages,
//     setMessages,
//     handleSubmit,
//     input,
//     setInput,
//     append,
//     isLoading,
//     stop,
//   } = useChat({
//     api: "/api/chat", // Endpoint that implements Vercel AI SDK stream protocol
//   });

//   // Custom hook for auto-scrolling to bottom of chat
//   // Used by:
//   // - Messages container ref
//   // - Scroll anchor div
//   const [messagesContainerRef, messagesEndRef] = useScrollToBottom<HTMLDivElement>();

//   return (
//     // Main chat container with styling
//     <div className="flex flex-col min-w-0 w-[90dvw] max-w-3xl h-[80dvh] mx-auto my-[10dvh] bg-background rounded-lg shadow-lg border">
//       {/* Messages container with scroll behavior
//           Dependencies:
//           - messagesContainerRef: Used by useScrollToBottom for scroll management
//           - Styling includes custom scrollbar design */}
//       <div
//         ref={messagesContainerRef}
//         className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll p-10 py-20 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-muted-foreground/20 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent"
//       >
//         {/* Overview component shown when no messages exist */}
//         {messages.length === 0 && <Overview />}

//         {/* Message list
//             Maps through messages array and renders PreviewMessage component
//             Dependencies:
//             - PreviewMessage expects: chatId, message object, and loading state
//             - Loading state is calculated based on message index */}
//         {messages.map((message: Message, index: number) => (
//           <PreviewMessage
//             key={message.id}
//             chatId={chatId}
//             message={message}
//             isLoading={isLoading && index === messages.length - 1}
//           />
//         ))}

//         {/* Thinking indicator shown when:
//             - System is loading
//             - Messages exist
//             - Last message was from user */}
//         {isLoading &&
//           messages.length > 0 &&
//           messages[messages.length - 1].role === "user" && <ThinkingMessage />}

//         {/* Scroll anchor for useScrollToBottom
//             Used to determine scroll position */}
//         <div ref={messagesEndRef} className="shrink-0 min-w-[24px] min-h-[24px]" />
//       </div>

//       {/* Input form
//           Dependencies:
//           - MultimodalInput requires all chat hook properties
//           - Handles file attachments and message submission */}
//       <form className="flex p-4 bg-background/95 rounded-b-lg">
//         <MultimodalInput
//           chatId={chatId}
//           input={input}
//           setInput={setInput}
//           handleSubmit={handleSubmit}
//           isLoading={isLoading}
//           stop={stop}
//           messages={messages}
//           setMessages={setMessages}
//           append={append}
//         />
//       </form>
//     </div>
//   );
// }

// Main exported component
// Renders the ChatUI component directly
// export function Chat() {
//   return <ChatUI />;
// }
