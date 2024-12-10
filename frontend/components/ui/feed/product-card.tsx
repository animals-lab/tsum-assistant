import { Product } from "@/types/feed"
import { AspectRatio } from "@/components/ui/aspect-ratio"
import { Badge } from "@/components/ui/badge"
import Image from "next/image"

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const discount = product.oldprice 
    ? Math.round(((parseFloat(product.oldprice) - parseFloat(product.price)) / parseFloat(product.oldprice)) * 100)
    : 0;

  return (
    <div className="w-[272px] group relative rounded-xl overflow-hidden">
      <AspectRatio ratio={3/4}>
        <Image
          src={product.picture}
          alt={product.name}
          fill
          className="object-cover rounded-xl"
          sizes="272px"
          priority={false}
        />
      </AspectRatio>
      
      {/* Hover overlay with all information */}
      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        {/* Discount badge - now part of the hover overlay */}
        {discount > 0 && (
          <Badge 
            className="absolute top-2 right-2 bg-red-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            variant="secondary"
          >
            -{discount}%
          </Badge>
        )}
        
        <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
          <h3 className="font-semibold text-sm truncate">{product.brand}</h3>
          <p className="text-sm truncate">{product.name}</p>
          <div className="flex items-center justify-between mt-2">
            <div className="flex flex-col">
              <span className="font-semibold">
                {product.price} {product.currencyId}
              </span>
              {product.oldprice && (
                <span className="text-sm line-through opacity-75">
                  {product.oldprice} {product.currencyId}
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
  )
} 