import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingBag, Trash2 } from 'lucide-react';
import { useCartStore } from '../store/cartStore';
import { CartItemCard } from '../components/CartItemCard';
import { Button } from '../components/ui/Button';

export const CartPage: React.FC = () => {
  const navigate = useNavigate();
  const { items, totalPrice, totalItems, loading, fetchCart, clear, validateCart } = useCartStore();

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  if (!loading && items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4 pb-24">
        <ShoppingBag className="w-16 h-16 text-tg-hint mb-4" />
        <h2 className="text-xl font-bold text-tg-text mb-2">Корзина пуста</h2>
        <p className="text-sm text-tg-hint text-center mb-6">
          Добавьте товары из каталога
        </p>
        <Button onClick={() => navigate('/')}>Перейти в каталог</Button>
      </div>
    );
  }

  return (
    <div className="pb-48">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 flex items-center justify-between">
        <h1 className="text-xl font-bold text-tg-text">
          Корзина ({totalItems})
        </h1>
        <button
          onClick={clear}
          className="flex items-center gap-1 text-sm text-tg-destructive"
        >
          <Trash2 className="w-4 h-4" />
          Очистить
        </button>
      </div>

      {/* Items */}
      <div className="px-4 space-y-3">
        {items.map((item) => (
          <CartItemCard key={item.id} item={item} />
        ))}
      </div>

      {/* Total + Checkout */}
      <div className="fixed bottom-16 left-0 right-0 p-4 bg-tg-bg border-t border-tg-secondary">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-tg-hint">Итого:</span>
          <span className="text-xl font-bold text-tg-text">
            {totalPrice.toLocaleString('ru-RU')} ₽
          </span>
        </div>
        <Button
          onClick={async () => {
            const { removed, adjusted } = await validateCart();
            if (removed.length > 0 || adjusted.length > 0) {
              const parts: string[] = [];
              if (removed.length > 0) {
                parts.push(`Убрано (нет в наличии): ${removed.map((r) => r.product_name).join(', ')}`);
              }
              if (adjusted.length > 0) {
                parts.push(
                  adjusted.map((a) => `${a.product_name}: ${a.old_quantity} → ${a.new_quantity} шт.`).join(', ')
                );
              }
              window.Telegram?.WebApp?.showAlert?.(parts.join('\n')) ?? alert(parts.join('\n'));
            }
            navigate('/checkout');
          }}
          fullWidth
          size="lg"
        >
          Оформить заказ
        </Button>
      </div>
    </div>
  );
};





