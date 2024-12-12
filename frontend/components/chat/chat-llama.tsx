"use client";

import { ChatSection } from '@llamaindex/chat-ui';
import { useChat } from 'ai/react';
import { CustomChatMessages } from '@/components/chat/custom/custom-chat-messages';
import { MultimodalInput } from "@/components/chat/ui/multi-modal-input";
import { useEffect } from 'react';
import type { Product } from "@/types/feed";
import { cn } from "@/lib/utils";

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
  const handler = useChat();

  useEffect(() => {
    if (!onNewProducts) return;
    
    console.log('Chat handler data:', handler.data);
    if (handler.data && Array.isArray(handler.data) && handler.data.length > 0) {
      const firstItem = handler.data.shift();
      console.log('First item:', firstItem);
      if (firstItem && typeof firstItem === 'object' && 'offers' in firstItem) {
        console.log('Found offers:', firstItem.offers);
        onNewProducts(firstItem.offers as Product[]);
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



