import React from 'react';
import { ShoppingCart, Heart, CreditCard, HelpCircle } from 'lucide-react';
import { useBackButton } from '../hooks/useBackButton';

const sections = [
  {
    icon: ShoppingCart,
    title: 'Как оформить заказ',
    steps: [
      'Выберите товары из каталога',
      'Нажмите кнопку «В корзину» на карточке товара',
      'Перейдите в корзину и проверьте выбранные товары',
      'Нажмите «Оформить заказ»',
      'Заполните контактные данные и адрес',
      'Подтвердите заказ',
    ],
  },
  {
    icon: Heart,
    title: 'Избранное',
    steps: [
      'Нажмите на сердечко на карточке товара, чтобы добавить его в избранное',
      'Все избранные товары доступны во вкладке «Избранное»',
      'Нажмите на сердечко повторно, чтобы убрать товар из избранного',
    ],
  },
  {
    icon: CreditCard,
    title: 'Оплата и доставка',
    steps: [
      'Способы оплаты зависят от настроек магазина',
      'Возможен самовывоз или доставка — уточняйте при оформлении',
      'Статус заказа можно отслеживать в разделе «Мои заказы»',
    ],
  },
  {
    icon: HelpCircle,
    title: 'О приложении',
    steps: [
      'Это приложение — мини-магазин внутри Telegram',
      'Все данные надёжно защищены',
      'Если у вас возникли проблемы — обратитесь в поддержку через профиль',
    ],
  },
];

export const HelpPage: React.FC = () => {
  useBackButton();

  return (
    <div className="pb-20">
      <div className="px-4 pt-4 pb-3">
        <h1 className="text-xl font-bold text-tg-text">Помощь</h1>
      </div>

      <div className="px-4 space-y-3">
        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <div
              key={section.title}
              className="bg-tg-secondary rounded-2xl p-4"
            >
              <div className="flex items-center gap-2 mb-3">
                <Icon className="w-5 h-5 text-tg-button" />
                <h3 className="text-base font-semibold text-tg-text">
                  {section.title}
                </h3>
              </div>
              <ol className="space-y-2">
                {section.steps.map((step, idx) => (
                  <li key={idx} className="flex gap-2 text-sm text-tg-hint">
                    <span className="text-tg-button font-medium flex-shrink-0">
                      {idx + 1}.
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          );
        })}
      </div>
    </div>
  );
};





