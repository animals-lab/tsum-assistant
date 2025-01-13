"use client";

import { ChatSection } from '@llamaindex/chat-ui';
import { useChat } from 'ai/react';
import { CustomChatMessages } from '@/components/chat/custom/custom-chat-messages';
import { MultimodalInput } from "@/components/chat/ui/multi-modal-input";
import { useEffect } from 'react';
import type { Product } from "@/types/feed";
import { cn } from "@/lib/utils";

interface ChatMessage {
  offers?: Product[];
  [key: string]: any;
}

interface ChatProps {
  onNewProducts?: (products: Product[]) => void;
  className?: string;
  variant?: 'standalone' | 'sidebar';
}

export default function Chat({ 
  onNewProducts, 
  className,
  variant = 'standalone' 
}: ChatProps) {
  const handler = useChat<ChatMessage>();

  useEffect(() => {
    if (!onNewProducts) return;
    
    if (handler.data && Array.isArray(handler.data) && handler.data.length > 0) {
      // Look for the most recent message with offers
      const messageWithOffers = [...handler.data].reverse().find(item => 
        item && typeof item === 'object' && 'offers' in item
      );
      
      if (messageWithOffers?.offers && Array.isArray(messageWithOffers.offers)) {
        onNewProducts(messageWithOffers.offers);
      }
    }
  }, [handler.data, onNewProducts]);

  const defaultStyles = {
    standalone: "fixed inset-4 md:inset-10 max-w-3xl mx-auto flex flex-col bg-white/70 backdrop-blur-md rounded-lg shadow-lg border p-4 z-50",
    sidebar: "fixed left-4 top-4 bottom-4 flex flex-col w-[600px] bg-white/70 backdrop-blur-md rounded-lg shadow-lg border p-3 z-50"
  };

  return (
    <ChatSection 
      handler={handler} 
      className={cn(defaultStyles[variant], className)}
    >
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



