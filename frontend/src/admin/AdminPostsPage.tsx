import React, { useEffect, useState, useRef } from 'react';
import { Send, Upload, X } from 'lucide-react';
import {
  adminGetPosts,
  adminCreatePost,
  adminSendPost,
  adminUploadPostImage,
  adminGetProducts,
  adminGetSettings,
} from '../api/endpoints';
import type { AdminPost, Product } from '../types';
import { useConfigStore } from '../store/configStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';

const BUTTON_COLORS = [
  { value: 'blue', label: 'Синий', class: 'bg-blue-500' },
  { value: 'green', label: 'Зелёный', class: 'bg-green-500' },
  { value: 'red', label: 'Красный', class: 'bg-red-500' },
  { value: 'gray', label: 'Серый', class: 'bg-gray-500' },
] as const;

const resolveImageUrl = (url: string | null): string => {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  return `${window.location.origin}${url}`;
};

const buildProductDeeplink = (productId: number): string => {
  const botUsername = useConfigStore.getState().config?.bot_username;
  if (!botUsername) return `/product/${productId}`;
  return `https://t.me/${botUsername}?start=product_${productId}`;
};

export const AdminPostsPage: React.FC = () => {
  const config = useConfigStore((s) => s.config);
  const [posts, setPosts] = useState<AdminPost[]>([]);
  const [total, setTotal] = useState(0);
  const [postsPage, setPostsPage] = useState(0);
  const [postsLoading, setPostsLoading] = useState(true);
  const [channelId, setChannelId] = useState<string | null>(null);

  // Form state
  const [text, setText] = useState('');
  const [productId, setProductId] = useState<number | ''>('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [photoUrl, setPhotoUrl] = useState('');
  const [useProductPhoto, setUseProductPhoto] = useState(true);
  const [buttonText, setButtonText] = useState('');
  const [buttonUrl, setButtonUrl] = useState('');
  const [buttonColor, setButtonColor] = useState<string>('blue');

  const [products, setProducts] = useState<Product[]>([]);
  const [productSearch, setProductSearch] = useState('');
  const [productsLoading, setProductsLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [sendModal, setSendModal] = useState<AdminPost | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const lastAutoFilledProductId = useRef<number | null>(null);

  const fetchPosts = () => {
    setPostsLoading(true);
    adminGetPosts({ skip: postsPage * 20, limit: 20 })
      .then(({ data }) => {
        setPosts(data.items);
        setTotal(data.total);
      })
      .finally(() => setPostsLoading(false));
  };

  useEffect(() => {
    fetchPosts();
  }, [postsPage]);

  useEffect(() => {
    adminGetSettings().then(({ data }: any) => {
      setChannelId(data.channel_id || null);
    });
  }, []);

  // Product search
  useEffect(() => {
    if (!productSearch.trim()) {
      setProducts([]);
      return;
    }
    setProductsLoading(true);
    const t = setTimeout(() => {
      adminGetProducts({ search: productSearch.trim(), per_page: 20 })
        .then(({ data }) => setProducts(data.items))
        .finally(() => setProductsLoading(false));
    }, 300);
    return () => clearTimeout(t);
  }, [productSearch]);

  // When product selected - sync from products list
  useEffect(() => {
    if (!productId || typeof productId !== 'number') {
      setSelectedProduct(null);
      lastAutoFilledProductId.current = null;
      return;
    }
    const p = products.find((x) => x.id === productId);
    if (p) {
      setSelectedProduct(p);
      if (useProductPhoto) {
        const img = p.media?.find((m) => m.media_type === 'image');
        const url = img?.url ?? p.image_url;
        setPhotoUrl(url ? (url.startsWith('http') ? url : `${window.location.origin}${url}`) : '');
      }
      if (lastAutoFilledProductId.current !== p.id) {
        lastAutoFilledProductId.current = p.id;
        setButtonText('Перейти к товару');
        setButtonUrl(buildProductDeeplink(p.id));
      }
    }
  }, [productId, products, useProductPhoto]);

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !file.type.startsWith('image/')) return;
    setSaving(true);
    try {
      const { data } = await adminUploadPostImage(file);
      setPhotoUrl(data.url);
      setUseProductPhoto(false);
    } catch {
      alert('Ошибка загрузки изображения');
    }
    setSaving(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleCreate = async () => {
    setSaving(true);
    try {
      await adminCreatePost({
        text: text.trim(),
        product_id: productId ? Number(productId) : null,
        photo_url: !useProductPhoto && photoUrl ? photoUrl : undefined,
        button_text: buttonText.trim() || undefined,
        button_url: buttonUrl.trim() || undefined,
        button_color: buttonColor || undefined,
      });
      fetchPosts();
      setText('');
      setProductId('');
      setSelectedProduct(null);
      setPhotoUrl('');
      setButtonText('');
      setButtonUrl('');
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'Ошибка создания';
      alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    setSaving(false);
  };

  const handleSend = async (post: AdminPost) => {
    setSending(true);
    try {
      await adminSendPost(post.id);
      setSendModal(null);
      fetchPosts();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'Ошибка отправки';
      alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    setSending(false);
  };

  const displayPhotoUrl = photoUrl || (useProductPhoto && selectedProduct
    ? (selectedProduct.media?.find((m) => m.media_type === 'image')?.url
      ? resolveImageUrl(selectedProduct.media!.find((m) => m.media_type === 'image')!.url)
      : resolveImageUrl(selectedProduct.image_url))
    : '');

  const displayButtonUrl = buttonUrl || (selectedProduct ? buildProductDeeplink(selectedProduct.id) : '');
  const displayButtonText = buttonText || 'Перейти к товару';

  const colorClass = BUTTON_COLORS.find((c) => c.value === buttonColor)?.class ?? 'bg-blue-500';

  return (
    <div>
      <h1 className="text-xl font-bold text-tg-text mb-4">Посты в канал</h1>

      {/* Create form */}
      <div className="space-y-4 mb-8">
        <h2 className="text-base font-semibold text-tg-text">Новый пост</h2>
        <Textarea
          label="Описание"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={4}
          placeholder="Текст поста..."
        />

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Товар</label>
          <Input
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
            placeholder="Поиск по названию..."
          />
          {products.length > 0 && (
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value ? Number(e.target.value) : '')}
              className="mt-2 w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
            >
              <option value="">— Не выбран —</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {selectedProduct && (
          <div className="flex gap-3 p-3 rounded-xl bg-tg-secondary">
            {(displayPhotoUrl || selectedProduct.image_url) && (
              <img
                src={displayPhotoUrl || resolveImageUrl(selectedProduct.image_url)}
                alt=""
                className="w-16 h-16 object-cover rounded-lg"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-tg-text truncate">{selectedProduct.name}</p>
              <p className="text-xs text-tg-hint mt-1">Ссылка: {displayButtonUrl}</p>
            </div>
          </div>
        )}

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={useProductPhoto}
            onChange={(e) => setUseProductPhoto(e.target.checked)}
            className="w-5 h-5 rounded"
          />
          <span className="text-sm text-tg-text">Использовать фото товара автоматически</span>
        </label>

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Изображение</label>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            onChange={handleImageSelect}
            className="hidden"
          />
          {photoUrl && !useProductPhoto && (
            <div className="flex items-center gap-2">
              <img
                src={resolveImageUrl(photoUrl)}
                alt="Превью"
                className="h-20 w-20 object-cover rounded-lg"
              />
              <Button type="button" variant="secondary" onClick={() => setPhotoUrl('')} className="shrink-0">
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}
          {(!photoUrl || useProductPhoto) && (
            <Button
              type="button"
              variant="secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={saving}
            >
              <Upload className="w-4 h-4 mr-2" />
              Загрузить своё изображение
            </Button>
          )}
        </div>

        <Input
          label="Текст кнопки"
          value={buttonText}
          onChange={(e) => setButtonText(e.target.value)}
          placeholder="Перейти к товару"
        />
        <Input
          label="URL кнопки"
          value={buttonUrl}
          onChange={(e) => setButtonUrl(e.target.value)}
          placeholder="Deep-link (авто при выборе товара)"
        />
        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Цвет кнопки</label>
          <div className="flex gap-2">
            {BUTTON_COLORS.map((c) => (
              <button
                key={c.value}
                type="button"
                onClick={() => setButtonColor(c.value)}
                className={`w-8 h-8 rounded-full ${c.class} ${buttonColor === c.value ? 'ring-2 ring-offset-2 ring-tg-button' : ''}`}
                title={c.label}
              />
            ))}
          </div>
        </div>

        <Button onClick={handleCreate} disabled={saving} fullWidth>
          {saving ? 'Сохранение...' : 'Создать черновик'}
        </Button>
      </div>

      {/* Preview */}
      <div className="mb-8 p-4 rounded-xl bg-tg-secondary">
        <h3 className="text-sm font-medium text-tg-hint mb-3">Превью</h3>
        <div className="max-w-sm rounded-xl overflow-hidden bg-white text-black shadow">
          {displayPhotoUrl && (
            <img src={resolveImageUrl(displayPhotoUrl)} alt="" className="w-full aspect-video object-cover" />
          )}
          <div className="p-3">
            <p className="text-sm whitespace-pre-wrap">{text || '(пусто)'}</p>
            {displayButtonText && displayButtonUrl && (
              <a
                href={displayButtonUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={`mt-2 inline-block px-4 py-2 rounded-lg text-white text-sm font-medium ${colorClass}`}
              >
                {displayButtonText}
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Posts list */}
      <h2 className="text-base font-semibold text-tg-text mb-3">Черновики и отправленные</h2>
      {postsLoading ? (
        <p className="text-tg-hint">Загрузка...</p>
      ) : posts.length === 0 ? (
        <p className="text-tg-hint">Нет постов</p>
      ) : (
        <div className="space-y-2">
          {posts.map((post) => (
            <div
              key={post.id}
              className="p-4 rounded-xl bg-tg-secondary flex items-center justify-between gap-3"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm text-tg-text truncate">{post.text || '(без текста)'}</p>
                <p className="text-xs text-tg-hint mt-1">
                  {post.sent_at ? `Отправлен ${new Date(post.sent_at).toLocaleString()}` : 'Черновик'}
                </p>
              </div>
              {!post.sent_at && (
                <Button
                  size="small"
                  onClick={() => setSendModal(post)}
                  disabled={sending}
                >
                  <Send className="w-4 h-4 mr-1" />
                  Отправить
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {total > 20 && (
        <div className="flex gap-2 mt-4">
          <Button
            variant="secondary"
            disabled={postsPage === 0}
            onClick={() => setPostsPage((p) => p - 1)}
          >
            Назад
          </Button>
          <Button
            variant="secondary"
            disabled={postsPage >= Math.ceil(total / 20) - 1}
            onClick={() => setPostsPage((p) => p + 1)}
          >
            Вперёд
          </Button>
        </div>
      )}

      {/* Send confirmation modal */}
      {sendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => !sending && setSendModal(null)}>
          <div className="bg-tg-bg rounded-xl p-4 max-w-sm w-full" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-tg-text mb-2">Отправить пост?</h3>
            <p className="text-sm text-tg-hint mb-4">
              Отправить в канал <strong>{channelId || 'не настроен'}</strong>?
            </p>
            <div className="p-3 rounded-lg bg-tg-secondary mb-4 text-sm text-tg-text max-h-24 overflow-y-auto">
              {sendModal.text || '(пусто)'}
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setSendModal(null)} disabled={sending} className="flex-1">
                Отмена
              </Button>
              <Button onClick={() => handleSend(sendModal)} disabled={sending} className="flex-1">
                {sending ? 'Отправка...' : 'Отправить'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
