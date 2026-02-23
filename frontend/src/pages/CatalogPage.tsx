import React, { useEffect, useState, useCallback } from 'react';
import { getProducts, getCategories, getBanners } from '../api/endpoints';
import type { Product, Category, Banner } from '../types';
import { ProductCard } from '../components/ProductCard';
import { SearchBar } from '../components/SearchBar';
import { CategoryFilter } from '../components/CategoryFilter';
import { Skeleton } from '../components/ui/Skeleton';
import { SlidersHorizontal, Store } from 'lucide-react';
import { useConfigStore } from '../store/configStore';

export const CatalogPage: React.FC = () => {
  const config = useConfigStore((s) => s.config);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [banners, setBanners] = useState<Banner[]>([]);
  /** Категория, по нажатию на которую открыт ряд подкатегорий (только для корневых с детьми) */
  const [expandedCategoryId, setExpandedCategoryId] = useState<number | null>(null);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await getProducts({
        page,
        per_page: 20,
        category_id: selectedCategory ?? undefined,
        search: search || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setProducts(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  }, [page, selectedCategory, search, sortBy, sortOrder]);

  useEffect(() => {
    getCategories().then(({ data }) => setCategories(data));
  }, []);

  useEffect(() => {
    getBanners().then(({ data }) => setBanners(data));
  }, []);

  // API returns tree: roots with children. First row = roots.
  const rootCategories = categories;
  // Подкатегории показываются при раскрытии корневой категории по клику (expandedCategoryId)
  const expandedRoot = expandedCategoryId != null ? rootCategories.find((c) => c.id === expandedCategoryId) : null;
  const subcategories = expandedRoot?.children ?? undefined;
  const subcategoriesParentId = expandedRoot?.id ?? null;
  const subcategoriesParentName = expandedRoot?.name ?? '';

  const handleCategorySelect = (id: number | null) => {
    if (id === null) {
      setSelectedCategory(null);
      setExpandedCategoryId(null);
      return;
    }
    // Клик по «Все в X» или по подкатегории — только выбираем, ряд подкатегорий не закрываем
    if (expandedCategoryId != null && (id === expandedCategoryId || expandedRoot?.children?.some((ch) => ch.id === id))) {
      setSelectedCategory(id);
      return;
    }
    const cat = rootCategories.find((c) => c.id === id);
    if (cat?.children?.length) {
      setExpandedCategoryId((prev) => (prev === id ? null : id));
      setSelectedCategory(null);
    } else {
      setSelectedCategory(id);
      setExpandedCategoryId(null);
    }
  };

  useEffect(() => {
    setPage(1);
  }, [selectedCategory, search, sortBy, sortOrder]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const handleSearch = (query: string) => {
    setSearch(query);
  };

  const totalPages = Math.ceil(total / 20);

  // Адаптивные размеры: clamp(min, vw%, max) — масштабируются с экраном, остаются в разумных границах
  const getBannerStyles = (): { wrapper: string; wrapperStyle: React.CSSProperties; imgCls: string } => {
    const shape = config?.banner_aspect_shape ?? 'rectangle';
    const size = config?.banner_size ?? 'medium';
    const rectangleSize: Record<string, { w: string; h: string }> = {
      small: { w: 'clamp(100px, 32vw, 180px)', h: 'clamp(66px, 21.3vw, 120px)' },
      medium: { w: 'clamp(140px, 44vw, 240px)', h: 'clamp(93px, 29.3vw, 160px)' },
      large: { w: 'clamp(180px, 56vw, 300px)', h: 'clamp(120px, 37.3vw, 200px)' },
      xl: { w: 'clamp(220px, 68vw, 360px)', h: 'clamp(146px, 45.3vw, 240px)' },
    };
    const squareSize: Record<string, string> = {
      small: 'clamp(88px, 28vw, 140px)',
      medium: 'clamp(120px, 36vw, 180px)',
      large: 'clamp(160px, 48vw, 220px)',
      xl: 'clamp(200px, 60vw, 280px)',
    };
    const rect = rectangleSize[size] ?? rectangleSize.medium;
    const sq = squareSize[size] ?? squareSize.medium;
    if (shape === 'square') {
      return {
        wrapper: 'flex-none rounded-xl overflow-hidden shrink-0',
        wrapperStyle: { width: sq, height: sq, minWidth: sq, minHeight: sq },
        imgCls: 'w-full h-full object-cover',
      };
    }
    return {
      wrapper: 'flex-none rounded-xl overflow-hidden shrink-0',
      wrapperStyle: { width: rect.w, height: rect.h, minWidth: rect.w, minHeight: rect.h },
      imgCls: 'w-full h-full object-cover',
    };
  };

  return (
    <div className="pb-20">
      {/* Shop header — логотип и название по центру */}
      <div className="flex items-center justify-center gap-3 px-4 pt-4 pb-2">
        {config?.bot_photo_url ? (
          <img
            src={config.bot_photo_url}
            alt={config.shop_name}
            className="w-11 h-11 rounded-full object-cover ring-2 ring-tg-button/20 flex-shrink-0"
          />
        ) : (
          <div className="w-11 h-11 rounded-full bg-tg-button/10 flex items-center justify-center flex-shrink-0">
            <Store className="w-5 h-5 text-tg-button" />
          </div>
        )}
        <h1 className="text-lg font-bold text-tg-text leading-tight truncate min-w-0">
          {config?.shop_name || 'Магазин'}
        </h1>
      </div>

      {/* Banners — фиксированные размеры, горизонтальная прокрутка без ползунка */}
      {banners.length > 0 && (
        <div
          className="pt-1 pb-3 overflow-x-auto overflow-y-hidden flex-nowrap scrollbar-hide"
          style={{ WebkitOverflowScrolling: 'touch' }}
        >
          <div className="flex gap-2 items-center pl-4 pr-4 min-w-min">
            {banners.map((banner) => {
              const { wrapper, wrapperStyle, imgCls } = getBannerStyles();
              const img = (
                <img
                  src={banner.image_url}
                  alt=""
                  className={`rounded-xl bg-tg-secondary ${imgCls}`}
                />
              );
              if (banner.link && banner.link.trim()) {
                const isExternal = /^https?:\/\//i.test(banner.link.trim());
                return (
                  <a
                    key={banner.id}
                    href={banner.link.trim()}
                    target={isExternal ? '_blank' : undefined}
                    rel={isExternal ? 'noopener noreferrer' : undefined}
                    className={wrapper}
                    style={wrapperStyle}
                  >
                    {img}
                  </a>
                );
              }
              return (
                <div key={banner.id} className={wrapper} style={wrapperStyle}>
                  {img}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="px-4 pt-1 pb-2">
        <SearchBar onSearch={handleSearch} />
      </div>

      {/* Categories (roots) + subcategories row when a category with children is selected */}
      <div className="px-4 pb-2">
        <CategoryFilter
          categories={rootCategories}
          selected={selectedCategory}
          onSelect={handleCategorySelect}
          subcategories={subcategories}
          parentId={subcategoriesParentId}
          parentName={subcategoriesParentName}
          categoryImageSize={config?.category_image_size ?? 'medium'}
          expandedId={expandedCategoryId}
        />
      </div>

      {/* Sort/Filter toggle */}
      <div className="px-4 pb-3 flex items-center justify-between">
        <span className="text-sm text-tg-hint">
          {total} {total === 1 ? 'товар' : 'товаров'}
        </span>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-1 text-sm text-tg-link"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Сортировка
        </button>
      </div>

      {/* Sort options */}
      {showFilters && (
        <div className="px-4 pb-3 flex gap-2 flex-wrap">
          {[
            { label: 'Новые', sort: 'created_at', order: 'desc' },
            { label: 'Дешевле', sort: 'price', order: 'asc' },
            { label: 'Дороже', sort: 'price', order: 'desc' },
            { label: 'По имени', sort: 'name', order: 'asc' },
          ].map((opt) => (
            <button
              key={opt.label}
              onClick={() => {
                setSortBy(opt.sort);
                setSortOrder(opt.order);
              }}
              className={`px-3 py-1.5 rounded-full text-xs font-medium ${
                sortBy === opt.sort && sortOrder === opt.order
                  ? 'bg-tg-button text-tg-button-text'
                  : 'bg-tg-secondary text-tg-text'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {/* Products grid */}
      <div className="px-4 grid grid-cols-2 gap-3">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-2xl overflow-hidden">
                <Skeleton className="aspect-square" />
                <div className="p-3 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-5 w-1/2" />
                </div>
              </div>
            ))
          : products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
      </div>

      {/* Empty state */}
      {!loading && products.length === 0 && (
        <div className="text-center py-12 text-tg-hint">
          <p className="text-4xl mb-3">🔍</p>
          <p>Товары не найдены</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 px-4 py-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded-lg bg-tg-secondary text-tg-text text-sm disabled:opacity-50"
          >
            ←
          </button>
          <span className="text-sm text-tg-hint">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 rounded-lg bg-tg-secondary text-tg-text text-sm disabled:opacity-50"
          >
            →
          </button>
        </div>
      )}
    </div>
  );
};

