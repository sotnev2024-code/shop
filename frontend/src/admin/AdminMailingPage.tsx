import React, { useState } from 'react';
import { Send } from 'lucide-react';
import { adminSendMailing } from '../api/endpoints';
import { Button } from '../components/ui/Button';

export const AdminMailingPage: React.FC = () => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ sent: number; failed: number; total: number } | null>(null);

  const handleSend = async () => {
    if (!text.trim()) return;
    if (!confirm('Отправить рассылку всем пользователям?')) return;

    setLoading(true);
    try {
      const { data } = await adminSendMailing(text);
      setResult(data);
      setText('');
    } catch {
      alert('Ошибка отправки');
    }
    setLoading(false);
  };

  return (
    <div>
      <h1 className="text-xl font-bold text-tg-text mb-4">Рассылка</h1>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">
            Текст рассылки
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none focus:ring-2 focus:ring-tg-button resize-none"
            placeholder="Введите текст рассылки..."
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





