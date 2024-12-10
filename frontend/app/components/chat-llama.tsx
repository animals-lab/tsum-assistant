"use client";

import { ChatSection } from '@llamaindex/chat-ui';
import { useChat } from 'ai/react';
import { CustomChatMessages } from './ui/chat/custom-chat-messages';
import { MultimodalInput } from "@/app/components/ui/chat/custom-multi-modal-input";

export default function ChatExample() {
  const handler = useChat()
  return (
    <ChatSection handler={handler} className="flex flex-col min-w-0 w-[90dvw] max-w-3xl h-[80dvh] mx-auto my-[10dvh] bg-background rounded-lg shadow-lg border p-10">
      <CustomChatMessages />
      <MultimodalInput
        className='' 
        chatId="chat"
        input={handler.input}
        setInput={handler.setInput}
        isLoading={handler.isLoading}
        stop={handler.stop}
        messages={handler.messages}
        setMessages={handler.setMessages}
        append={handler.append}
        handleSubmit={handler.handleSubmit}
      />
    </ChatSection>
  )
}



