"use client";

import { ChatSection } from '@llamaindex/chat-ui';
import { useChat } from 'ai/react';
import { CustomChatMessages } from '@/components/ui/chat/custom-chat-messages';
import { MultimodalInput } from "@/components/ui/chat/custom-multi-modal-input";

export default function Chat() {
  const handler = useChat()
  return (
    <ChatSection handler={handler} className="fixed left-4 top-4 bottom-4 flex flex-col w-[600px] bg-white/70 backdrop-blur-md rounded-lg shadow-lg border p-3 z-50">
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



