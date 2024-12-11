"use client";

import { ChatSection } from '@llamaindex/chat-ui';
import { useChat } from 'ai/react';
import { CustomChatMessages } from '@/components/ui/chat/custom-chat-messages';
import { MultimodalInput } from "@/components/ui/chat/custom-multi-modal-input";
import { useEffect } from 'react';
import type { Product } from "@/types/feed";

interface ChatProps {
  onNewProducts: (products: Product[]) => void;
}

export default function Chat({ onNewProducts }: ChatProps) {
  const handler = useChat();

  useEffect(() => {
    console.log('Chat handler data:', handler.data);
    if (handler.data && Array.isArray(handler.data) && handler.data.length > 0) {
      const firstItem = handler.data.shift();
      console.log('First item:', firstItem);
      if (firstItem && typeof firstItem === 'object' && 'offers' in firstItem) {
        console.log('Found offers:', firstItem.offers);
        onNewProducts(firstItem.offers);
      }
    }
  }, [handler.data, onNewProducts]);

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



