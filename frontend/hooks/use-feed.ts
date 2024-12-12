import { useState, useEffect, useRef } from 'react'
import { Product, FeedResponse, FilterState } from '@/types/feed'

const CARD_WIDTH = 272
const CARD_GAP = 16
const API_URL = 'http://127.0.0.1:8000'
const PAGE_SIZE = 20

export function useFeed() {
  const [products, setProducts] = useState<Product[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [filters, setFilters] = useState<FilterState>({})
  const [totalItems, setTotalItems] = useState(0)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const loadingRef = useRef(false)
  const isInitialLoad = useRef(true)

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
    if (loadingRef.current) {
      console.log('Loading in progress, skipping request')
      return
    }
    
    console.log('Loading products:', { 
      limit, 
      currentOffset, 
      isInitial, 
      hasMore,
      currentProductsCount: products.length,
      stateOffset: offset
    })

    loadingRef.current = true
    setIsLoading(true)

    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: currentOffset.toString(),
        query_text: ''
      })

      const url = `${API_URL}/api/catalog?${params}`
      console.log('Fetching URL:', url)

      const response = await fetch(url)

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const data = await response.json()
      console.log('API Response:', {
        itemsReceived: data.items.length,
        total: data.total,
        requestedOffset: currentOffset,
        requestedLimit: limit,
        firstItemId: data.items[0]?.id,
        lastItemId: data.items[data.items.length - 1]?.id
      })
      
      // Transform the data to match our frontend interface
      const transformedItems = data.items.map((item: any) => ({
        id: item.id.toString(),
        name: item.name,
        url: item.url,
        price: item.price.toString(),
        currencyId: 'RUB',
        picture: item.picture,
        brand: item.vendor,
        description: item.description,
        available: item.available,
        color: item.color,
        material: item.material,
        season: item.season,
        params: {
          design_country: item.design_country,
          gender: item.gender,
          category: item.category
        },
        categoryId: item.category_id?.toString()
      }))

      // Only replace items on initial load or filter change
      if (isInitial) {
        setProducts(transformedItems)
      } else {
        // Append items for pagination
        setProducts(prev => {
          console.log('Updating products:', {
            previousCount: prev.length,
            newItemsCount: transformedItems.length,
            totalAfterUpdate: prev.length + transformedItems.length,
            firstNewId: transformedItems[0]?.id,
            lastNewId: transformedItems[transformedItems.length - 1]?.id
          })
          return [...prev, ...transformedItems]
        })
      }
      
      const newTotal = data.total || 1000 // Fallback to 1000 if total is not provided
      if (isInitial || newTotal > totalItems) {
        setTotalItems(newTotal)
      }

      const newOffset = currentOffset + transformedItems.length
      const newHasMore = transformedItems.length > 0 && newOffset < newTotal
      
      console.log('Pagination update:', {
        currentOffset,
        newOffset,
        newTotal,
        receivedItems: transformedItems.length,
        newHasMore,
        currentStateOffset: offset
      })

      setHasMore(newHasMore)
      setOffset(newOffset)
    } catch (error) {
      console.error('Error loading products:', error)
    } finally {
      setIsLoading(false)
      loadingRef.current = false
    }
  }

  // Initial load with calculated number of items
  useEffect(() => {
    if (isInitialLoad.current) {
      console.log('Initial load')
      const initialItemsCount = calculateInitialItems()
      loadProducts(initialItemsCount, 0, true)
      isInitialLoad.current = false
    }
  }, [])

  // Regular filters update
  useEffect(() => {
    if (!isInitialLoad.current) {
      console.log('Filters updated, reloading')
      const initialItemsCount = calculateInitialItems()
      setOffset(0)
      loadProducts(initialItemsCount, 0, true)
    }
  }, [filters])

  const loadMore = () => {
    console.log('loadMore called:', { 
      isLoading, 
      hasMore, 
      currentOffset: offset, 
      totalItems,
      currentProductsCount: products.length
    })
    if (!isLoading && hasMore && !loadingRef.current) {
      loadProducts(PAGE_SIZE, offset, false)
    }
  }

  const updateFilters = (newFilters: FilterState) => {
    setFilters(newFilters)
    setOffset(0)
  }

  return {
    products,
    isLoading,
    filters,
    totalItems,
    hasMore,
    updateFilters,
    loadMore
  }
} 