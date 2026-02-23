import React, { useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { ArrowLeft, CreditCard, Truck, AlertTriangle } from 'lucide-react';
import { useConfigStore } from '../store/configStore';
import { useCartStore } from '../store/cartStore';
import { createOrder, checkPromo, createPayment, getMe } from '../api/endpoints';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { YandexAddressSuggest } from '../components/YandexAddressSuggest';
import { useBackButton } from '../hooks/useBackButton';

export const CheckoutPage: React.FC = () => {
  useBackButton();
  const navigate = useNavigate();
  const config = useConfigStore((s) => s.config);
  const fetchConfig = useConfigStore((s) => s.fetchConfig);
  const { totalPrice, items, validateCart, fetchCart } = useCartStore();

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  useEffect(() => {
    setDeliveryType(config?.pickup_enabled ? 'pickup' : 'delivery');
  }, [config?.pickup_enabled]);

  useEffect(() => {
    if (config?.bonus_enabled && config?.bonus_spend_enabled) {
      getMe().then(({ data }) => setBonusBalance(data.bonus_balance)).catch(() => {});
    }
  }, [config?.bonus_enabled, config?.bonus_spend_enabled]);

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [deliveryType, setDeliveryType] = useState<string>(
    config?.pickup_enabled ? 'pickup' : 'delivery'
  );
  const [deliveryService, setDeliveryService] = useState('');
  const [promoCode, setPromoCode] = useState('');
  const [promoResult, setPromoResult] = useState<string>('');
  const [promoValid, setPromoValid] = useState(false);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [stockConflict, setStockConflict] = useState<{
    removed: Array<{ product_name: string }>;
    adjusted: Array<{ product_name: string; old_quantity: number; new_quantity: number }>;
  } | null>(null);
  const [addressError, setAddressError] = useState<string | null>(null);
  const [bonusBalance, setBonusBalance] = useState<number>(0);
  const [bonusToUse, setBonusToUse] = useState<number>(0);

  const checkoutType = config?.checkout_type || 'basic';
  const hasPayment = ['payment', 'full'].includes(checkoutType);
  const hasDelivery = checkoutType === 'full' && config?.delivery_enabled;

  const showBonusBlock = !!(config?.bonus_enabled && config?.bonus_spend_enabled);
  const maxBonusByLimit =
    showBonusBlock && config
      ? config.bonus_spend_limit_type === 'percent'
        ? (totalPrice * config.bonus_spend_limit_value) / 100
        : config.bonus_spend_limit_value
      : 0;
  const maxBonusAllowed = Math.floor(Math.min(bonusBalance, maxBonusByLimit));
  const subtotal = Math.max(0, totalPrice - bonusToUse);
  const deliveryFee =
    deliveryType === 'delivery' && config
      ? (config.free_delivery_min_amount > 0 && subtotal >= config.free_delivery_min_amount)
        ? 0
        : (config.delivery_cost || 0)
      : 0;
  const payAmount = subtotal + deliveryFee;

  // Determine if pickup is available (requires store_address)
  const pickupAvailable = config?.pickup_enabled && !!config?.store_address;
  const deliveryAvailable = config?.delivery_enabled !== false;

  const handleCheckPromo = async () => {
    if (!promoCode.trim()) return;
    try {
      const { data } = await checkPromo(promoCode, totalPrice, deliveryType);
      setPromoResult(data.message);
      setPromoValid(data.valid);
    } catch {
      setPromoResult('Ошибка проверки');
      setPromoValid(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setStockConflict(null);
    setAddressError(null);

    // Проверка наличия перед оформлением
    const { removed, adjusted } = await validateCart();
    if (removed.length > 0 || adjusted.length > 0) {
      setStockConflict({
        removed: removed.map((r) => ({ product_name: r.product_name })),
        adjusted: adjusted.map((a) => ({
          product_name: a.product_name,
          old_quantity: a.old_quantity,
          new_quantity: a.new_quantity,
        })),
      });
      setLoading(false);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('warning');
      return;
    }

    // Проверка города доставки, если админ указал ограничение
    const deliveryCity = config?.delivery_city?.trim();
    if (deliveryType === 'delivery' && deliveryCity && address.trim()) {
      let addressInCity = false;
      if (config?.yandex_maps_key) {
        try {
          const res = await fetch(
            `https://geocode-maps.yandex.ru/1.x/?apikey=${config.yandex_maps_key}&format=json&geocode=${encodeURIComponent(address)}&lang=ru_RU&results=1`
          );
          const data = await res.json();
          const text = data.response?.GeoObjectCollection?.featureMember?.[0]?.GeoObject?.metaDataProperty?.GeocoderMetaData?.text ?? '';
          addressInCity = text.toLowerCase().includes(deliveryCity.toLowerCase());
        } catch {
          addressInCity = address.toLowerCase().includes(deliveryCity.toLowerCase());
        }
      } else {
        addressInCity = address.toLowerCase().includes(deliveryCity.toLowerCase());
      }
      if (!addressInCity) {
        setAddressError(`Доставка возможна только в ${deliveryCity}. Укажите адрес в этом городе.`);
        setLoading(false);
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.('warning');
        return;
      }
    }

    try {
      const { data: order } = await createOrder({
        customer_name: name,
        customer_phone: phone,
        address: deliveryType === 'pickup'
          ? `Самовывоз: ${config?.store_address || 'Адрес магазина'}`
          : address,
        address_coords: undefined,
        delivery_type: deliveryType,
        delivery_service: deliveryService || undefined,
        promo_code: promoValid ? promoCode : undefined,
        bonus_to_use: bonusToUse > 0 ? Math.round(bonusToUse) : undefined,
      });

      if (hasPayment && config?.payment_enabled) {
        try {
          await createPayment(order.id);
          navigate(`/order/${order.id}`);
        } catch {
          navigate(`/order/${order.id}`);
        }
      } else {
        navigate(`/order/${order.id}`);
      }
    } catch (err: any) {
      const status = err?.response?.status;
      const data = err?.response?.data;
      const msg = typeof data?.detail === 'string' ? data.detail : data?.detail?.msg || 'Ошибка оформления заказа';

      if (status === 409 && data?.removed !== undefined) {
        setStockConflict({
          removed: data.removed || [],
          adjusted: data.adjusted || [],
        });
        await fetchCart();
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('warning');
      } else if (status === 400 && msg) {
        setPromoResult(msg);
        setPromoValid(false);
        alert(msg);
      } else {
        console.error(err);
        alert(msg);
      }
    }
    setLoading(false);
  };

  if (items.length === 0 && !stockConflict) {
    return <Navigate to="/cart" replace />;
  }

  return (
    <div className="pb-24">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 flex items-center gap-3">
        <button onClick={() => navigate(-1)}>
          <ArrowLeft className="w-6 h-6 text-tg-text" />
        </button>
        <h1 className="text-xl font-bold text-tg-text">Оформление заказа</h1>
      </div>

      {/* Step indicator */}
      <div className="px-4 pb-4">
        <div className="flex items-center gap-2">
          {[1, 2, 3].slice(0, hasDelivery ? 3 : hasPayment ? 2 : 1).map((s) => (
            <div
              key={s}
              className={`h-1 flex-1 rounded-full ${
                s <= step ? 'bg-tg-button' : 'bg-tg-secondary'
              }`}
            />
          ))}
        </div>
      </div>

      <div className="px-4 space-y-4">
        {/* Step 1: Contact info */}
        {step === 1 && (
          <>
            <h2 className="text-lg font-semibold text-tg-text">Контактные данные</h2>
            <Input
              label="Имя"
              placeholder="Введите ваше имя"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Input
              label="Телефон"
              placeholder="+7 (999) 999-99-99"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />

            {/* Delivery type */}
            {(pickupAvailable || deliveryAvailable) && (
              <div>
                <label className="block text-sm font-medium text-tg-hint mb-2">
                  Способ получения
                </label>
                <div className="flex gap-2">
                  {pickupAvailable && (
                    <button
                      onClick={() => setDeliveryType('pickup')}
                      className={`flex-1 p-3 rounded-xl text-sm font-medium ${
                        deliveryType === 'pickup'
                          ? 'bg-tg-button text-tg-button-text'
                          : 'bg-tg-secondary text-tg-text'
                      }`}
                    >
                      🏪 Самовывоз
                    </button>
                  )}
                  {deliveryAvailable && (
                    <button
                      onClick={() => setDeliveryType('delivery')}
                      className={`flex-1 p-3 rounded-xl text-sm font-medium ${
                        deliveryType === 'delivery'
                          ? 'bg-tg-button text-tg-button-text'
                          : 'bg-tg-secondary text-tg-text'
                      }`}
                    >
                      🚚 Доставка
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Pickup address display */}
            {deliveryType === 'pickup' && config?.store_address && (
              <div className="p-3 bg-tg-secondary rounded-xl">
                <p className="text-xs text-tg-hint mb-1">Адрес самовывоза:</p>
                <p className="text-sm text-tg-text">{config.store_address}</p>
              </div>
            )}

            {/* Delivery address */}
            {deliveryType === 'delivery' && (
              <div>
                {config?.yandex_maps_key ? (
                  <YandexAddressSuggest
                    apiKey={config.yandex_maps_key}
                    value={address}
                    onChange={(v) => {
                      setAddress(v);
                      setAddressError(null);
                    }}
                    label="Адрес доставки"
                    placeholder="Начните вводить адрес"
                    deliveryCity={config?.delivery_city}
                  />
                ) : (
                  <Input
                    label="Адрес доставки"
                    placeholder="Укажите адрес доставки"
                    value={address}
                    onChange={(e) => {
                      setAddress(e.target.value);
                      setAddressError(null);
                    }}
                  />
                )}
                {addressError && (
                  <p className="mt-1 text-sm text-red-500">{addressError}</p>
                )}
                {config?.delivery_city && !addressError && (
                  <p className="mt-1 text-xs text-tg-hint">
                    📍 Доставка доступна только в: {config.delivery_city}
                  </p>
                )}
              </div>
            )}

            {/* Bonus spend */}
            {showBonusBlock && (
              <div>
                <label className="block text-sm font-medium text-tg-hint mb-1">Списать бонусы</label>
                <p className="text-xs text-tg-hint mb-1">Доступно: {bonusBalance.toLocaleString('ru-RU')} бонусов. Макс. к списанию: {maxBonusAllowed.toLocaleString('ru-RU')}</p>
                <div className="flex gap-2 items-center flex-wrap">
                  <input
                    type="number"
                    min={0}
                    max={maxBonusAllowed}
                    step={1}
                    value={bonusToUse || ''}
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      setBonusToUse(Number.isFinite(v) ? Math.min(Math.max(0, Math.round(v)), maxBonusAllowed) : 0);
                    }}
                    placeholder="0"
                    className="w-24 px-3 py-2 rounded-xl bg-tg-secondary text-tg-text text-sm border-none outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setBonusToUse(maxBonusAllowed)}
                    className="px-3 py-2 rounded-lg text-sm bg-tg-secondary text-tg-text"
                  >
                    Потратить все
                  </button>
                  <button
                    type="button"
                    onClick={() => setBonusToUse(0)}
                    className="px-3 py-2 rounded-lg text-sm bg-tg-secondary text-tg-text"
                  >
                    Не использовать
                  </button>
                </div>
              </div>
            )}

            {/* Promo */}
            {config?.promo_enabled && (
              <div>
                <label className="block text-sm font-medium text-tg-hint mb-1">
                  Промокод
                </label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Введите промокод"
                    value={promoCode}
                    onChange={(e) => setPromoCode(e.target.value)}
                  />
                  <Button variant="secondary" onClick={handleCheckPromo}>
                    ОК
                  </Button>
                </div>
                {promoResult && (
                  <p className={`text-xs mt-1 ${promoValid ? 'text-green-600' : 'text-red-500'}`}>
                    {promoResult}
                  </p>
                )}
              </div>
            )}
          </>
        )}

        {/* Step 2: Delivery service (full checkout) */}
        {step === 2 && hasDelivery && (
          <>
            <h2 className="text-lg font-semibold text-tg-text">
              <Truck className="w-5 h-5 inline mr-1" />
              Служба доставки
            </h2>
            {['СДЭК', 'Почта России', 'Boxberry', 'DPD'].map((service) => (
              <button
                key={service}
                onClick={() => setDeliveryService(service)}
                className={`w-full p-4 rounded-xl text-left font-medium ${
                  deliveryService === service
                    ? 'bg-tg-button text-tg-button-text'
                    : 'bg-tg-secondary text-tg-text'
                }`}
              >
                {service}
              </button>
            ))}
          </>
        )}

        {/* Stock conflict warning */}
        {stockConflict && (
          <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 mt-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <h3 className="text-sm font-semibold text-amber-800">Наличие товаров изменилось</h3>
            </div>
            {stockConflict.removed.length > 0 && (
              <div className="mb-2">
                <p className="text-xs font-medium text-red-600 mb-1">Убрано (нет в наличии):</p>
                {stockConflict.removed.map((r, i) => (
                  <p key={i} className="text-xs text-red-600">• {r.product_name}</p>
                ))}
              </div>
            )}
            {stockConflict.adjusted.length > 0 && (
              <div>
                <p className="text-xs font-medium text-amber-700 mb-1">Количество изменено:</p>
                {stockConflict.adjusted.map((a, i) => (
                  <p key={i} className="text-xs text-amber-700">
                    • {a.product_name}: {a.old_quantity} → {a.new_quantity} шт.
                  </p>
                ))}
              </div>
            )}
            <p className="text-xs text-amber-600 mt-2">Проверьте заказ и попробуйте снова.</p>
          </div>
        )}

        {/* Order summary */}
        <div className="bg-tg-secondary rounded-2xl p-4 mt-4">
          <h3 className="text-sm font-semibold text-tg-text mb-2">Ваш заказ</h3>
          {items.map((item) => (
            <div key={item.id} className="flex justify-between text-sm py-1">
              <span className="text-tg-hint truncate mr-2">
                {item.product.name}
                {item.modification_label ? ` (${item.modification_label})` : ''} x{item.quantity}
              </span>
              <span className="text-tg-text flex-shrink-0">
                {(item.product.price * item.quantity).toLocaleString('ru-RU')} ₽
              </span>
            </div>
          ))}
          {bonusToUse > 0 && (
            <div className="flex justify-between text-sm py-1">
              <span className="text-tg-hint">Списание бонусов</span>
              <span className="text-tg-text">−{bonusToUse.toLocaleString('ru-RU')} ₽</span>
            </div>
          )}
          {deliveryFee > 0 && (
            <div className="flex justify-between text-sm py-1">
              <span className="text-tg-hint">Доставка</span>
              <span className="text-tg-text">{deliveryFee.toLocaleString('ru-RU')} ₽</span>
            </div>
          )}
          {deliveryType === 'delivery' && config && config.free_delivery_min_amount > 0 && deliveryFee === 0 && (
            <div className="flex justify-between text-sm py-1 text-green-600">
              <span>Доставка</span>
              <span>Бесплатно (от {config.free_delivery_min_amount.toLocaleString('ru-RU')} ₽)</span>
            </div>
          )}
          <div className="border-t border-tg-bg mt-2 pt-2 flex justify-between">
            <span className="font-bold text-tg-text">{bonusToUse > 0 ? 'К оплате' : 'Итого'}</span>
            <span className="font-bold text-tg-text">
              {payAmount.toLocaleString('ru-RU')} ₽
            </span>
          </div>
        </div>
      </div>

      {/* Bottom action */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-tg-bg border-t border-tg-secondary">
        {hasDelivery && step === 1 ? (
          <Button
            onClick={() => setStep(2)}
            fullWidth
            size="lg"
            disabled={!name || !phone || (deliveryType === 'delivery' && !address)}
          >
            Далее
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            fullWidth
            size="lg"
            disabled={loading || !name || !phone || (deliveryType === 'delivery' && !address)}
          >
            {hasPayment && config?.payment_enabled ? (
              <>
                <CreditCard className="w-5 h-5 mr-2" />
                Оплатить {payAmount.toLocaleString('ru-RU')} ₽
              </>
            ) : (
              `Оформить заказ — ${payAmount.toLocaleString('ru-RU')} ₽`
            )}
          </Button>
        )}
      </div>
    </div>
  );
};
