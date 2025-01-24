import { Product } from "@/types/feed"
import { Badge } from "./ui/badge"
import Image from "next/image"
import * as AspectRatioPrimitive from "@radix-ui/react-aspect-ratio"

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const discount = product.old_price 
    ? Math.round(((product.old_price - product.price) / product.old_price) * 100)
    : 0;

  return (
    <a 
      href={product.url} 
      target="_blank" 
      rel="noopener noreferrer" 
      className="block"
    >
      <div className="w-[272px] group relative rounded-xl overflow-hidden">
        <AspectRatioPrimitive.Root ratio={3/4}>
          <img
            src={product.picture}
            alt={product.name}
            // fill
            className="object-cover rounded-xl"
            sizes="272px"
            // priority={false}
          />
        </AspectRatioPrimitive.Root>
        
        {/* Discount badge */}
        {product.has_discount && (
          <Badge 
            className="absolute top-2 right-2 bg-red-300 z-10"
            variant="secondary"
          >
            -{discount}%
          </Badge>
        )}
        
        {/* Hover overlay with all information */}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          {/* TSUM logo badge */}
          <div className="absolute top-4 left-4 w-12 h-8 bg-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <img
              src="https://www.tsum.ru/static/media/logo.5e134.svg"
              alt="TSUM"
              // fill
              className="object-contain"
            />
          </div>

          <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
            <h3 className="font-semibold text-sm truncate">{product.vendor}</h3>
            <p className="text-sm truncate">{product.name}</p>
            <div className="flex items-center justify-between mt-2">
              <div className="flex flex-col">
                <span className="font-semibold">
                  {product.price} ₽
                </span>
                {product.old_price && (
                  <span className="text-sm line-through opacity-75">
                    {product.old_price} ₽
                  </span>
                )}
              </div>
              {!product.available && (
                <Badge variant="secondary" className="bg-white/20">
                  Out of Stock
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>
    </a>
  )
} 