import type { ChatTurnResponse, Product } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  listProducts: (category?: string, page = 1, pageSize = 20, sort = "rating") =>
    request<{ items: Product[]; total: number; page: number; page_size: number }>(
      `/products?${new URLSearchParams({
        ...(category ? { category } : {}),
        page: String(page),
        page_size: String(pageSize),
        sort,
      })}`
    ),

  listCategories: () => request<string[]>(`/products/categories`),

  getProduct: (slug: string) => request<Product>(`/products/${slug}`),

  semanticSearch: (q: string, top_k = 12) =>
    request<Product[]>(`/search`, { method: "POST", body: JSON.stringify({ q, top_k }) }),

  suggest: (q: string, k = 6) =>
    request<{ slug: string; title: string; image_url: string; price: number; category: string }[]>(
      `/search/suggest?q=${encodeURIComponent(q)}&k=${k}`
    ),

  related: (slug: string, k = 8) =>
    request<Product[]>(`/recommendations/related/${slug}?k=${k}`),

  forYou: (k = 12, token?: string) =>
    request<Product[]>(`/recommendations/for-you?k=${k}`, {}, token),

  chat: (sessionId: string, message: string, token: string) =>
    request<ChatTurnResponse>(
      `/chat`,
      { method: "POST", body: JSON.stringify({ session_id: sessionId, message }) },
      token
    ),

  listSessions: (token: string) =>
    request<{ session_id: string; preview: string; updated_at: string | null }[]>(
      `/chat/sessions`,
      {},
      token
    ),

  deleteSession: (sessionId: string, token: string) =>
    request<{ deleted: boolean }>(
      `/chat/sessions/${sessionId}`,
      { method: "DELETE" },
      token
    ),

  getConversation: (sessionId: string, token: string) =>
    request<{
      session_id: string;
      messages: { role: "user" | "assistant" | "system"; content: string; products?: Product[] }[];
      extracted_preferences: Record<string, unknown>;
    }>(`/chat/${sessionId}`, {}, token),

  getCart: (token: string) =>
    request<{ items: any[]; subtotal: number; count: number }>(`/cart`, {}, token),

  addToCart: (slug: string, qty: number, token: string) =>
    request(`/cart/add`, { method: "POST", body: JSON.stringify({ slug, qty }) }, token),

  updateCart: (slug: string, qty: number, token: string) =>
    request(`/cart/update`, { method: "POST", body: JSON.stringify({ slug, qty }) }, token),

  removeFromCart: (slug: string, token: string) =>
    request(`/cart/${slug}`, { method: "DELETE" }, token),

  pushHistory: (slug: string, token: string) =>
    request(`/users/history/${slug}`, { method: "POST" }, token),

  transcribe: async (blob: Blob): Promise<{ text: string }> => {
    const form = new FormData();
    form.append("file", blob, "audio.webm");
    const res = await fetch(`${BASE}/transcribe`, {
      method: "POST",
      body: form,
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json() as Promise<{ text: string }>;
  },
};
