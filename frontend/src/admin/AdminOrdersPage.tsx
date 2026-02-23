import React, { useEffect, useState } from 'react';
import { adminGetOrders, adminUpdateOrder } from '../api/endpoints';
import type { Order } from '../types';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

const statuses = ['new', 'confirmed', 'paid', 'delivering', 'done', 'cancelled'];
const statusLabels: Record<string, string> = {
  new: 'Новый',
  confirmed: 'Подтверждён',
  paid: 'Оплачен',
  delivering: 'Доставка',
  done: 'Выполнен',
  cancelled: 'Отменён',
};

export const AdminOrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const fetchOrders = () => {
    setLoading(true);
    adminGetOrders({ status: filter || undefined })
      .then(({ data }) => setOrders(data.items))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOrders();
  }, [filter]);

  const handleStatusChange = async (orderId: number, newStatus: string) => {
    await adminUpdateOrder(orderId, { status: newStatus });
    fetchOrders();
  };

  return (
    <div>
      <h1 className="text-xl font-bold text-tg-text mb-4">Заказы</h1>

      {/* Status filter */}
      <div className="flex gap-2 overflow-x-auto pb-3 mb-3">
        <button
          onClick={() => setFilter('')}
          className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium ${
            !filter ? 'bg-tg-button text-tg-button-text' : 'bg-tg-secondary text-tg-text'
          }`}
        >
          Все
        </button>
        {statuses.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium ${
              filter === s ? 'bg-tg-button text-tg-button-text' : 'bg-tg-secondary text-tg-text'
            }`}
          >
            {statusLabels[s]}
          </button>
        ))}
      </div>

      {/* Orders list */}
      <div className="space-y-3">
        {orders.map((order) => (
          <div
            key={order.id}
            className="bg-tg-secondary rounded-2xl p-4"
          >
            <div
              className="cursor-pointer"
              onClick={() => setExpandedId(expandedId === order.id ? null : order.id)}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-tg-text">#{order.id}</span>
                <Badge>{statusLabels[order.status]}</Badge>
              </div>
              <div className="text-xs text-tg-hint">
                {order.customer_name} • {order.customer_phone}
              </div>
              <div className="text-sm font-bold text-tg-text mt-1">
                {order.total.toLocaleString('ru-RU')} ₽
                {order.bonus_used != null && order.bonus_used > 0 && (
                  <span className="block text-xs font-normal text-tg-hint mt-0.5">
                    Списано бонусов: {Math.round(order.bonus_used).toLocaleString('ru-RU')}
                  </span>
                )}
                {order.delivery_fee != null && order.delivery_fee > 0 && (
                  <span className="block text-xs font-normal text-tg-hint mt-0.5">
                    Доставка: {order.delivery_fee.toLocaleString('ru-RU')} ₽
                  </span>
                )}
              </div>
            </div>

            {expandedId === order.id && (
              <div className="mt-3 pt-3 border-t border-tg-bg">
                {/* Items */}
                {order.items.map((item) => (
                  <div key={item.id} className="text-xs text-tg-hint py-0.5">
                    {item.product_name}
                    {item.modification_label ? ` (${item.modification_label})` : ''} x{item.quantity} — {(item.price_at_order * item.quantity).toFixed(2)} ₽
                  </div>
                ))}
                {order.address && (
                  <div className="text-xs text-tg-hint mt-2">📍 {order.address}</div>
                )}
                {order.bonus_used != null && order.bonus_used > 0 && (
                  <div className="text-xs text-tg-hint mt-2">🎁 Списано бонусов: {Math.round(order.bonus_used).toLocaleString('ru-RU')}</div>
                )}
                {order.delivery_fee != null && order.delivery_fee > 0 && (
                  <div className="text-xs text-tg-hint mt-2">🚚 Доставка: {order.delivery_fee.toLocaleString('ru-RU')} ₽</div>
                )}

                {/* Status buttons */}
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {statuses.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleStatusChange(order.id, s)}
                      disabled={order.status === s}
                      className={`px-2 py-1 rounded-lg text-[10px] font-medium ${
                        order.status === s
                          ? 'bg-tg-button text-tg-button-text'
                          : 'bg-tg-bg text-tg-hint'
                      }`}
                    >
                      {statusLabels[s]}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {!loading && orders.length === 0 && (
        <div className="text-center py-8 text-tg-hint text-sm">Нет заказов</div>
      )}
    </div>
  );
};





