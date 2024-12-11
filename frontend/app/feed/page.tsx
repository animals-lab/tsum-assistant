'use client'

import { useFeed } from "@/components/ui/hooks/use-feed"
import { ProductCard } from "@/components/ui/feed/product-card"
import { useEffect, useRef, useState } from "react"
import Chat from "@/components/chat-llama"
import type { Product } from "@/types/feed"
import { motion, AnimatePresence } from "framer-motion"

export default function Home() {
  const {
    products,
    isLoading: isFeedLoading,
    loadMore,
    hasMore,
    totalItems
  } = useFeed()

  const [streamedProducts, setStreamedProducts] = useState<Product[]>([])
  const [chatProducts, setChatProducts] = useState<Product[]>([])

  // Combine all products, with chat and streamed products first
  const allProducts = [...chatProducts, ...streamedProducts, ...products]

  const [isIntersecting, setIsIntersecting] = useState(false)
  const observerTarget = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        const isIntersecting = entries[0].isIntersecting
        setIsIntersecting(isIntersecting)

        if (isIntersecting && hasMore && !isFeedLoading) {
          loadMore()
        }
      },
      { 
        threshold: 0,
        rootMargin: '200px'
      }
    )

    const currentTarget = observerTarget.current
    if (currentTarget) {
      observer.observe(currentTarget)
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget)
      }
    }
  }, [hasMore, isFeedLoading, loadMore])

  const handleNewChatProducts = (newProducts: Product[]) => {
    console.log('Received new products:', newProducts);
    // Filter out duplicates based on id
    const filteredProducts = newProducts.filter(offer => 
      !chatProducts.some(p => p.id === offer.id) && 
      !streamedProducts.some(p => p.id === offer.id) && 
      !products.some(p => p.id === offer.id)
    )
    console.log('After filtering duplicates:', filteredProducts);
    if (filteredProducts.length > 0) {
      console.log('Adding new products to state');
      setChatProducts(prev => {
        const newState = [...filteredProducts.map(p => ({ ...p, isFromChat: true })), ...prev];
        console.log('New chat products state:', newState);
        return newState;
      });
    }
  }

  return (
    <>
      <main className="min-h-screen p-4 pl-[420px] md:p-6 md:pl-[420px] lg:p-8 lg:pl-[420px]">
        <div className="max-w-[1800px] mx-auto">
          <div className="mb-4 flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Showing {allProducts.length} of {totalItems + streamedProducts.length + chatProducts.length} items
            </div>
            {(streamedProducts.length > 0 || chatProducts.length > 0) && (
              <div className="text-sm">
                {streamedProducts.length > 0 && (
                  <span className="text-green-600 mr-4">
                    {streamedProducts.length} new items received
                  </span>
                )}
                {chatProducts.length > 0 && (
                  <span className="text-blue-600">
                    {chatProducts.length} items from chat
                  </span>
                )}
              </div>
            )}
          </div>
          <div 
            className="grid auto-rows-auto"
            style={{
              gap: '16px',
              gridTemplateColumns: 'repeat(auto-fill, 272px)',
              justifyContent: 'center'
            }}
          >
            <AnimatePresence mode="popLayout">
              {allProducts?.map((product: Product) => (
                <motion.div 
                  key={`${product.id}-${(product as any).isFromChat ? 'chat' : (product as any).isStreamed ? 'streamed' : 'fetched'}`}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.3 }}
                  layout
                >
                  <ProductCard product={product} />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          {hasMore && (
            <div 
              ref={observerTarget}
              className="h-24 mt-4 flex items-center justify-center"
            >
              {isFeedLoading && (
                <div className="flex flex-col items-center gap-2">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                  <div className="text-sm text-gray-600">
                    Loading more items...
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
      <Chat onNewProducts={handleNewChatProducts} />
    </>
  )
}

