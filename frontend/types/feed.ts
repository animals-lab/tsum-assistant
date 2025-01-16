export interface Product {
  id: string;
  tsum_sku: string;
  vendor_sku: string;
  name: string;
  url: string;
  price: number;
  old_price?: number;
  vendor: string;
  picture: string;
  description: string;
  available: boolean;
  color?: string;
  color_shade?: string;
  design_country?: string;
  gender?: string;
  season?: string;
  material?: string;
  categories?: string[];
  has_discount: boolean;
  hash?: string | null;
}

export interface FeedResponse {
  items: Product[];
  totalItems: number;
}

export interface FilterState {
  brand?: string[];
  color?: string[];
  material?: string[];
  size?: string[];
  season?: string[];
  priceRange?: [number, number];
} 