import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package } from 'lucide-react';
import { getOrders } from '../api/endpoints';
import type { Order } from '../types';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useBackButton } from '../hooks/useBackButton';

const statusLabels: Record<string, { label: string; variant: 'default' | 'success' | 'warning' | 'danger' }> = {
  new: { label: 'Новый', variant: 'default' },
  confirmed: { label: 'Подтверждён', variant: 'warning' },
  paid: { label: 'Оплачен', variant: 'success' },
  delivering: { label: 'Доставка', variant: 'warning' },
  done: { label: 'Выполнен', variant: 'success' },
  cancelled: { label: 'Отменён', variant: 'danger' },
};

export const OrdersPage: React.FC = () => {
  useBackButton();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOrders()
      .then(({ data }) => setOrders(data.items))
      .finally(() => setLoading(false));
  }, []);

  if (!loading && orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4 pb-24">
        <Package className="w-16 h-16 text-tg-hint mb-4" />
        <h2 className="text-xl font-bold text-tg-text mb-2">Нет заказов</h2>
        <p className="text-sm text-tg-hint text-center mb-6">
          Оформите первый заказ в каталоге
        </p>
        <Button onClick={() => navigate('/')}>Перейти в каталог</Button>
      </div>
    );
  }

  return (
    <div className="pb-20">
      <div className="px-4 pt-4 pb-3">
        <h1 className="text-xl font-bold text-tg-text">Мои заказы</h1>
      </div>

      <div className="px-4 space-y-3">
        {orders.map((order) => {
          const statusInfo = statusLabels[order.status] || statusLabels.new;
          return (
            <div
              key={order.id}
              onClick={() => navigate(`/order/${order.id}`)}
              className="bg-tg-secondary rounded-2xl p-4 cursor-pointer active:scale-[0.98] transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-base font-bold text-tg-text">
                  Заказ #{order.id}
                </span>
                <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
              </div>
              <div className="text-sm text-tg-hint mb-1">
                {new Date(order.created_at).toLocaleDateString('ru-RU', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-tg-hint">
                  {order.items.length} товар(ов)
                </span>
                <span className="text-base font-bold text-tg-text">
                  {order.total.toLocaleString('ru-RU')} ₽
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

