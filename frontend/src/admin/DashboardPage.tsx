import React, { useEffect, useState } from 'react';
import { Users, Package, DollarSign, ShoppingBag } from 'lucide-react';
import { getStats } from '../api/endpoints';
import type { Stats } from '../types';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats()
      .then(({ data }) => setStats(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-tg-button border-t-transparent rounded-full" />
      </div>
    );
  }

  const cards = [
    {
      icon: <Users className="w-6 h-6 text-blue-500" />,
      title: 'Пользователи',
      value: stats.users.total,
      sub: `+${stats.users.new_month} за месяц`,
    },
    {
      icon: <Package className="w-6 h-6 text-green-500" />,
      title: 'Заказы',
      value: stats.orders.total,
      sub: `${stats.orders.week} за неделю`,
    },
    {
      icon: <DollarSign className="w-6 h-6 text-yellow-500" />,
      title: 'Выручка (месяц)',
      value: `${stats.revenue.month.toLocaleString('ru-RU')} ₽`,
      sub: `Всего: ${stats.revenue.total.toLocaleString('ru-RU')} ₽`,
    },
    {
      icon: <ShoppingBag className="w-6 h-6 text-purple-500" />,
      title: 'Товары',
      value: stats.products.total,
      sub: 'в каталоге',
    },
  ];

  return (
    <div>
      <h1 className="text-xl font-bold text-tg-text mb-4">Панель управления</h1>

      <div className="grid grid-cols-2 gap-3">
        {cards.map((card) => (
          <div key={card.title} className="bg-tg-secondary rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              {card.icon}
              <span className="text-xs text-tg-hint">{card.title}</span>
            </div>
            <div className="text-xl font-bold text-tg-text">{card.value}</div>
            <div className="text-xs text-tg-hint mt-1">{card.sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
};





