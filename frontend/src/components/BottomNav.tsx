import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutGrid, Heart, ShoppingCart, User } from 'lucide-react';
import { useCartStore } from '../store/cartStore';

export const BottomNav: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const totalItems = useCartStore((s) => s.totalItems);

  const tabs = [
    { path: '/', icon: LayoutGrid, label: 'Каталог' },
    { path: '/favorites', icon: Heart, label: 'Избранное' },
    { path: '/cart', icon: ShoppingCart, label: 'Корзина', badge: totalItems },
    { path: '/profile', icon: User, label: 'Профиль' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-tg-bg border-t border-tg-secondary z-50">
      <div className="flex items-center justify-around py-2 pb-[env(safe-area-inset-bottom)]">
        {tabs.map((tab) => {
          const isActive = location.pathname === tab.path;
          const Icon = tab.icon;
          return (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 relative ${
                isActive ? 'text-tg-button' : 'text-tg-hint'
              }`}
            >
              <div className="relative">
                <Icon className="w-6 h-6" />
                {tab.badge ? (
                  <span className="absolute -top-1.5 -right-2 bg-red-500 text-white text-[10px] font-bold min-w-[16px] h-4 rounded-full flex items-center justify-center px-1">
                    {tab.badge}
                  </span>
                ) : null}
              </div>
              <span className="text-[10px] font-medium">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
