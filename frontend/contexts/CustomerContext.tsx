'use client'

import { createContext, useContext, useState } from 'react'
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
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null
    return null
  }

  // Get initial customer from cookie or default to first customer
  const customerId = getCookie('customerId')
  const initialCustomer = customerId 
    ? customers.find(c => c.id === parseInt(customerId)) ?? customers[0]
    : customers[0]

  const [customer, setCustomer] = useState<Customer>(initialCustomer)

  const handleSetCustomer = (newCustomer: Customer) => {
    setCustomer(newCustomer)
    document.cookie = `customerId=${newCustomer.id};path=/;max-age=${60 * 60 * 24 * 30}`
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