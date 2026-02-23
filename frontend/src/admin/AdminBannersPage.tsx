import React, { useEffect, useState } from 'react';
import { Plus, Trash2, Edit, Check, X } from 'lucide-react';
import {
  adminGetBanners,
  adminCreateBanner,
  adminUpdateBanner,
  adminDeleteBanner,
  adminUploadBannerImage,
} from '../api/endpoints';
import type { Banner } from '../types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const AdminBannersPage: React.FC = () => {
  const [banners, setBanners] = useState<Banner[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const [imageUrl, setImageUrl] = useState('');
  const [link, setLink] = useState('');
  const [sortOrder, setSortOrder] = useState('0');
  const [isActive, setIsActive] = useState(true);
  const [uploadingImage, setUploadingImage] = useState(false);

  const fetchBanners = () => {
    adminGetBanners().then(({ data }) => setBanners(data));
  };

  useEffect(() => {
    fetchBanners();
  }, []);

  const resetForm = () => {
    setImageUrl('');
    setLink('');
    setSortOrder('0');
    setIsActive(true);
    setShowForm(false);
    setEditingId(null);
  };

  const handleStartAdd = () => {
    resetForm();
    setShowForm(true);
  };

  const handleStartEdit = (b: Banner) => {
    setEditingId(b.id);
    setImageUrl(b.image_url);
    setLink(b.link || '');
    setSortOrder(String(b.sort_order));
    setIsActive(b.is_active);
    setShowForm(false);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    resetForm();
  };

  const handleCreate = async () => {
    if (!imageUrl.trim()) return;
    setLoading(true);
    try {
      await adminCreateBanner({
        image_url: imageUrl.trim(),
        link: link.trim() || null,
        sort_order: parseInt(sortOrder, 10) || 0,
        is_active: isActive,
      });
      resetForm();
      fetchBanners();
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (editingId == null || !imageUrl.trim()) return;
    setLoading(true);
    try {
      await adminUpdateBanner(editingId, {
        image_url: imageUrl.trim(),
        link: link.trim() || null,
        sort_order: parseInt(sortOrder, 10) || 0,
        is_active: isActive,
      });
      resetForm();
      fetchBanners();
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить баннер?')) return;
    setLoading(true);
    try {
      await adminDeleteBanner(id);
      fetchBanners();
      if (editingId === id) handleCancelEdit();
    } finally {
      setLoading(false);
    }
  };

  const handleBannerImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingImage(true);
    try {
      const { data } = await adminUploadBannerImage(file);
      setImageUrl(data.url);
    } finally {
      setUploadingImage(false);
      e.target.value = '';
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-tg-text">Баннеры</h1>
        <Button size="sm" onClick={handleStartAdd} disabled={loading}>
          <Plus className="w-4 h-4 mr-1" />
          Добавить
        </Button>
      </div>

      {showForm && (
        <div className="bg-tg-secondary rounded-2xl p-4 mb-4 space-y-3">
          <h2 className="text-base font-semibold text-tg-text">Новый баннер</h2>
          <div>
            <span className="block text-sm font-medium text-tg-hint mb-1">Фото баннера</span>
            <p className="text-xs text-tg-hint mb-2 p-2 rounded-lg bg-tg-bg/50">
              <strong>Формат:</strong> JPG, PNG, WebP или GIF (до 50 МБ).<br />
              <strong>Размер:</strong> зависит от настроек в «Настройки» → «Отображение баннеров». Рекомендуем загружать не меньше: прямоугольник — 360×240 px (соотношение 3∶2), квадрат — 280×280 px. Тогда изображение не обрежется на любом размере экрана.
            </p>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={handleBannerImageSelect}
              disabled={uploadingImage}
              className="block w-full text-sm text-tg-text file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-tg-bg file:text-tg-text"
            />
            {uploadingImage && <span className="text-xs text-tg-hint mt-1">Загрузка…</span>}
            {imageUrl && (
              <img
                src={imageUrl}
                alt=""
                className="mt-2 w-full max-w-xs h-24 object-cover rounded-lg bg-tg-bg"
              />
            )}
          </div>
          <Input
            label="Ссылка (необязательно)"
            value={link}
            onChange={(e) => setLink(e.target.value)}
            placeholder="https://... или оставьте пустым"
          />
          <Input
            label="Порядок"
            type="number"
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
          />
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="w-5 h-5 rounded"
            />
            <span className="text-sm text-tg-text">Активен (показывать в каталоге)</span>
          </label>
          <div className="flex gap-2">
            <Button onClick={handleCreate} disabled={!imageUrl.trim() || loading}>
              Создать
            </Button>
            <Button onClick={resetForm} disabled={loading}>
              Отмена
            </Button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {banners.map((b) => (
          <div key={b.id} className="bg-tg-secondary rounded-xl p-3 space-y-2">
            {editingId === b.id ? (
              <>
                <div>
                  <span className="block text-sm font-medium text-tg-hint mb-1">Фото баннера</span>
                  <p className="text-xs text-tg-hint mb-2 p-2 rounded-lg bg-tg-bg/50">
                    <strong>Формат:</strong> JPG, PNG, WebP или GIF (до 50 МБ). <strong>Размер:</strong> прямоугольник 360×240 px (3∶2), квадрат 280×280 px — см. «Настройки» → «Отображение баннеров».
                  </p>
                  {imageUrl && (
                    <img
                      src={imageUrl}
                      alt=""
                      className="mb-2 w-full max-w-xs h-24 object-cover rounded-lg bg-tg-bg"
                    />
                  )}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    onChange={handleBannerImageSelect}
                    disabled={uploadingImage}
                    className="block w-full text-sm text-tg-text file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-tg-bg file:text-tg-text"
                  />
                  {uploadingImage && <span className="text-xs text-tg-hint mt-1">Загрузка…</span>}
                </div>
                <Input
                  label="Ссылка"
                  value={link}
                  onChange={(e) => setLink(e.target.value)}
                />
                <Input
                  label="Порядок"
                  type="number"
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value)}
                />
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="w-5 h-5 rounded"
                  />
                  <span className="text-sm text-tg-text">Активен</span>
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={handleUpdate}
                    disabled={!imageUrl.trim() || loading}
                    className="w-8 h-8 rounded-lg bg-green-500 text-white flex items-center justify-center"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="w-8 h-8 rounded-lg bg-tg-bg text-tg-hint flex items-center justify-center"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-start gap-3">
                  <img
                    src={b.image_url}
                    alt=""
                    className="w-20 h-14 object-cover rounded-lg bg-tg-bg flex-shrink-0"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-xs text-tg-hint">
                      Порядок: {b.sort_order} {b.is_active ? '• Активен' : '• Скрыт'}
                    </div>
                    {b.link ? (
                      <div className="text-xs text-tg-link truncate mt-0.5" title={b.link}>
                        Ссылка: {b.link}
                      </div>
                    ) : (
                      <div className="text-xs text-tg-hint mt-0.5">Обычный баннер (без ссылки)</div>
                    )}
                  </div>
                  <div className="flex gap-1 flex-shrink-0">
                    <button
                      onClick={() => handleStartEdit(b)}
                      className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center"
                    >
                      <Edit className="w-4 h-4 text-tg-link" />
                    </button>
                    <button
                      onClick={() => handleDelete(b.id)}
                      disabled={loading}
                      className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        ))}
        {banners.length === 0 && !showForm && (
          <p className="text-center text-sm text-tg-hint py-4">Нет баннеров. Добавьте первый.</p>
        )}
      </div>
    </div>
  );
};
