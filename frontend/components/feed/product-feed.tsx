'use client'

import { useFeed } from "@/hooks/use-feed"
import { ProductCard } from "./product-card"
import { useEffect, useRef, useState } from "react"
import type { Product } from "@/types/feed"
import { motion, AnimatePresence } from "framer-motion"

interface ProductFeedProps {
  chatProducts: Product[];
}

export function ProductFeed({ chatProducts }: ProductFeedProps) {
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
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !isFeedLoading) {
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
    <div className="w-full">
      <div className="mb-4 flex justify-between items-center">
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
      <div 
        className="grid auto-rows-auto"
        style={{
          gap: '16px',
          gridTemplateColumns: 'repeat(auto-fill, 272px)',
          justifyContent: 'center'
        }}
      >
        <AnimatePresence mode="popLayout">
          {allProducts?.map((product, index) => (
            <motion.div 
              key={`${product.id}-${index}`}
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
  )
} 