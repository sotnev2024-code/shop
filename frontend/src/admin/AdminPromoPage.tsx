import React, { useEffect, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { adminGetPromos, adminCreatePromo, adminDeletePromo } from '../api/endpoints';
import type { PromoCode } from '../types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const AdminPromoPage: React.FC = () => {
  const [promos, setPromos] = useState<PromoCode[]>([]);
  const [showForm, setShowForm] = useState(false);

  const [code, setCode] = useState('');
  const [discountType, setDiscountType] = useState('percent');
  const [discountValue, setDiscountValue] = useState('');
  const [maxUses, setMaxUses] = useState('');
  const [validUntil, setValidUntil] = useState('');
  const [firstOrderOnly, setFirstOrderOnly] = useState(false);

  const fetchPromos = () => {
    adminGetPromos().then(({ data }) => setPromos(data));
  };

  useEffect(() => {
    fetchPromos();
  }, []);

  const handleCreate = async () => {
    await adminCreatePromo({
      code,
      discount_type: discountType,
      discount_value: discountType === 'free_delivery' ? 0 : parseFloat(discountValue) || 0,
      min_order_amount: 0,
      max_uses: maxUses ? parseInt(maxUses) : null,
      valid_until: validUntil ? `${validUntil}T23:59:59` : null,
      is_active: true,
      first_order_only: firstOrderOnly,
    });
    setCode('');
    setDiscountValue('');
    setMaxUses('');
    setValidUntil('');
    setFirstOrderOnly(false);
    setShowForm(false);
    fetchPromos();
  };

  const handleDelete = async (id: number) => {
    if (confirm('Удалить промокод?')) {
      await adminDeletePromo(id);
      fetchPromos();
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-tg-text">Промокоды</h1>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Plus className="w-4 h-4 mr-1" />
          Создать
        </Button>
      </div>

      {showForm && (
        <div className="bg-tg-secondary rounded-2xl p-4 mb-4 space-y-3">
          <Input label="Код" value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-tg-hint mb-1">Тип</label>
              <select
                value={discountType}
                onChange={(e) => setDiscountType(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-tg-bg text-tg-text border-none outline-none"
              >
                <option value="percent">Процент (%)</option>
                <option value="fixed">Фикс. сумма (₽)</option>
                <option value="free_delivery">Бесплатная доставка</option>
              </select>
            </div>
            {discountType !== 'free_delivery' && (
              <Input
                label="Значение"
                type="number"
                value={discountValue}
                onChange={(e) => setDiscountValue(e.target.value)}
              />
            )}
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={firstOrderOnly}
              onChange={(e) => setFirstOrderOnly(e.target.checked)}
              className="w-5 h-5 rounded"
            />
            <span className="text-sm text-tg-text">Только для первого заказа</span>
          </label>
          <Input
            label="Макс. использований (пусто = безлимит)"
            type="number"
            value={maxUses}
            onChange={(e) => setMaxUses(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-tg-hint mb-1">Действует до (дата)</label>
            <input
              type="date"
              value={validUntil}
              onChange={(e) => setValidUntil(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-tg-bg text-tg-text border-none outline-none"
            />
            <p className="text-xs text-tg-hint mt-0.5">Оставьте пустым — без срока</p>
          </div>
          <Button
            onClick={handleCreate}
            disabled={!code || (discountType !== 'free_delivery' && !discountValue)}
          >
            Создать
          </Button>
        </div>
      )}

      <div className="space-y-2">
        {promos.map((p) => (
          <div key={p.id} className="bg-tg-secondary rounded-xl p-3 flex items-center justify-between">
            <div>
              <div className="text-sm font-bold text-tg-text font-mono">{p.code}</div>
              <div className="text-xs text-tg-hint">
                {p.discount_type === 'free_delivery'
                  ? 'Бесплатная доставка'
                  : p.discount_type === 'percent'
                    ? `${p.discount_value}%`
                    : `${p.discount_value} ₽`}
                {p.first_order_only && ' • 1-й заказ'}
                {p.valid_until && ` • до ${new Date(p.valid_until).toLocaleDateString('ru-RU')}`}
                {' • '}
                Исп: {p.used_count}{p.max_uses ? `/${p.max_uses}` : ''}
              </div>
            </div>
            <button
              onClick={() => handleDelete(p.id)}
              className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center"
            >
              <Trash2 className="w-4 h-4 text-red-500" />
            </button>
          </div>
        ))}
        {promos.length === 0 && (
          <p className="text-center text-sm text-tg-hint py-4">Нет промокодов</p>
        )}
      </div>
    </div>
  );
};





