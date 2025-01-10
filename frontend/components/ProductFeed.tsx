'use client'

import { useCustomer } from '@/contexts/CustomerContext'
import { useEffect, useState } from 'react'

export default function ProductFeed({ chatProducts }) {
  const { customer } = useCustomer()
  const [products, setProducts] = useState(chatProducts)

  // Reload products when customer changes
  useEffect(() => {
    // Add your logic here to fetch new products based on customer.id
    fetchProducts(customer.id).then(setProducts)
  }, [customer.id])

  return (
    // Your existing render logic using 'products' instead of 'chatProducts'
  )
} 