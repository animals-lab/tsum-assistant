'use client'

import { useFeed } from "@/hooks/use-feed"
import { ProductCard } from "./product-card"
import { useEffect, useRef } from "react"
import type { Product } from "@/types/feed"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { useCustomer } from '@/contexts/CustomerContext'

const ANIMATION_SETTINGS = {
  initial: { opacity: 0, scale: 0 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.9 },
  transition: { duration: 0.3 }
};

interface ProductFeedProps {
  chatProducts: Product[];
  className?: string;
}

export function ProductFeed({ chatProducts, className }: ProductFeedProps) {
  const { customer } = useCustomer()
  const { products, isLoading, totalItems, hasMore, loadMore } = useFeed(chatProducts)

  // Reload feed when customer changes
  useEffect(() => {
    if (customer?.id) {
      // Add your logic here to fetch new products based on customer.id
    }
  }, [customer?.id])

  return (
    <div className={cn("grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4", className)}>
      <AnimatePresence>
        {products.map((product, index) => (
          <motion.div
            key={`${product.id}-${index}`}
            {...ANIMATION_SETTINGS}
          >
            <ProductCard product={product} />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
} 