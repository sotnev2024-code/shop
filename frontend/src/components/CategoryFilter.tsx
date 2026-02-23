import React from 'react';
import type { Category } from '../types';

export type CategoryImageSize = 'small' | 'medium' | 'large' | 'xlarge';

const CATEGORY_SIZE_CLASS: Record<CategoryImageSize, string> = {
  small: 'w-20 h-20',
  medium: 'w-40 h-40',
  large: 'w-56 h-56',
  xlarge: 'w-72 h-72',
};

const CATEGORY_CARD_WIDTH: Record<CategoryImageSize, string> = {
  small: 'w-20',
  medium: 'w-40',
  large: 'w-56',
  xlarge: 'w-72',
};

interface CategoryFilterProps {
  categories: Category[];
  selected: number | null;
  onSelect: (id: number | null) => void;
  subcategories?: Category[];
  parentId?: number | null;
  parentName?: string;
  categoryImageSize?: CategoryImageSize;
  /** id корневой категории, у которой открыт ряд подкатегорий (для подсветки) */
  expandedId?: number | null;
}

const pillClass = (active: boolean) =>
  `flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all ${
    active ? 'bg-tg-button text-tg-button-text' : 'bg-tg-secondary text-tg-text'
  }`;

export const CategoryFilter: React.FC<CategoryFilterProps> = ({
  categories,
  selected,
  onSelect,
  subcategories = undefined,
  parentId = null,
  parentName = '',
  categoryImageSize = 'medium',
  expandedId = null,
}) => {
  const withImages = categories.filter((c) => c.image_url);
  const withoutImages = categories.filter((c) => !c.image_url);
  const hasAllCategory = categories.some((c) => c.slug === 'all');

  const hasImages = withImages.length > 0;
  const imgClass = CATEGORY_SIZE_CLASS[categoryImageSize];
  const cardWidth = CATEGORY_CARD_WIDTH[categoryImageSize];

  return (
    <div className="space-y-2">
      {/* Первый ряд: категории с картинками (карточки) — включая «Все», если у неё есть картинка; иначе «Все» + остальные пилюлями */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide items-start">
        {hasImages ? (
          withImages.map((cat) => {
            const isAllCategory = cat.slug === 'all';
            return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelect(isAllCategory ? null : cat.id)}
              className={`flex-none shrink-0 ${cardWidth} rounded-xl overflow-hidden text-left transition-all ${
                (isAllCategory ? selected === null : selected === cat.id) ? 'ring-2 ring-tg-button' : expandedId === cat.id ? 'ring-2 ring-tg-hint' : ''
              }`}
            >
              <img
                src={cat.image_url!}
                alt=""
                className={`${imgClass} object-cover bg-tg-secondary`}
              />
              <span className={`block ${cardWidth} py-1 px-1 text-xs font-medium text-tg-text truncate bg-tg-secondary`}>
                {cat.name}
              </span>
            </button>
            );
          })
        ) : (
          <>
            {!hasAllCategory && (
            <button
              onClick={() => onSelect(null)}
              className={pillClass(selected === null)}
            >
              Все
            </button>
            )}
            {withoutImages.map((cat) => {
              const isAllCategory = cat.slug === 'all';
              return (
              <button
                key={cat.id}
                onClick={() => onSelect(isAllCategory ? null : cat.id)}
                className={pillClass(isAllCategory ? selected === null : (selected === cat.id || expandedId === cat.id))}
              >
                {cat.name}
              </button>
              );
            })}
          </>
        )}
      </div>
      {/* Второй ряд: «Все» (если нет категории «Все» из API) + категории без картинок */}
      {hasImages && (
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {!hasAllCategory && (
          <button
            onClick={() => onSelect(null)}
            className={pillClass(selected === null)}
          >
            Все
          </button>
          )}
          {withoutImages.map((cat) => {
            const isAllCategory = cat.slug === 'all';
            return (
            <button
              key={cat.id}
              onClick={() => onSelect(isAllCategory ? null : cat.id)}
              className={pillClass(isAllCategory ? selected === null : (selected === cat.id || expandedId === cat.id))}
            >
              {cat.name}
            </button>
            );
          })}
        </div>
      )}
      {subcategories != null && subcategories.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
          <button
            onClick={() => onSelect(parentId ?? null)}
            className={pillClass(selected === parentId)}
          >
            Все в {parentName}
          </button>
          {subcategories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => onSelect(cat.id)}
              className={pillClass(selected === cat.id)}
            >
              {cat.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};





