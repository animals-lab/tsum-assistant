"use client";

import { ChatMessage, ChatMessages, useChatUI } from "@llamaindex/chat-ui";
import { ChatMessageAvatar } from "./chat-avatar";
import { ChatMessageContent } from "./chat-message-content";
import { ChatStarter } from "./chat-starter";

export default function CustomChatMessages() {
  const { messages } = useChatUI();
  return (
    <ChatMessages className="flex-1 flex flex-col overflow-hidden">
      <ChatMessages.List 
        className="flex-1 overflow-y-auto [&::-webkit-scrollbar]:w-1 p-4 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-gray-200 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-2 [&::-webkit-scrollbar-thumb]:border-transparent dark:[&::-webkit-scrollbar-thumb]:bg-gray-700"
      >
        {messages.map((message: any, index: any) => (
          <ChatMessage
            key={index}
            message={message}
            isLast={index === messages.length - 1}
          >
            <ChatMessageAvatar />
            <ChatMessageContent />
          </ChatMessage>
        ))}
        <ChatMessages.Loading />
      </ChatMessages.List>
      <ChatStarter />
    </ChatMessages>
  );
}
