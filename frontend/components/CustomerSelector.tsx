'use client'

import { useEffect } from 'react'
import { Menu } from '@headlessui/react'
import { UserIcon } from '@heroicons/react/24/outline'
import { useCustomer } from '@/contexts/CustomerContext'

const customers = [
  { id: 1, name: 'Виктор Иванович' },
  { id: 2, name: 'Леночка' }
]

export default function CustomerSelector() {
  const { customer, setCustomer } = useCustomer()

  const handleCustomerSelect = (newCustomer: typeof customers[0]) => {
    setCustomer(newCustomer)
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      <Menu as="div" className="relative">
        <Menu.Button className="flex items-center gap-2 rounded-full bg-white px-4 py-2 shadow-md hover:bg-gray-50">
          <UserIcon className="h-5 w-5" />
          <span>{customer.name}</span>
        </Menu.Button>
        
        <Menu.Items className="absolute right-0 mt-2 w-48 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
          <div className="py-1">
            {customers.map((customerOption) => (
              <Menu.Item key={customerOption.id}>
                {({ active }) => (
                  <button
                    onClick={() => handleCustomerSelect(customerOption)}
                    className={`${
                      active ? 'bg-gray-100' : ''
                    } block w-full px-4 py-2 text-left text-sm ${
                      customerOption.id === customer.id ? 'bg-gray-50' : ''
                    }`}
                  >
                    {customerOption.name}
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>
        </Menu.Items>
      </Menu>
    </div>
  )
} 