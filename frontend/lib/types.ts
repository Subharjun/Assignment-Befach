export type Product = {
  slug: string;
  title: string;
  description: string;
  brand?: string;
  category: string;
  subcategory?: string;
  price: number;
  currency?: string;
  rating: number;
  rating_count: number;
  image_url: string;
  images?: string[];
  tags?: string[];
  stock?: number;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  products?: Product[];
};

export type ChatTurnResponse = {
  session_id: string;
  reply: string;
  products: Product[];
  follow_up?: string | null;
  preferences: Record<string, unknown>;
};
