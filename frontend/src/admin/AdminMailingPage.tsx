import React, { useState, useRef } from 'react';
import { Send, Upload, X } from 'lucide-react';
import {
  adminSendMailing,
  adminUploadMailingImage,
  type MailingAudience,
  type MailingPayload,
} from '../api/endpoints';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';

const AUDIENCE_OPTIONS: { value: MailingAudience; label: string }[] = [
  { value: 'all', label: 'Все пользователи' },
  { value: 'has_orders', label: 'Делали заказы' },
  { value: 'has_cart', label: 'Есть в корзине' },
  { value: 'has_favorites', label: 'Есть в избранном' },
  { value: 'no_orders', label: 'Не делали заказов' },
];

export const AdminMailingPage: React.FC = () => {
  const [name, setName] = useState('');
  const [audience, setAudience] = useState<MailingAudience>('all');
  const [text, setText] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [buttonText, setButtonText] = useState('');
  const [buttonUrl, setButtonUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ sent: number; failed: number; total: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !file.type.startsWith('image/')) return;
    setUploading(true);
    try {
      const { data } = await adminUploadMailingImage(file);
      setImageUrl(data.url);
    } catch {
      alert('Ошибка загрузки изображения');
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSend = async () => {
    if (!text.trim()) return;
    const confirmMsg = `Отправить рассылку "${name || 'Без названия'}" выбранной аудитории (${AUDIENCE_OPTIONS.find((o) => o.value === audience)?.label})?`;
    if (!confirm(confirmMsg)) return;

    setLoading(true);
    setResult(null);
    try {
      const payload: MailingPayload = {
        name: name.trim() || undefined,
        audience,
        text: text.trim(),
        image_url: imageUrl || undefined,
        button_text: buttonText.trim() || undefined,
        button_url: buttonUrl.trim() || undefined,
      };
      const { data } = await adminSendMailing(payload);
      setResult(data);
      setText('');
      setName('');
      setImageUrl('');
      setButtonText('');
      setButtonUrl('');
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'Ошибка отправки';
      alert(msg);
    }
    setLoading(false);
  };

  return (
    <div>
      <h1 className="text-xl font-bold text-tg-text mb-4">Рассылка</h1>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Название рассылки</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Необязательно"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">
            Кому отправить
          </label>
          <select
            value={audience}
            onChange={(e) => setAudience(e.target.value as MailingAudience)}
            className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none focus:ring-2 focus:ring-tg-button"
          >
            {AUDIENCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Текст сообщения *</label>
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            placeholder="Введите текст рассылки..."
            className="resize-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Изображение</label>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            onChange={handleImageSelect}
            className="hidden"
          />
          {imageUrl ? (
            <div className="flex items-center gap-2">
              <img
                src={imageUrl.startsWith('http') ? imageUrl : `${window.location.origin}${imageUrl}`}
                alt="Превью"
                className="h-20 w-20 object-cover rounded-lg"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={() => setImageUrl('')}
                className="shrink-0"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <Button
              type="button"
              variant="secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              <Upload className="w-4 h-4 mr-2" />
              {uploading ? 'Загрузка...' : 'Загрузить изображение'}
            </Button>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Текст кнопки</label>
          <Input
            value={buttonText}
            onChange={(e) => setButtonText(e.target.value)}
            placeholder="Необязательно"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">
            Ссылка кнопки
          </label>
          <Input
            value={buttonUrl}
            onChange={(e) => setButtonUrl(e.target.value)}
            placeholder="По умолчанию — ссылка на магазин"
          />
        </div>

        <Button onClick={handleSend} disabled={loading || !text.trim()} fullWidth>
          <Send className="w-4 h-4 mr-2" />
          {loading ? 'Отправка...' : 'Отправить рассылку'}
        </Button>

        {result && (
          <div className="bg-tg-secondary rounded-xl p-4 text-sm">
            <p className="text-green-600">Успешно: {result.sent}</p>
            <p className="text-red-500">Ошибки: {result.failed}</p>
            <p className="text-tg-hint">Всего: {result.total}</p>
          </div>
        )}
      </div>
    </div>
  );
};
