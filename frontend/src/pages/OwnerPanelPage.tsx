import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  Database,
  CreditCard,
  Truck,
  Map,
  Link,
  Clock,
  Tag,
  Send,
  Package,
  Eye,
  EyeOff,
  ShoppingCart,
} from 'lucide-react';
import { ownerGetConfig, ownerUpdateConfig } from '../api/endpoints';
import type { OwnerConfig } from '../types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useBackButton } from '../hooks/useBackButton';

export const OwnerPanelPage: React.FC = () => {
  useBackButton();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  // Config state
  const [checkoutType, setCheckoutType] = useState('basic');
  const [productSource, setProductSource] = useState('database');
  const [promoEnabled, setPromoEnabled] = useState(true);
  const [mailingEnabled, setMailingEnabled] = useState(true);
  const [deliveryEnabled, setDeliveryEnabled] = useState(false);
  const [pickupEnabled, setPickupEnabled] = useState(true);

  // Delivery services
  const [sdekEnabled, setSdekEnabled] = useState(false);
  const [pochtaEnabled, setPochtaEnabled] = useState(false);
  const [yandexDeliveryEnabled, setYandexDeliveryEnabled] = useState(false);

  // Integration keys
  const [moyskladToken, setMoyskladToken] = useState('');
  const [oneCEndpoint, setOneCEndpoint] = useState('');
  const [oneCLogin, setOneCLogin] = useState('');
  const [oneCPassword, setOneCPassword] = useState('');
  const [paymentToken, setPaymentToken] = useState('');
  const [yandexMapsKey, setYandexMapsKey] = useState('');
  const [supportLink, setSupportLink] = useState('');
  const [syncInterval, setSyncInterval] = useState('15');

  // Visibility toggles for secrets
  const [showMoysklad, setShowMoysklad] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  const [showOneCPassword, setShowOneCPassword] = useState(false);
  const [showYandexMaps, setShowYandexMaps] = useState(false);

  useEffect(() => {
    ownerGetConfig()
      .then(({ data }) => {
        setCheckoutType(data.checkout_type);
        setProductSource(data.product_source);
        setPromoEnabled(data.promo_enabled);
        setMailingEnabled(data.mailing_enabled);
        setDeliveryEnabled(data.delivery_enabled);
        setPickupEnabled(data.pickup_enabled);
        setSdekEnabled(data.delivery_sdek_enabled);
        setPochtaEnabled(data.delivery_pochta_enabled);
        setYandexDeliveryEnabled(data.delivery_yandex_enabled);
        setMoyskladToken(data.moysklad_token || '');
        setOneCEndpoint(data.one_c_endpoint || '');
        setOneCLogin(data.one_c_login || '');
        setOneCPassword(data.one_c_password || '');
        setPaymentToken(data.payment_provider_token || '');
        setYandexMapsKey(data.yandex_maps_key || '');
        setSupportLink(data.support_link || '');
        setSyncInterval(String(data.sync_interval_minutes));
      })
      .catch(() => {
        setError('Нет доступа к настройкам платформы');
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      const update: Partial<OwnerConfig> = {
        checkout_type: checkoutType,
        product_source: productSource,
        promo_enabled: promoEnabled,
        mailing_enabled: mailingEnabled,
        delivery_enabled: deliveryEnabled,
        pickup_enabled: pickupEnabled,
        delivery_sdek_enabled: sdekEnabled,
        delivery_pochta_enabled: pochtaEnabled,
        delivery_yandex_enabled: yandexDeliveryEnabled,
        support_link: supportLink || null,
        sync_interval_minutes: parseInt(syncInterval) || 15,
      };

      // Only send secrets if they were changed (don't contain mask chars)
      if (moyskladToken && !moyskladToken.includes('*')) {
        update.moysklad_token = moyskladToken;
      }
      if (oneCEndpoint) update.one_c_endpoint = oneCEndpoint;
      if (oneCLogin) update.one_c_login = oneCLogin;
      if (oneCPassword && !oneCPassword.includes('*')) {
        update.one_c_password = oneCPassword;
      }
      if (paymentToken && !paymentToken.includes('*')) {
        update.payment_provider_token = paymentToken;
      }
      if (yandexMapsKey && !yandexMapsKey.includes('*')) {
        update.yandex_maps_key = yandexMapsKey;
      }

      const { data } = await ownerUpdateConfig(update);

      // Update local state with response (masked values)
      setMoyskladToken(data.moysklad_token || '');
      setOneCEndpoint(data.one_c_endpoint || '');
      setOneCLogin(data.one_c_login || '');
      setOneCPassword(data.one_c_password || '');
      setPaymentToken(data.payment_provider_token || '');
      setYandexMapsKey(data.yandex_maps_key || '');

      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Ошибка сохранения');
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin w-10 h-10 border-4 border-tg-button border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error && !saving) {
    return (
      <div className="p-4">
        <div className="flex items-center gap-3 mb-4">
          <button onClick={() => navigate(-1)}>
            <ArrowLeft className="w-6 h-6 text-tg-text" />
          </button>
          <h1 className="text-xl font-bold text-tg-text">Настройки платформы</h1>
        </div>
        <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm">{error}</div>
      </div>
    );
  }

  return (
    <div className="pb-24">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 flex items-center gap-3 border-b border-tg-secondary">
        <button onClick={() => navigate(-1)}>
          <ArrowLeft className="w-6 h-6 text-tg-text" />
        </button>
        <h1 className="text-xl font-bold text-tg-text">Настройки платформы</h1>
      </div>

      <div className="px-4 pt-4 space-y-6">

        {/* ====== MODULES ====== */}
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-tg-text flex items-center gap-2">
            <Package className="w-5 h-5" />
            Модули
          </h2>

          {/* Product source */}
          <div>
            <label className="block text-sm font-medium text-tg-hint mb-1">
              <Database className="w-4 h-4 inline mr-1" />
              Источник каталога
            </label>
            <select
              value={productSource}
              onChange={(e) => setProductSource(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
            >
              <option value="database">База данных (ручное добавление)</option>
              <option value="moysklad">МойСклад</option>
              <option value="one_c">1С</option>
            </select>
          </div>

          {/* Checkout type */}
          <div>
            <label className="block text-sm font-medium text-tg-hint mb-1">
              <ShoppingCart className="w-4 h-4 inline mr-1" />
              Тип оформления заказа
            </label>
            <select
              value={checkoutType}
              onChange={(e) => setCheckoutType(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
            >
              <option value="basic">Базовый (имя + телефон)</option>
              <option value="enhanced">Расширенный (+ адрес)</option>
              <option value="payment">С оплатой</option>
              <option value="full">Полный (доставка + оплата)</option>
            </select>
          </div>

          {/* Toggles */}
          <div className="space-y-3">
            <ToggleRow
              icon={<Tag className="w-4 h-4" />}
              label="Промокоды"
              description="Возможность применять промокоды при оформлении"
              checked={promoEnabled}
              onChange={setPromoEnabled}
            />
            <ToggleRow
              icon={<Send className="w-4 h-4" />}
              label="Рассылка"
              description="Массовая отправка сообщений пользователям"
              checked={mailingEnabled}
              onChange={setMailingEnabled}
            />
            <ToggleRow
              icon={<Truck className="w-4 h-4" />}
              label="Доставка"
              description="Возможность заказать доставку"
              checked={deliveryEnabled}
              onChange={setDeliveryEnabled}
            />
            <ToggleRow
              icon={<Package className="w-4 h-4" />}
              label="Самовывоз"
              description="Возможность забрать товар самостоятельно"
              checked={pickupEnabled}
              onChange={setPickupEnabled}
            />
          </div>
        </section>

        <Divider />

        {/* ====== DELIVERY SERVICES ====== */}
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-tg-text flex items-center gap-2">
            <Truck className="w-5 h-5" />
            Службы доставки
          </h2>
          <p className="text-xs text-tg-hint -mt-2">
            Включите нужные интеграции. Для работы каждой службы потребуются API-ключи (скоро).
          </p>

          <div className="space-y-3">
            <ToggleRow
              label="Яндекс Доставка"
              description="Курьерская доставка через Яндекс"
              checked={yandexDeliveryEnabled}
              onChange={setYandexDeliveryEnabled}
            />
            <ToggleRow
              label="СДЭК"
              description="Доставка через СДЭК"
              checked={sdekEnabled}
              onChange={setSdekEnabled}
            />
            <ToggleRow
              label="Почта России"
              description="Доставка через Почту России"
              checked={pochtaEnabled}
              onChange={setPochtaEnabled}
            />
          </div>
        </section>

        <Divider />

        {/* ====== INTEGRATION KEYS ====== */}
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-tg-text flex items-center gap-2">
            <Link className="w-5 h-5" />
            Интеграции и ключи
          </h2>

          {/* MoySklad token */}
          {productSource === 'moysklad' && (
            <SecretInput
              label="Токен МойСклад"
              value={moyskladToken}
              onChange={setMoyskladToken}
              visible={showMoysklad}
              onToggleVisible={() => setShowMoysklad(!showMoysklad)}
              placeholder="Введите токен МойСклад"
            />
          )}

          {/* 1C */}
          {productSource === 'one_c' && (
            <>
              <Input
                label="Эндпоинт 1С"
                value={oneCEndpoint}
                onChange={(e) => setOneCEndpoint(e.target.value)}
                placeholder="https://1c-server.example.com/odata/..."
              />
              <Input
                label="Логин 1С"
                value={oneCLogin}
                onChange={(e) => setOneCLogin(e.target.value)}
                placeholder="admin"
              />
              <SecretInput
                label="Пароль 1С"
                value={oneCPassword}
                onChange={setOneCPassword}
                visible={showOneCPassword}
                onToggleVisible={() => setShowOneCPassword(!showOneCPassword)}
                placeholder="Введите пароль"
              />
            </>
          )}

          {/* Payment */}
          <SecretInput
            label="Токен платёжного провайдера"
            icon={<CreditCard className="w-4 h-4" />}
            value={paymentToken}
            onChange={setPaymentToken}
            visible={showPayment}
            onToggleVisible={() => setShowPayment(!showPayment)}
            placeholder="Введите токен (Telegram Payments)"
          />

          {/* Yandex Maps */}
          <SecretInput
            label="API-ключ Яндекс Карт"
            icon={<Map className="w-4 h-4" />}
            value={yandexMapsKey}
            onChange={setYandexMapsKey}
            visible={showYandexMaps}
            onToggleVisible={() => setShowYandexMaps(!showYandexMaps)}
            placeholder="Введите ключ Яндекс Карт"
          />

          {/* Support link */}
          <Input
            label="Ссылка на поддержку"
            value={supportLink}
            onChange={(e) => setSupportLink(e.target.value)}
            placeholder="https://t.me/your_support"
          />

          {/* Sync interval */}
          {productSource !== 'database' && (
            <div>
              <label className="block text-sm font-medium text-tg-hint mb-1">
                <Clock className="w-4 h-4 inline mr-1" />
                Интервал синхронизации (минуты)
              </label>
              <input
                type="number"
                min="1"
                max="1440"
                value={syncInterval}
                onChange={(e) => setSyncInterval(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
              />
              <p className="text-xs text-tg-hint mt-1">
                Как часто синхронизировать каталог с внешним источником
              </p>
            </div>
          )}
        </section>

        {/* Error */}
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm">{error}</div>
        )}
      </div>

      {/* Fixed save button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-tg-bg border-t border-tg-secondary">
        <Button
          onClick={handleSave}
          fullWidth
          size="lg"
          disabled={saving}
          className={saved ? 'bg-green-500 hover:bg-green-500' : ''}
        >
          <Save className="w-5 h-5 mr-2" />
          {saving ? 'Сохранение...' : saved ? 'Сохранено!' : 'Сохранить настройки'}
        </Button>
      </div>
    </div>
  );
};


// ---- Helper components ----

const Divider: React.FC = () => (
  <div className="border-t border-tg-secondary" />
);

interface ToggleRowProps {
  icon?: React.ReactNode;
  label: string;
  description: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}

const ToggleRow: React.FC<ToggleRowProps> = ({ icon, label, description, checked, onChange }) => (
  <label className="flex items-center gap-3 p-3 bg-tg-secondary rounded-xl cursor-pointer">
    <div className="flex-1">
      <div className="text-sm font-medium text-tg-text flex items-center gap-1.5">
        {icon}
        {label}
      </div>
      <div className="text-xs text-tg-hint mt-0.5">{description}</div>
    </div>
    <div className="relative">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="sr-only"
      />
      <div
        className={`w-11 h-6 rounded-full transition-colors ${
          checked ? 'bg-tg-button' : 'bg-gray-300'
        }`}
      >
        <div
          className={`w-5 h-5 bg-white rounded-full shadow-sm transform transition-transform mt-0.5 ${
            checked ? 'translate-x-[22px]' : 'translate-x-0.5'
          }`}
        />
      </div>
    </div>
  </label>
);

interface SecretInputProps {
  label: string;
  icon?: React.ReactNode;
  value: string;
  onChange: (value: string) => void;
  visible: boolean;
  onToggleVisible: () => void;
  placeholder?: string;
}

const SecretInput: React.FC<SecretInputProps> = ({
  label,
  icon,
  value,
  onChange,
  visible,
  onToggleVisible,
  placeholder,
}) => (
  <div>
    <label className="block text-sm font-medium text-tg-hint mb-1">
      {icon && <span className="inline mr-1">{icon}</span>}
      {label}
    </label>
    <div className="relative">
      <input
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 pr-10 rounded-xl bg-tg-secondary text-tg-text border-none outline-none focus:ring-2 focus:ring-tg-button placeholder-tg-hint"
      />
      <button
        type="button"
        onClick={onToggleVisible}
        className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center text-tg-hint"
      >
        {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
      </button>
    </div>
    <p className="text-xs text-tg-hint mt-1">
      {value && value.includes('*') ? 'Значение задано (замаскировано). Введите новое для замены.' : ''}
    </p>
  </div>
);





