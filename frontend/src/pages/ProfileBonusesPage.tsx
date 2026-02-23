import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Gift } from 'lucide-react';
import { getMe, getBonusTransactions } from '../api/endpoints';
import { useBackButton } from '../hooks/useBackButton';

const kindLabels: Record<string, string> = {
  welcome: 'Приветственные бонусы',
  purchase: 'Начисление за заказ',
  spend: 'Списание на заказ',
  refund: 'Возврат при отмене заказа',
};

export const ProfileBonusesPage: React.FC = () => {
  useBackButton();
  const navigate = useNavigate();
  const [balance, setBalance] = useState<number | null>(null);
  const [transactions, setTransactions] = useState<Array<{ id: number; amount: number; kind: string; order_id: number | null; created_at: string }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getMe(), getBonusTransactions({ limit: 50 })])
      .then(([meRes, txRes]) => {
        setBalance(meRes.data.bonus_balance);
        setTransactions(txRes.data.items);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-tg-bg text-tg-text pb-20">
      <div className="sticky top-0 bg-tg-bg border-b border-tg-secondary px-4 py-3 flex items-center gap-3">
        <button type="button" onClick={() => navigate('/profile')} className="p-1 -ml-1">
          <ArrowLeft className="w-6 h-6 text-tg-text" />
        </button>
        <h1 className="text-lg font-semibold">Бонусы</h1>
      </div>

      <div className="px-4 py-6">
        {loading ? (
          <p className="text-sm text-tg-hint">Загрузка…</p>
        ) : (
          <>
            <div className="flex items-center gap-3 p-4 rounded-2xl bg-tg-secondary mb-6">
              <div className="w-12 h-12 rounded-full bg-tg-button/20 flex items-center justify-center">
                <Gift className="w-6 h-6 text-tg-button" />
              </div>
              <div>
                <p className="text-sm text-tg-hint">Баланс бонусов</p>
                <p className="text-2xl font-bold text-tg-text">{balance != null ? balance.toLocaleString('ru-RU') : '0'}</p>
              </div>
            </div>

            <h2 className="text-sm font-semibold text-tg-hint mb-2">Последние операции</h2>
            {transactions.length === 0 ? (
              <p className="text-sm text-tg-hint">Пока нет операций по бонусам</p>
            ) : (
              <ul className="space-y-2">
                {transactions.map((tx) => (
                  <li key={tx.id} className="flex items-center justify-between py-3 px-4 rounded-xl bg-tg-secondary">
                    <div>
                      <p className="text-sm font-medium text-tg-text">{kindLabels[tx.kind] || tx.kind}</p>
                      <p className="text-xs text-tg-hint">{formatDate(tx.created_at)}</p>
                    </div>
                    <span className={`font-semibold ${tx.amount >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {tx.amount >= 0 ? '+' : ''}{tx.amount.toLocaleString('ru-RU')}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </div>
  );
};
