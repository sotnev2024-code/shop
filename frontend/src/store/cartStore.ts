import { create } from 'zustand';
import type { CartItem } from '../types';
import * as api from '../api/endpoints';

interface CartValidationResult {
  removed: Array<{ product_id: number; product_name: string; old_quantity: number }>;
  adjusted: Array<{ product_id: number; product_name: string; old_quantity: number; new_quantity: number }>;
}

interface CartState {
  items: CartItem[];
  totalPrice: number;
  totalItems: number;
  loading: boolean;
  fetchCart: () => Promise<void>;
  addItem: (productId: number, quantity?: number, modificationTypeId?: number | null, modificationValue?: string | null) => Promise<void>;
  updateItem: (itemId: number, quantity: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
  clear: () => Promise<void>;
  validateCart: () => Promise<CartValidationResult>;
  getCartItemByProductId: (productId: number, modificationTypeId?: number | null, modificationValue?: string | null) => CartItem | undefined;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  totalPrice: 0,
  totalItems: 0,
  loading: false,
  fetchCart: async () => {
    set({ loading: true });
    try {
      const { data } = await api.getCart();
      set({
        items: data.items,
        totalPrice: data.total_price,
        totalItems: data.total_items,
        loading: false,
      });
    } catch {
      set({ loading: false });
    }
  },
  addItem: async (productId, quantity = 1, modificationTypeId?, modificationValue?) => {
    try {
      await api.addToCart(productId, quantity, modificationTypeId, modificationValue);
      await get().fetchCart();
    } catch (error: any) {
      // Re-throw so the component can handle the error (e.g. show alert)
      const message = error?.response?.data?.detail || 'Ошибка добавления в корзину';
      if (message === 'Товар закончился на складе') {
        window.Telegram?.WebApp?.showAlert?.(message);
      }
      throw error;
    }
  },
  updateItem: async (itemId, quantity) => {
    try {
      if (quantity <= 0) {
        await api.removeFromCart(itemId);
      } else {
        await api.updateCartItem(itemId, quantity);
      }
      await get().fetchCart();
    } catch (error: any) {
      const message = error?.response?.data?.detail;
      if (message) {
        window.Telegram?.WebApp?.showAlert?.(message);
      }
      await get().fetchCart();
    }
  },
  removeItem: async (itemId) => {
    await api.removeFromCart(itemId);
    await get().fetchCart();
  },
  clear: async () => {
    await api.clearCart();
    set({ items: [], totalPrice: 0, totalItems: 0 });
  },
  validateCart: async () => {
    try {
      const { data } = await api.validateCart();
      set({
        items: data.items,
        totalPrice: data.total_price,
        totalItems: data.total_items,
      });
      return { removed: data.removed, adjusted: data.adjusted };
    } catch {
      return { removed: [], adjusted: [] };
    }
  },
  getCartItemByProductId: (productId, modificationTypeId?, modificationValue?) => {
    return get().items.find(
      (item) =>
        item.product_id === productId &&
        (modificationTypeId == null ? item.modification_type_id == null : item.modification_type_id === modificationTypeId) &&
        (modificationValue == null || modificationValue === '' ? (item.modification_value == null || item.modification_value === '') : item.modification_value === modificationValue)
    );
  },
}));
