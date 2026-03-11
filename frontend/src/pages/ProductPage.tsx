import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Heart, Minus, Plus, ShoppingCart, Check, Share2 } from 'lucide-react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Pagination } from 'swiper/modules';
import 'swiper/css';
import 'swiper/css/pagination';
import { getProduct, getProducts } from '../api/endpoints';
import type { Product, ProductMedia } from '../types';
import { useCartStore } from '../store/cartStore';
import { useFavoritesStore } from '../store/favoritesStore';
import { useConfigStore } from '../store/configStore';
import { usePreferencesStore } from '../store/preferencesStore';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { ProductCard } from '../components/ProductCard';
import { useBackButton } from '../hooks/useBackButton';

export const ProductPage: React.FC = () => {
  useBackButton();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const config = useConfigStore((s) => s.config);
  const [product, setProduct] = useState<Product | null>(null);
  const [relatedProducts, setRelatedProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [justAdded, setJustAdded] = useState(false);
  const [selectedVariantValue, setSelectedVariantValue] = useState<string | null>(null);

  const addItem = useCartStore((s) => s.addItem);
  const updateItem = useCartStore((s) => s.updateItem);
  const cartItems = useCartStore((s) => s.items);
  const getCartItemByProductId = useCartStore((s) => s.getCartItemByProductId);
  const toggleFav = useFavoritesStore((s) => s.toggle);
  const showVideosInCatalog = usePreferencesStore((s) => s.showVideosInCatalog);

  const hasVariants = Boolean(product?.variants?.length && product?.modification_type);
  const cartItem = product
    ? hasVariants
      ? getCartItemByProductId(product.id, product.modification_type!.id, selectedVariantValue)
      : cartItems.find((item) => item.product_id === product.id && item.modification_type_id == null)
    : undefined;
  const inCart = !!cartItem;

  // Build sorted media list: videos first, then images; filter videos if setting disabled
  const mediaList = useMemo<ProductMedia[]>(() => {
    if (!product) return [];
    let items: ProductMedia[];
    if (product.media && product.media.length > 0) {
      items = [...product.media].sort((a, b) => a.sort_order - b.sort_order);
    } else if (product.image_url) {
      items = [{ id: 0, media_type: 'image', url: product.image_url, sort_order: 0 }];
    } else {
      return [];
    }
    if (!showVideosInCatalog) {
      const filtered = items.filter((m) => m.media_type !== 'video');
      if (filtered.length === 0 && product.image_url) {
        return [{ id: 0, media_type: 'image', url: product.image_url, sort_order: 0 }];
      }
      return filtered;
    }
    return items;
  }, [product, showVideosInCatalog]);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getProduct(Number(id))
      .then(({ data }) => {
        setProduct(data);
        // Fetch related products from same category
        if (data.category_id) {
          getProducts({
            category_id: data.category_id,
            per_page: 10,
            sort_by: 'created_at',
            sort_order: 'desc',
          }).then(({ data: listData }) => {
            setRelatedProducts(listData.items.filter((p) => p.id !== data.id));
          }).catch(() => {});
        }
      })
      .catch(() => navigate('/'))
      .finally(() => setLoading(false));
  }, [id, navigate]);

  const handleAddToCart = async () => {
    if (!product) return;
    if (hasVariants) {
      if (!selectedVariantValue) {
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('warning');
        window.Telegram?.WebApp?.showAlert?.('Выберите вариант');
        return;
      }
      const variant = product.variants!.find((v) => v.value === selectedVariantValue);
      if (!variant || variant.quantity <= 0) {
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
        window.Telegram?.WebApp?.showAlert?.('Этого варианта нет в наличии');
        return;
      }
    } else {
      if (product.stock_quantity <= 0) {
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
        window.Telegram?.WebApp?.showAlert?.('Товар закончился на складе');
        return;
      }
    }
    if (inCart) {
      navigate('/cart');
      return;
    }
    try {
      if (hasVariants && product.modification_type && selectedVariantValue) {
        await addItem(product.id, quantity, product.modification_type.id, selectedVariantValue);
      } else {
        await addItem(product.id, quantity);
      }
      setJustAdded(true);
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
      setTimeout(() => setJustAdded(false), 2000);
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  const handleCartQtyChange = async (delta: number) => {
    if (!cartItem) return;
    const newQty = cartItem.quantity + delta;
    await updateItem(cartItem.id, newQty);
  };

  const handleToggleFav = async () => {
    if (!product) return;
    await toggleFav(product.id, isProductFavorite, product);
    setProduct((prev) => prev ? { ...prev, is_favorite: !isProductFavorite } : prev);
  };

  const handleShare = () => {
    if (!product) return;
    const botUsername = config?.bot_username;
    if (!botUsername) {
      window.Telegram?.WebApp?.showAlert?.('Функция поделиться временно недоступна');
      return;
    }

    const shareUrl = `https://t.me/${botUsername}?start=product_${product.id}`;
    const shareText = `${product.name}\n💰 ${product.price.toLocaleString('ru-RU')} ₽\n\n${shareUrl}`;

    const shareTelegramUrl = `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(product.name + ' — ' + product.price.toLocaleString('ru-RU') + ' ₽')}`;
    try {
      if (window.Telegram?.WebApp?.openTelegramLink) {
        window.Telegram.WebApp.openTelegramLink(shareTelegramUrl);
      } else {
        window.open(shareTelegramUrl, '_blank');
      }
    } catch {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(shareText).then(() => {
          window.Telegram?.WebApp?.showAlert?.('Ссылка скопирована!');
        });
      }
    }
  };

  const productId = product?.id ?? -1;
  const isProductFavorite = useFavoritesStore((s) => s.items.some((item) => item.id === productId));

  if (loading) {
    return (
      <div className="pb-20">
        <Skeleton className="w-full aspect-square" />
        <div className="p-4 space-y-3">
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    );
  }

  if (!product) return null;

  return (
    <div className="pb-24">
      {/* Media Gallery — z-0 чтобы кнопка «назад» и прочие элементы были поверх слайдера */}
      <div className="relative z-0">
        {mediaList.length > 1 ? (
          <Swiper
            modules={[Pagination]}
            pagination={{ clickable: true }}
            spaceBetween={0}
            slidesPerView={1}
            className="w-full aspect-square product-page-swiper"
          >
            {mediaList.map((m) => (
              <SwiperSlide key={m.id}>
                {m.media_type === 'video' ? (
                  <video
                    src={m.url}
                    autoPlay
                    muted
                    loop
                    playsInline
                    controls
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <img
                    src={m.url}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                )}
              </SwiperSlide>
            ))}
          </Swiper>
        ) : mediaList.length === 1 ? (
          <div className="aspect-square bg-gray-100">
            {mediaList[0].media_type === 'video' ? (
              <video
                src={mediaList[0].url}
                autoPlay
                muted
                loop
                playsInline
                controls
                className="w-full h-full object-cover"
              />
            ) : (
              <img
                src={mediaList[0].url}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            )}
          </div>
        ) : (
          <div className="aspect-square bg-gray-100 flex items-center justify-center text-6xl">
            📦
          </div>
        )}

        <button
          onClick={() => navigate(-1)}
          className="absolute top-4 left-4 w-10 h-10 rounded-full bg-white/80 backdrop-blur flex items-center justify-center z-10"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>

        <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
          <button
            onClick={handleToggleFav}
            className="w-10 h-10 rounded-full bg-white/80 backdrop-blur flex items-center justify-center transition-transform active:scale-90"
          >
            <Heart
              className={`w-5 h-5 transition-colors ${
                isProductFavorite ? 'fill-red-500 text-red-500' : 'text-gray-500'
              }`}
            />
          </button>
          <button
            onClick={handleShare}
            className="w-10 h-10 rounded-full bg-white/80 backdrop-blur flex items-center justify-center transition-transform active:scale-90"
          >
            <Share2 className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {product.old_price && (
          <div className="absolute bottom-4 left-4 bg-red-500 text-white text-sm px-3 py-1 rounded-full font-medium z-10">
            -{Math.round((1 - product.price / product.old_price) * 100)}%
          </div>
        )}

        {/* Media counter */}
        {mediaList.length > 1 && (
          <div className="absolute top-4 left-16 bg-black/50 text-white text-xs px-2 py-1 rounded-full z-10">
            {mediaList.length} фото
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-1">
          {product.category && (
            <span className="text-xs text-tg-link bg-tg-secondary px-2 py-0.5 rounded-full">
              {product.category.name}
            </span>
          )}
          {!hasVariants && product.stock_quantity <= 0 && (
            <span className="text-xs text-red-500 bg-red-50 px-2 py-0.5 rounded-full">
              Нет в наличии
            </span>
          )}
          {hasVariants && !product.variants!.some((v) => v.quantity > 0) && (
            <span className="text-xs text-red-500 bg-red-50 px-2 py-0.5 rounded-full">
              Нет в наличии
            </span>
          )}
        </div>

        <h1 className="text-xl font-bold text-tg-text mb-2">{product.name}</h1>

        <div className="flex items-baseline gap-2 mb-4">
          <span className="text-2xl font-bold text-tg-text">
            {product.price.toLocaleString('ru-RU')} ₽
          </span>
          {product.old_price && (
            <span className="text-base text-tg-hint line-through">
              {product.old_price.toLocaleString('ru-RU')} ₽
            </span>
          )}
        </div>

        {product.description && (
          <p className="text-sm text-tg-hint leading-relaxed mb-6 whitespace-pre-wrap">
            {product.description}
          </p>
        )}

        {/* Variant selector: in stock = white, out of stock = gray */}
        {hasVariants && product.modification_type && product.variants && (
          <div className="mb-4">
            <span className="text-sm text-tg-hint block mb-2">{product.modification_type.name}:</span>
            <div className="flex flex-wrap gap-2">
              {product.variants.map((v) => {
                const inStock = v.quantity > 0;
                const isSelected = selectedVariantValue === v.value;
                return (
                  <button
                    key={v.value}
                    type="button"
                    onClick={() => setSelectedVariantValue(v.value)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                      inStock
                        ? isSelected
                          ? 'bg-tg-button text-tg-button-text'
                          : 'bg-tg-secondary text-tg-text'
                        : 'bg-tg-secondary text-tg-hint cursor-default opacity-70'
                    }`}
                  >
                    {v.value}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Quantity selector (only if not already in cart) */}
        {!inCart && (
          <div className="flex items-center gap-4 mb-4">
            <span className="text-sm text-tg-hint">Количество:</span>
            <div className="flex items-center gap-3 bg-tg-secondary rounded-full px-1">
              <button
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="w-8 h-8 rounded-full flex items-center justify-center"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="text-base font-medium min-w-[24px] text-center">{quantity}</span>
              <button
                onClick={() => setQuantity((q) => q + 1)}
                className="w-8 h-8 rounded-full flex items-center justify-center"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* In-cart quantity controls */}
        {inCart && !justAdded && (
          <div className="flex items-center gap-4 mb-4">
            <span className="text-sm text-tg-hint">В корзине:</span>
            <div className="flex items-center gap-3 bg-tg-button rounded-full px-1">
              <button
                onClick={() => handleCartQtyChange(-1)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-tg-button-text"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="text-base font-medium min-w-[24px] text-center text-tg-button-text">
                {cartItem.quantity}
              </span>
              <button
                onClick={() => handleCartQtyChange(1)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-tg-button-text"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Related Products */}
      {relatedProducts.length > 0 && (
        <div className="px-4 pb-4">
          <h2 className="text-lg font-bold text-tg-text mb-3">Похожие товары</h2>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-none">
            {relatedProducts.slice(0, 8).map((rp) => (
              <div key={rp.id} className="flex-shrink-0 w-[160px]">
                <ProductCard product={rp} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fixed bottom button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-tg-bg border-t border-tg-secondary">
        {justAdded ? (
          <Button fullWidth size="lg" className="bg-green-500 hover:bg-green-500">
            <Check className="w-5 h-5 mr-2" />
            Добавлено в корзину!
          </Button>
        ) : inCart ? (
          <Button
            onClick={() => navigate('/cart')}
            fullWidth
            size="lg"
          >
            <ShoppingCart className="w-5 h-5 mr-2" />
            Перейти в корзину ({cartItem.quantity})
          </Button>
        ) : (
          <Button
            onClick={handleAddToCart}
            fullWidth
            size="lg"
            disabled={
              hasVariants
                ? !selectedVariantValue || (product.variants!.find((v) => v.value === selectedVariantValue)?.quantity ?? 0) <= 0
                : product.stock_quantity <= 0
            }
          >
            <ShoppingCart className="w-5 h-5 mr-2" />
            В корзину — {(product.price * quantity).toLocaleString('ru-RU')} ₽
          </Button>
        )}
      </div>
    </div>
  );
};
