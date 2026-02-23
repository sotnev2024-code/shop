import React from 'react';
import { Minus, Plus, Trash2, AlertTriangle } from 'lucide-react';
import type { CartItem } from '../types';
import { useCartStore } from '../store/cartStore';

interface CartItemCardProps {
  item: CartItem;
}

export const CartItemCard: React.FC<CartItemCardProps> = ({ item }) => {
  const { updateItem, removeItem } = useCartStore();

  const stock = item.modification_value && item.product.variants?.length
    ? (item.product.variants.find((v) => v.value === item.modification_value)?.quantity ?? 0)
    : item.product.stock_quantity;
  const overStock = stock > 0 && item.quantity > stock;
  const outOfStock = stock <= 0;

  // Thumbnail: first image from media, or image_url
  const thumbnailUrl = (() => {
    if (item.product.media?.length) {
      const sorted = [...item.product.media].sort((a, b) => a.sort_order - b.sort_order);
      const firstImage = sorted.find((m) => m.media_type === 'image');
      if (firstImage?.url) return firstImage.url;
    }
    return item.product.image_url;
  })();

  return (
    <div className={`flex gap-3 p-3 bg-tg-secondary rounded-2xl ${outOfStock ? 'opacity-60' : ''}`}>
      {/* Image */}
      <div className="w-20 h-20 flex-shrink-0 rounded-xl overflow-hidden bg-gray-100">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={item.product.name}
            className={`w-full h-full object-cover ${outOfStock ? 'grayscale' : ''}`}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-2xl">📦</div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium text-tg-text line-clamp-2">{item.product.name}</h3>
        {item.modification_label && (
          <p className="text-xs text-tg-hint mt-0.5">{item.modification_label}</p>
        )}
        <p className="text-base font-bold text-tg-text mt-1">
          {(item.product.price * item.quantity).toLocaleString('ru-RU')} ₽
        </p>

        {/* Stock warnings */}
        {outOfStock && (
          <div className="flex items-center gap-1 mt-1 text-red-500 text-xs">
            <AlertTriangle className="w-3 h-3" />
            <span>Нет в наличии</span>
          </div>
        )}
        {overStock && (
          <div className="flex items-center gap-1 mt-1 text-amber-500 text-xs">
            <AlertTriangle className="w-3 h-3" />
            <span>Осталось {stock} шт.</span>
          </div>
        )}

        {/* Quantity controls */}
        <div className="flex items-center gap-3 mt-2">
          {outOfStock ? (
            <button
              onClick={() => removeItem(item.id)}
              className="text-red-500 text-xs font-medium flex items-center gap-1"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Убрать
            </button>
          ) : (
            <>
              <div className="flex items-center gap-2 bg-tg-bg rounded-full">
                <button
                  onClick={() => updateItem(item.id, item.quantity - 1)}
                  className="w-7 h-7 rounded-full flex items-center justify-center bg-tg-secondary"
                >
                  <Minus className="w-3 h-3" />
                </button>
                <span className="text-sm font-medium min-w-[20px] text-center">
                  {item.quantity}
                </span>
                <button
                  onClick={() => updateItem(item.id, item.quantity + 1)}
                  disabled={stock > 0 && item.quantity >= stock}
                  className="w-7 h-7 rounded-full flex items-center justify-center bg-tg-secondary disabled:opacity-40"
                >
                  <Plus className="w-3 h-3" />
                </button>
              </div>

              <button
                onClick={() => removeItem(item.id)}
                className="text-tg-hint hover:text-red-500 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
