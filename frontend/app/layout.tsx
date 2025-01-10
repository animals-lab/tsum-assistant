import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/assets/globals.css";
import CustomerSelector from '@/components/CustomerSelector'
import { CustomerProvider } from '@/contexts/CustomerContext'

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Tsum Chat",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CustomerProvider>
          <CustomerSelector />
          {children}
        </CustomerProvider>
      </body>
    </html>
  );
}
