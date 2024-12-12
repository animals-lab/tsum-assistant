'use client'

import { useState, useCallback } from "react"
import Chat from "@/components/chat/chat-llama"
import { ProductFeed } from "@/components/feed/product-feed"
import type { Product } from "@/types/feed"

export default function Page() {
  const [chatProducts, setChatProducts] = useState<Product[]>([])

  const handleNewChatProducts = useCallback((newProducts: Product[]) => {
    setChatProducts(prev => {
      const newState = [...prev];
      
      newProducts.forEach(product => {
        // Remove if exists in current list
        const existingIndex = newState.findIndex(p => p.id === product.id);
        if (existingIndex !== -1) {
          newState.splice(existingIndex, 1);
        }
        // Add to top
        newState.unshift(product);
      });
      
      return newState;
    });
  }, []);

  return (
    <div className="flex w-full min-h-screen bg-white">
      <Chat 
        variant="sidebar"
        onNewProducts={handleNewChatProducts} 
      />
      <main className="flex-1 min-h-screen p-4 pl-[532px] md:p-6 md:pl-[532px] lg:p-8 lg:pl-[532px]">
        <div className="max-w-[1800px] mx-auto">
          <ProductFeed chatProducts={chatProducts} />
        </div>
      </main>
    </div>
  )
}

