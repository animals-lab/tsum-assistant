'use client'

import { useFeed } from "@/hooks/use-feed"
import { ProductCard } from "./product-card"
import { useEffect, useRef } from "react"
import type { Product } from "@/types/feed"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

const ANIMATION_SETTINGS = {
  initial: { opacity: 0, scale: 0.9 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.9 },
  transition: { duration: 0.3 }
};

interface ProductFeedProps {
  chatProducts: Product[];
  className?: string;
}

export function ProductFeed({ chatProducts, className }: ProductFeedProps) {
  const {
    products,
    isLoading: isFeedLoading,
    loadMore,
    hasMore,
    totalItems
  } = useFeed()

  // Combine all products, with chat products first
  const allProducts = [...chatProducts, ...products]

  const observerTarget = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!observerTarget.current) return;

    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !isFeedLoading) {
          loadMore()
        }
      },
      { 
        threshold: 0,
        rootMargin: '100px'
      }
    )

    observer.observe(observerTarget.current)
    return () => observer.disconnect()
  }, [hasMore, isFeedLoading, loadMore])

  return (
    <div className={cn("w-full space-y-6", className)}>
      {/* Stats bar */}
      <div className="flex justify-between items-center px-4 sm:px-6">
        <div className="text-sm text-gray-600">
          Showing {allProducts.length} of {totalItems + chatProducts.length} items
        </div>
        {chatProducts.length > 0 && (
          <div className="text-sm">
            <span className="text-blue-600">
              {chatProducts.length} items from chat
            </span>
          </div>
        )}
      </div>

      {/* Products grid */}
      <div 
        className="grid gap-4 sm:gap-6 justify-center"
        style={{
          gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 272px))'
        }}
      >
        <AnimatePresence mode="popLayout">
          {allProducts?.map((product) => (
            <motion.div 
              key={product.id}
              {...ANIMATION_SETTINGS}
              layout
            >
              <ProductCard product={product} />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Loading indicator */}
      {hasMore && (
        <div 
          ref={observerTarget}
          className="h-16 flex items-center justify-center"
          aria-hidden={!isFeedLoading}
        >
          {isFeedLoading && (
            <div className="flex flex-col items-center gap-2" role="status">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-[#f8460f] border-t-transparent" />
              <div className="text-sm text-gray-600">Loading more items...</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
} 