import React, { useState, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { Heart, ShoppingCart, Check, Minus, Plus, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Pagination } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/pagination';
import type { Product, ProductMedia } from '../types';
import { useCartStore } from '../store/cartStore';
import { useFavoritesStore } from '../store/favoritesStore';

interface ProductCardProps {
  product: Product;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const navigate = useNavigate();
  const addItem = useCartStore((s) => s.addItem);
  const updateItem = useCartStore((s) => s.updateItem);
  const cartItems = useCartStore((s) => s.items);
  const getCartItemByProductId = useCartStore((s) => s.getCartItemByProductId);
  const toggleFav = useFavoritesStore((s) => s.toggle);
  const isProductFavorite = useFavoritesStore((s) => s.items.some((item) => item.id === product.id));

  const [justAdded, setJustAdded] = useState(false);
  const [showVariantPicker, setShowVariantPicker] = useState(false);

  const hasVariants = Boolean(product.modification_type && product.variants?.length);
  const outOfStock = hasVariants
    ? !product.variants?.some((v) => v.quantity > 0)
    : product.stock_quantity <= 0;

  const cartItem = hasVariants
    ? null
    : cartItems.find((item) => item.product_id === product.id && item.modification_type_id == null);
  const inCart = !!cartItem;

  // Build sorted media list: videos first, then images
  const mediaList = useMemo<ProductMedia[]>(() => {
    if (product.media && product.media.length > 0) {
      return [...product.media].sort((a, b) => a.sort_order - b.sort_order);
    }
    if (product.image_url) {
      return [{ id: 0, media_type: 'image', url: product.image_url, sort_order: 0 }];
    }
    return [];
  }, [product.media, product.image_url]);

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (outOfStock) {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
      window.Telegram?.WebApp?.showAlert?.('Товар закончился на складе');
      return;
    }
    if (hasVariants) {
      setShowVariantPicker(true);
      return;
    }
    if (inCart) {
      navigate('/cart');
      return;
    }
    try {
      await addItem(product.id);
      setJustAdded(true);
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
      setTimeout(() => setJustAdded(false), 1500);
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  const handleSelectVariant = async (e: React.MouseEvent, value: string, quantity: number) => {
    e.stopPropagation();
    if (quantity <= 0) return;
    if (!product.modification_type) return;
    try {
      await addItem(product.id, 1, product.modification_type.id, value);
      setShowVariantPicker(false);
      setJustAdded(true);
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
      setTimeout(() => setJustAdded(false), 1500);
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  const handleQtyChange = async (e: React.MouseEvent, delta: number) => {
    e.stopPropagation();
    if (!cartItem) return;
    const newQty = cartItem.quantity + delta;
    await updateItem(cartItem.id, newQty);
  };

  const handleToggleFav = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await toggleFav(product.id, isProductFavorite, product);
  };

  return (
    <div
      onClick={() => navigate(`/product/${product.id}`)}
      className="bg-tg-secondary rounded-2xl overflow-hidden cursor-pointer active:scale-[0.98] transition-all"
    >
      {/* Media area */}
      <div className="relative aspect-square bg-gray-100">
        {mediaList.length > 1 ? (
          <div onClick={(e) => e.stopPropagation()}>
            <Swiper
              modules={[Pagination]}
              pagination={{ clickable: true }}
              spaceBetween={0}
              slidesPerView={1}
              className="w-full h-full aspect-square product-card-swiper"
            >
              {mediaList.map((m) => (
                <SwiperSlide key={m.id} onClick={() => navigate(`/product/${product.id}`)}>
                  {m.media_type === 'video' ? (
                    <video
                      src={m.url}
                      autoPlay
                      muted
                      loop
                      playsInline
                      className={`w-full h-full object-cover ${outOfStock ? 'opacity-50 grayscale' : ''}`}
                    />
                  ) : (
                    <img
                      src={m.url}
                      alt={product.name}
                      className={`w-full h-full object-cover ${outOfStock ? 'opacity-50 grayscale' : ''}`}
                    />
                  )}
                </SwiperSlide>
              ))}
            </Swiper>
          </div>
        ) : mediaList.length === 1 ? (
          mediaList[0].media_type === 'video' ? (
            <video
              src={mediaList[0].url}
              autoPlay
              muted
              loop
              playsInline
              className={`w-full h-full object-cover ${outOfStock ? 'opacity-50 grayscale' : ''}`}
            />
          ) : (
            <img
              src={mediaList[0].url}
              alt={product.name}
              className={`w-full h-full object-cover ${outOfStock ? 'opacity-50 grayscale' : ''}`}
            />
          )
        ) : (
          <div className={`w-full h-full flex items-center justify-center text-tg-hint text-4xl ${outOfStock ? 'opacity-50' : ''}`}>
            📦
          </div>
        )}

        {/* Out of stock overlay badge */}
        {outOfStock && (
          <div className="absolute inset-x-0 bottom-0 bg-black/60 text-white text-xs font-medium text-center py-1.5 z-10">
            Нет в наличии
          </div>
        )}

        {/* Favorite button */}
        <button
          onClick={handleToggleFav}
          className="absolute top-2 right-2 w-8 h-8 rounded-full bg-white/80 backdrop-blur flex items-center justify-center transition-transform active:scale-90 z-10"
        >
          <Heart
            className={`w-4 h-4 transition-colors ${
              isProductFavorite ? 'fill-red-500 text-red-500' : 'text-gray-400'
            }`}
          />
        </button>

        {/* Discount badge */}
        {product.old_price && !outOfStock && (
          <div className="absolute top-2 left-2 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full z-10">
            -{Math.round((1 - product.price / product.old_price) * 100)}%
          </div>
        )}

        {/* Media count indicator */}
        {mediaList.length > 1 && (
          <div className="absolute top-2 left-2 bg-black/50 text-white text-[10px] px-1.5 py-0.5 rounded-full z-10">
            {mediaList.length}
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <h3 className="text-sm font-medium text-tg-text line-clamp-2 mb-1">
          {product.name}
        </h3>

        <div className="flex items-center justify-between mt-2">
          <div>
            <span className={`text-base font-bold ${outOfStock ? 'text-tg-hint' : 'text-tg-text'}`}>
              {product.price.toLocaleString('ru-RU')} ₽
            </span>
            {product.old_price && (
              <span className="text-xs text-tg-hint line-through ml-1">
                {product.old_price.toLocaleString('ru-RU')} ₽
              </span>
            )}
          </div>

          {/* Cart button area */}
          {outOfStock ? (
            <div className="w-8 h-8 rounded-full bg-gray-300 text-gray-500 flex items-center justify-center opacity-50 cursor-not-allowed">
              <ShoppingCart className="w-4 h-4" />
            </div>
          ) : !hasVariants && inCart && !justAdded ? (
            <div
              className="flex items-center gap-1 bg-tg-button rounded-full"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={(e) => handleQtyChange(e, -1)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-tg-button-text"
              >
                <Minus className="w-3 h-3" />
              </button>
              <span className="text-xs font-bold text-tg-button-text min-w-[16px] text-center">
                {cartItem!.quantity}
              </span>
              <button
                onClick={(e) => handleQtyChange(e, 1)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-tg-button-text"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>
          ) : justAdded ? (
            <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center animate-bounce-once">
              <Check className="w-4 h-4" />
            </div>
          ) : (
            <button
              onClick={handleAddToCart}
              className="w-8 h-8 rounded-full bg-tg-button text-tg-button-text flex items-center justify-center"
            >
              <ShoppingCart className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Variant picker — портал в body, чтобы не обрезалось и клики работали */}
      {showVariantPicker &&
        hasVariants &&
        product.modification_type &&
        typeof document !== 'undefined' &&
        createPortal(
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Выбор варианта"
            className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50"
            style={{ touchAction: 'none' }}
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) setShowVariantPicker(false);
            }}
            onClick={(e) => {
              if (e.target === e.currentTarget) setShowVariantPicker(false);
            }}
          >
            <div
              className="w-full max-w-lg bg-tg-bg rounded-2xl shadow-xl p-4 max-h-[85vh] flex flex-col"
              onMouseDown={(e) => e.stopPropagation()}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <h3 className="text-base font-semibold text-tg-text flex-1 min-w-0">
                  Выберите {product.modification_type.name}
                </h3>
                <button
                  type="button"
                  aria-label="Закрыть"
                  className="flex-shrink-0 p-2 -m-2 rounded-full text-tg-hint hover:bg-tg-secondary active:bg-tg-secondary"
                  onMouseDown={(e) => e.stopPropagation()}
                  onClick={() => setShowVariantPicker(false)}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-tg-hint truncate mb-3">{product.name}</p>
              <div className="space-y-2 flex-1 min-h-0 overflow-y-auto">
                {(product.variants ?? []).map((v) => {
                  const inCartQty =
                    getCartItemByProductId(
                      product.id,
                      product.modification_type!.id,
                      v.value
                    )?.quantity ?? 0;
                  const available = v.quantity > 0;
                  return (
                    <button
                      key={v.value}
                      type="button"
                      disabled={!available}
                      onMouseDown={(e) => e.stopPropagation()}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectVariant(e, v.value, v.quantity);
                      }}
                      className={`w-full flex items-center justify-between gap-2 px-4 py-3 rounded-xl text-left text-sm font-medium transition-colors ${
                        available
                          ? 'bg-tg-secondary text-tg-text active:bg-tg-button active:text-tg-button-text'
                          : 'bg-tg-secondary/50 text-tg-hint cursor-not-allowed'
                      }`}
                    >
                      <span>{v.value}</span>
                      <span className="text-xs text-tg-hint">
                        {available ? (
                          <>
                            остаток {v.quantity}
                            {inCartQty > 0 && ` · в корзине ${inCartQty}`}
                          </>
                        ) : (
                          'нет в наличии'
                        )}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>,
          document.body
        )}
    </div>
  );
};
