import { useState, useEffect, useRef } from 'react'
import { Product } from '@/types/feed'

const CARD_WIDTH = 272
const CARD_GAP = 16
// const API_URL = 'http://localhost:3000'
const PAGE_SIZE = 20

export function useFeed(chatProducts: Product[] = []) {
  const [products, setProducts] = useState<Product[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [totalItems, setTotalItems] = useState(0)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const isInitialLoad = useRef(true)

  // Update products when chatProducts change
  useEffect(() => {
    setProducts(prev => {
      // Combine chat products with existing feed products
      const feedProducts = prev.filter(p => !chatProducts.find(cp => cp.id === p.id));
      return [...chatProducts, ...feedProducts];
    });
  }, [chatProducts]);

  // Calculate how many items we need to fill the viewport
  const calculateInitialItems = () => {
    if (typeof window === 'undefined') return PAGE_SIZE
    const viewportWidth = window.innerWidth - 32 // subtract padding
    const viewportHeight = window.innerHeight
    const columnsCount = Math.max(1, Math.floor((viewportWidth - CARD_GAP) / (CARD_WIDTH + CARD_GAP)))
    const rowsCount = Math.ceil(viewportHeight / (CARD_WIDTH * 1.5 + CARD_GAP)) // 1.5 is the aspect ratio
    const calculatedSize = columnsCount * (rowsCount + 1) // +1 row to ensure we have enough items to trigger scroll
    
    // Round up to the nearest multiple of PAGE_SIZE to ensure consistent pagination
    return Math.ceil(calculatedSize / PAGE_SIZE) * PAGE_SIZE
  }

  const loadProducts = async (limit: number = PAGE_SIZE, currentOffset: number = 0, isInitial: boolean = false) => {
    if (isLoading) return;
    
    setIsLoading(true)

    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: currentOffset.toString(),
        query_text: ''
      })

      const url = `/api/catalog?${params}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const data = await response.json()
      
      // Transform the data to match our frontend interface
      const transformedItems = data.items.map((item: any) => ({
        id: item.id.toString(),
        tsum_sku: item.tsum_sku,
        vendor_sku: item.vendor_sku,
        name: item.name,
        url: item.url,
        price: item.price,
        old_price: item.old_price,
        vendor: item.vendor,
        picture: item.picture,
        description: item.description,
        available: item.available,
        color: item.color,
        color_shade: item.color_shade,
        design_country: item.design_country,
        gender: item.gender,
        season: item.season,
        material: item.material,
        categories: item.categories,
        has_discount: item.has_discount,
        hash: item.hash,
        discount: item.old_price ? Math.round(((item.old_price - item.price) / item.old_price) * 100) : 0
      }))

      // Only replace items on initial load
      if (isInitial) {
        setProducts(transformedItems)
      } else {
        // Append items for pagination
        setProducts(prev => [...prev, ...transformedItems])
      }
      
      const newTotal = data.total || 1000 // Fallback to 1000 if total is not provided
      if (isInitial || newTotal > totalItems) {
        setTotalItems(newTotal)
      }

      const newOffset = currentOffset + transformedItems.length
      const newHasMore = transformedItems.length > 0 && newOffset < newTotal
      
      setHasMore(newHasMore)
      setOffset(newOffset)
    } catch (error) {
      console.error('Error loading products:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Initial load with calculated number of items
  useEffect(() => {
    if (isInitialLoad.current) {
      const initialItemsCount = calculateInitialItems()
      loadProducts(initialItemsCount, 0, true)
      isInitialLoad.current = false
    }
  }, [])

  const loadMore = () => {
    if (!isLoading && hasMore) {
      loadProducts(PAGE_SIZE, offset, false)
    }
  }

  return {
    products,
    isLoading,
    totalItems,
    hasMore,
    loadMore
  }
} 