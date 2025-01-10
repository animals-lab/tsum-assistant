'use client'

import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'

const customers = [
  { id: 1, name: 'Виктор Иванович' },
  { id: 2, name: 'Леночка' }
]

type Customer = typeof customers[0]

interface CustomerContextType {
  customer: Customer
  setCustomer: (customer: Customer) => void
}

const CustomerContext = createContext<CustomerContextType | undefined>(undefined)

export function CustomerProvider({ children }: { children: ReactNode }) {
  const getCookie = (name: string): string | null => {
    if (typeof document === 'undefined') return null
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null
    return null
  }

  const [customer, setCustomer] = useState<Customer>(customers[0])

  // Initialize customer from cookie after component mounts
  useEffect(() => {
    const customerId = getCookie('customerId')
    if (customerId) {
      const savedCustomer = customers.find(c => c.id === parseInt(customerId))
      if (savedCustomer) {
        setCustomer(savedCustomer)
      }
    }
  }, [])

  const handleSetCustomer = (newCustomer: Customer) => {
    setCustomer(newCustomer)
    document.cookie = `customerId=${newCustomer.id};path=/;max-age=${60 * 60 * 24 * 30};SameSite=Lax`
    setTimeout(() => {
      window.location.reload()
    }, 100)
  }

  return (
    <CustomerContext.Provider value={{ customer, setCustomer: handleSetCustomer }}>
      {children}
    </CustomerContext.Provider>
  )
}

export function useCustomer() {
  const context = useContext(CustomerContext)
  if (context === undefined) {
    throw new Error('useCustomer must be used within a CustomerProvider')
  }
  return context
} 