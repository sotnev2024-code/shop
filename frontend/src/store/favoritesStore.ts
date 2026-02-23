import { create } from 'zustand';
import type { Product } from '../types';
import * as api from '../api/endpoints';

interface FavoritesState {
  items: Product[];
  loading: boolean;
  fetchFavorites: () => Promise<void>;
  validateFavorites: () => Promise<Array<{ product_id: number; product_name: string }>>;
  toggle: (productId: number, isFavorite: boolean, product?: Product) => Promise<void>;
  isFavorite: (productId: number) => boolean;
}

export const useFavoritesStore = create<FavoritesState>((set, get) => ({
  items: [],
  loading: false,
  fetchFavorites: async () => {
    set({ loading: true });
    try {
      const { data } = await api.getFavorites();
      set({ items: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },
  validateFavorites: async () => {
    try {
      const { data } = await api.validateFavorites();
      const removed = data?.removed ?? [];
      if (removed.length > 0) {
        await get().fetchFavorites();
      }
      return removed;
    } catch {
      return [];
    }
  },
  toggle: async (productId, isFavorite, product?) => {
    const previousItems = get().items;

    // Optimistic update
    if (isFavorite) {
      set({ items: previousItems.filter((item) => item.id !== productId) });
    } else if (product) {
      set({ items: [...previousItems, { ...product, is_favorite: true }] });
    }

    try {
      if (isFavorite) {
        await api.removeFromFavorites(productId);
      } else {
        await api.addToFavorites(productId);
      }
    } catch {
      set({ items: previousItems });
      return;
    }

    try {
      const { data } = await api.getFavorites();
      set({ items: data });
    } catch {
      // Add/remove succeeded; refetch failed — keep optimistic state
    }
  },
  isFavorite: (productId) => {
    return get().items.some((item) => item.id === productId);
  },
}));
