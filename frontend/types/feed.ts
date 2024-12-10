export interface Product {
  id: string;
  name: string;
  url: string;
  price: string;
  oldprice?: string;
  currencyId: string;
  picture: string;
  brand: string;
  description: string;
  available: boolean;
  color?: string;
  material?: string;
  season?: string;
  params?: {
    design_country?: string;
    gender?: string;
    category?: string;
  };
  categoryId?: string;
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