import React, { useState } from 'react';
import { Trash2, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useBackButton } from '../hooks/useBackButton';
import { usePreferencesStore } from '../store/preferencesStore';

export const SettingsPage: React.FC = () => {
  useBackButton();
  const [cleared, setCleared] = useState(false);
  const showVideosInCatalog = usePreferencesStore((s) => s.showVideosInCatalog);
  const setShowVideosInCatalog = usePreferencesStore((s) => s.setShowVideosInCatalog);

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

      <div className="px-4 space-y-4">
        <div className="bg-tg-secondary rounded-2xl p-4">
          <h3 className="text-base font-medium text-tg-text mb-1">
            Отображение каталога
          </h3>
          <p className="text-sm text-tg-hint mb-3">
            Показывать видео в карточках товаров
          </p>
          <div className="flex items-center gap-3">
            <button
              type="button"
              role="switch"
              aria-checked={showVideosInCatalog}
              onClick={() => setShowVideosInCatalog(!showVideosInCatalog)}
              className={`relative w-12 h-7 rounded-full transition-colors ${
                showVideosInCatalog ? 'bg-tg-button' : 'bg-tg-hint/30'
              }`}
            >
              <span
                className={`absolute top-1 left-1 w-5 h-5 rounded-full bg-white transition-transform ${
                  showVideosInCatalog ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
            <span className="text-sm text-tg-text">
              {showVideosInCatalog ? 'Включено' : 'Выключено'}
            </span>
          </div>
        </div>

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





