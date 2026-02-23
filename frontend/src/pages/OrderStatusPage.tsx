import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, Clock, Truck } from 'lucide-react';
import { getOrder } from '../api/endpoints';
import type { Order } from '../types';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useBackButton } from '../hooks/useBackButton';

export const OrderStatusPage: React.FC = () => {
  useBackButton();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getOrder(Number(id))
      .then(({ data }) => setOrder(data))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading || !order) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-tg-button border-t-transparent rounded-full" />
      </div>
    );
  }

  const statusIcon = {
    new: <Clock className="w-12 h-12 text-yellow-500" />,
    confirmed: <Clock className="w-12 h-12 text-blue-500" />,
    paid: <CheckCircle className="w-12 h-12 text-green-500" />,
    delivering: <Truck className="w-12 h-12 text-blue-500" />,
    done: <CheckCircle className="w-12 h-12 text-green-500" />,
    cancelled: <Clock className="w-12 h-12 text-red-500" />,
  }[order.status] || <Clock className="w-12 h-12 text-tg-hint" />;

  const statusLabels: Record<string, string> = {
    new: 'Заказ принят',
    confirmed: 'Заказ подтверждён',
    paid: 'Заказ оплачен',
    delivering: 'Заказ в пути',
    done: 'Заказ выполнен',
    cancelled: 'Заказ отменён',
  };

  return (
    <div className="pb-24">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 flex items-center gap-3">
        <button onClick={() => navigate('/orders')}>
          <ArrowLeft className="w-6 h-6 text-tg-text" />
        </button>
        <h1 className="text-xl font-bold text-tg-text">Заказ #{order.id}</h1>
      </div>

      {/* Status */}
      <div className="text-center py-6">
        <div className="flex justify-center mb-3">{statusIcon}</div>
        <h2 className="text-xl font-bold text-tg-text mb-1">
          {statusLabels[order.status] || order.status}
        </h2>
        <p className="text-sm text-tg-hint">
          {new Date(order.created_at).toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>

      {/* Order details */}
      <div className="px-4 space-y-3">
        {/* Items */}
        <div className="bg-tg-secondary rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-tg-text mb-3">Товары</h3>
          {order.items.map((item) => (
            <div key={item.id} className="flex justify-between text-sm py-1.5">
              <span className="text-tg-text truncate mr-2">
                {item.product_name}
                {item.modification_label ? ` (${item.modification_label})` : ''} x{item.quantity}
              </span>
              <span className="text-tg-text flex-shrink-0 font-medium">
                {(item.price_at_order * item.quantity).toLocaleString('ru-RU')} ₽
              </span>
            </div>
          ))}
          {order.discount > 0 && (
            <div className="flex justify-between text-sm py-1.5 text-green-600">
              <span>Скидка</span>
              <span>-{order.discount.toLocaleString('ru-RU')} ₽</span>
            </div>
          )}
          {order.bonus_used != null && order.bonus_used > 0 && (
            <div className="flex justify-between text-sm py-1.5 text-tg-hint">
              <span>Списано бонусов</span>
              <span>-{Math.round(order.bonus_used).toLocaleString('ru-RU')}</span>
            </div>
          )}
          {order.delivery_fee != null && order.delivery_fee > 0 && (
            <div className="flex justify-between text-sm py-1.5">
              <span className="text-tg-hint">Доставка</span>
              <span className="text-tg-text">{order.delivery_fee.toLocaleString('ru-RU')} ₽</span>
            </div>
          )}
          <div className="border-t border-tg-bg mt-2 pt-2 flex justify-between">
            <span className="font-bold text-tg-text">Итого</span>
            <span className="font-bold text-tg-text">
              {order.total.toLocaleString('ru-RU')} ₽
            </span>
          </div>
        </div>

        {/* Delivery info */}
        <div className="bg-tg-secondary rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-tg-text mb-2">Данные заказа</h3>
          <div className="space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-tg-hint">Имя</span>
              <span className="text-tg-text">{order.customer_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-tg-hint">Телефон</span>
              <span className="text-tg-text">{order.customer_phone}</span>
            </div>
            {order.address && (
              <div className="flex justify-between">
                <span className="text-tg-hint">Адрес</span>
                <span className="text-tg-text text-right max-w-[200px]">{order.address}</span>
              </div>
            )}
            {order.delivery_service && (
              <div className="flex justify-between">
                <span className="text-tg-hint">Доставка</span>
                <span className="text-tg-text">{order.delivery_service}</span>
              </div>
            )}
            {order.tracking_number && (
              <div className="flex justify-between">
                <span className="text-tg-hint">Трек-номер</span>
                <span className="text-tg-link">{order.tracking_number}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Back to catalog */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-tg-bg border-t border-tg-secondary">
        <Button onClick={() => navigate('/')} fullWidth size="lg" variant="secondary">
          Вернуться в каталог
        </Button>
      </div>
    </div>
  );
};

