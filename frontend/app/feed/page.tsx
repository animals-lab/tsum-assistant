'use client'

import { useFeed } from "@/components/ui/hooks/use-feed"
import { ProductCard } from "@/components/ui/feed/product-card"
import { useEffect, useRef, useState } from "react"
import Chat from "@/components/chat-llama"
import type { Product } from "@/types/feed"

export default function Home() {
  const {
    products,
    isLoading: isFeedLoading,
    loadMore,
    hasMore,
    totalItems
  } = useFeed()

  const [streamedProducts, setStreamedProducts] = useState<Product[]>([])

  const allProducts = [...streamedProducts, ...products]

  const [isIntersecting, setIsIntersecting] = useState(false)
  const observerTarget = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const eventSource = new EventSource('http://localhost:8000/api/product-stream')

    eventSource.addEventListener('product', (event) => {
      try {
        const product = JSON.parse(event.data) as Product
        setStreamedProducts(prev => [{...product, isStreamed: true}, ...prev])
      } catch (error) {
        console.error('Error parsing product data:', error)
      }
    })

    eventSource.addEventListener('error', (event: Event) => {
      console.error('Stream error:', event)
    })

    return () => {
      eventSource.close()
    }
  }, [])

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

  return (
    <>
      <main className="min-h-screen p-4 pl-[420px] md:p-6 md:pl-[420px] lg:p-8 lg:pl-[420px]">
        <div className="max-w-[1800px] mx-auto">
          <div className="mb-4 flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Showing {allProducts.length} of {totalItems + streamedProducts.length} items
            </div>
            {streamedProducts.length > 0 && (
              <div className="text-sm text-green-600">
                {streamedProducts.length} new items received
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
            {allProducts?.map((product: Product) => (
              <div key={`${product.id}-${(product as any).isStreamed ? 'streamed' : 'fetched'}`}>
                <ProductCard product={product} />
              </div>
            ))}
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
      <Chat />
    </>
  )
}

