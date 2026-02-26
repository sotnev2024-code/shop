import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  Settings,
  HelpCircle,
  MessageCircle,
  Store,
  Smartphone,
  ChevronRight,
  Shield,
  Gift,
} from 'lucide-react';
import { useConfigStore } from '../store/configStore';

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const config = useConfigStore((s) => s.config);
  const configLoading = useConfigStore((s) => s.loading);
  const fetchConfig = useConfigStore((s) => s.fetchConfig);
  const [canAddToHome, setCanAddToHome] = useState(false);

  // Обновить конфиг при открытии профиля (актуальные is_admin / is_owner)
  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  // Telegram user data
  const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user;
  const firstName = tgUser?.first_name || 'Пользователь';
  const lastName = tgUser?.last_name || '';
  const photoUrl = tgUser?.photo_url || null;
  const username = tgUser?.username || null;

  useEffect(() => {
    // Check if the app can be added to the home screen
    const tg = window.Telegram?.WebApp;
    if (tg?.checkHomeScreenStatus) {
      try {
        tg.checkHomeScreenStatus((status: string) => {
          // status: 'unsupported' | 'unknown' | 'added' | 'missed'
          setCanAddToHome(status !== 'added' && status !== 'unsupported');
        });
      } catch {
        setCanAddToHome(false);
      }
    }
  }, []);

  const handleAddToHome = () => {
    const tg = window.Telegram?.WebApp;
    if (tg?.addToHomeScreen) {
      tg.addToHomeScreen();
      setCanAddToHome(false);
    }
  };

  const handleSupport = () => {
    const raw = config?.support_link?.trim();
    if (!raw) return;
    let supportLink: string;
    if (/^https?:\/\//i.test(raw)) {
      supportLink = raw;
    } else if (raw.startsWith('@')) {
      supportLink = `https://t.me/${raw.slice(1)}`;
    } else {
      supportLink = `https://t.me/${raw.replace(/^@/, '')}`;
    }
    try {
      const tg = window.Telegram?.WebApp;
      if (tg?.openTelegramLink) {
        tg.openTelegramLink(supportLink);
      } else {
        window.open(supportLink, '_blank');
      }
    } catch {
      window.open(supportLink, '_blank');
    }
  };

  const menuItems = [
    ...(config?.bonus_enabled
      ? [{
          icon: Gift,
          label: 'Бонусы',
          subtitle: 'Баланс и история',
          onClick: () => navigate('/profile/bonuses'),
        }]
      : []),
    {
      icon: Package,
      label: 'Мои заказы',
      subtitle: 'История и статус заказов',
      onClick: () => navigate('/orders'),
    },
    {
      icon: Settings,
      label: 'Настройки',
      subtitle: 'Кэш и данные',
      onClick: () => navigate('/profile/settings'),
    },
    {
      icon: HelpCircle,
      label: 'Помощь',
      subtitle: 'Как пользоваться приложением',
      onClick: () => navigate('/profile/help'),
    },
    {
      icon: MessageCircle,
      label: 'Поддержка',
      subtitle: 'Связаться с нами',
      onClick: handleSupport,
      hidden: !config?.support_link,
    },
  ];

  return (
    <div className="pb-20">
      {/* User card */}
      <div className="px-4 pt-6 pb-4 flex items-center gap-4">
        {photoUrl ? (
          <img
            src={photoUrl}
            alt={firstName}
            className="w-16 h-16 rounded-full object-cover"
          />
        ) : (
          <div className="w-16 h-16 rounded-full bg-tg-button text-tg-button-text flex items-center justify-center text-xl font-bold">
            {firstName.charAt(0)}
            {lastName ? lastName.charAt(0) : ''}
          </div>
        )}
        <div>
          <h1 className="text-xl font-bold text-tg-text">
            {firstName} {lastName}
          </h1>
          {username && (
            <p className="text-sm text-tg-hint">@{username}</p>
          )}
        </div>
      </div>

      {/* Telegram ID и статус админа (для отладки кнопки «Мой магазин») */}
      {config != null && config.current_telegram_id != null && (
        <div className="px-4 pb-2">
          <p className="text-xs text-tg-hint">
            Ваш Telegram ID: <span className="font-mono text-tg-text">{config.current_telegram_id}</span>
            {' · '}
            Кнопка «Мой магазин»: <span className="font-medium text-tg-text">{config.is_admin ? 'да' : 'нет'}</span>
            {!config?.is_admin && (
              <span className="block mt-1">
                Добавьте этот ID в ADMIN_IDS на сервере (в .env) и перезапустите бэкенд.
              </span>
            )}
          </p>
        </div>
      )}

      {/* Admin: My Shop */}
      {config?.is_admin && (
        <div className="px-4 pb-3">
          <button
            onClick={() => navigate('/admin')}
            className="w-full flex items-center gap-3 p-4 bg-tg-button text-tg-button-text rounded-2xl active:scale-[0.98] transition-all"
          >
            <Store className="w-6 h-6" />
            <div className="flex-1 text-left">
              <div className="font-semibold">Мой магазин</div>
              <div className="text-xs opacity-80">
                Товары, заказы, статистика, промокоды
              </div>
            </div>
            <ChevronRight className="w-5 h-5 opacity-60" />
          </button>
        </div>
      )}

      {/* Owner: Platform Settings */}
      {config?.is_owner && (
        <div className="px-4 pb-3">
          <button
            onClick={() => navigate('/owner')}
            className="w-full flex items-center gap-3 p-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-2xl active:scale-[0.98] transition-all"
          >
            <Shield className="w-6 h-6" />
            <div className="flex-1 text-left">
              <div className="font-semibold">Настройки платформы</div>
              <div className="text-xs opacity-80">
                Модули, интеграции, службы доставки
              </div>
            </div>
            <ChevronRight className="w-5 h-5 opacity-60" />
          </button>
        </div>
      )}

      {/* Menu items */}
      <div className="px-4 space-y-2">
        {menuItems
          .filter((item) => !item.hidden)
          .map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                onClick={item.onClick}
                className="w-full flex items-center gap-3 p-4 bg-tg-secondary rounded-2xl active:scale-[0.98] transition-all"
              >
                <div className="w-10 h-10 rounded-full bg-tg-bg flex items-center justify-center">
                  <Icon className="w-5 h-5 text-tg-button" />
                </div>
                <div className="flex-1 text-left">
                  <div className="text-base font-medium text-tg-text">
                    {item.label}
                  </div>
                  <div className="text-xs text-tg-hint">{item.subtitle}</div>
                </div>
                <ChevronRight className="w-5 h-5 text-tg-hint" />
              </button>
            );
          })}
      </div>

      {/* Add to home screen */}
      {canAddToHome && (
        <div className="px-4 mt-4">
          <button
            onClick={handleAddToHome}
            className="w-full flex items-center gap-3 p-4 bg-tg-secondary rounded-2xl active:scale-[0.98] transition-all border border-dashed border-tg-hint/30"
          >
            <div className="w-10 h-10 rounded-full bg-tg-bg flex items-center justify-center">
              <Smartphone className="w-5 h-5 text-tg-button" />
            </div>
            <div className="flex-1 text-left">
              <div className="text-base font-medium text-tg-text">
                Добавить на главный экран
              </div>
              <div className="text-xs text-tg-hint">
                Быстрый доступ к магазину
              </div>
            </div>
          </button>
        </div>
      )}
    </div>
  );
};

