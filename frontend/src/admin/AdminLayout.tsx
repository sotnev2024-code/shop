import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Image, LayoutDashboard, Package, ShoppingCart, Tag, Send, Settings } from 'lucide-react';

const adminTabs = [
  { path: '/admin', icon: LayoutDashboard, label: 'Главная' },
  { path: '/admin/orders', icon: ShoppingCart, label: 'Заказы' },
  { path: '/admin/products', icon: Package, label: 'Товары' },
  { path: '/admin/banners', icon: Image, label: 'Баннеры' },
  { path: '/admin/promos', icon: Tag, label: 'Промо' },
  { path: '/admin/mailing', icon: Send, label: 'Рассылка' },
  { path: '/admin/settings', icon: Settings, label: 'Настройки' },
];

export const AdminLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="px-4 pt-4 pb-2 flex items-center gap-3 border-b border-tg-secondary">
        <button onClick={() => navigate('/')}>
          <ArrowLeft className="w-5 h-5 text-tg-text" />
        </button>
        <h2 className="text-lg font-bold text-tg-text">Админ-панель</h2>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 overflow-x-auto px-4 py-2 border-b border-tg-secondary">
        {adminTabs.map((tab) => {
          const isActive = location.pathname === tab.path;
          const Icon = tab.icon;
          return (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium flex-shrink-0 ${
                isActive ? 'bg-tg-button text-tg-button-text' : 'text-tg-hint'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="px-4 pt-4">
        <Outlet />
      </div>
    </div>
  );
};





