import React, { useState } from 'react';
import { Trash2, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useBackButton } from '../hooks/useBackButton';

export const SettingsPage: React.FC = () => {
  useBackButton();
  const [cleared, setCleared] = useState(false);

  const handleClearCache = () => {
    // Clear all localStorage
    localStorage.clear();

    // Clear sessionStorage
    sessionStorage.clear();

    setCleared(true);

    // Reload after a short delay to show confirmation
    setTimeout(() => {
      window.location.reload();
    }, 1200);
  };

  return (
    <div className="pb-20">
      <div className="px-4 pt-4 pb-3">
        <h1 className="text-xl font-bold text-tg-text">Настройки</h1>
      </div>

      <div className="px-4">
        <div className="bg-tg-secondary rounded-2xl p-4">
          <h3 className="text-base font-medium text-tg-text mb-1">
            Очистить кэш
          </h3>
          <p className="text-sm text-tg-hint mb-4">
            Удалит сохранённые данные приложения. Это может помочь, если что-то
            работает некорректно.
          </p>

          {cleared ? (
            <div className="flex items-center gap-2 text-green-500">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm font-medium">Кэш очищен! Перезагрузка...</span>
            </div>
          ) : (
            <Button variant="danger" onClick={handleClearCache}>
              <Trash2 className="w-4 h-4 mr-2" />
              Очистить кэш
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};





