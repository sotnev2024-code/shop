import React, { useEffect, useMemo, useState } from 'react';
import { Plus, Trash2, Edit, Check, X, ChevronUp, ChevronDown, ChevronRight } from 'lucide-react';
import {
  adminGetSettings, adminUpdateSettings,
  adminGetCategories, adminCreateCategory, adminUpdateCategory, adminDeleteCategory, adminUploadCategoryImage,
  adminGetModificationTypes, adminCreateModificationType, adminUpdateModificationType, adminDeleteModificationType,
  adminAddModificationTypeValue, adminDeleteModificationTypeValue,
  adminGetProducts, adminBulkPriceUpdate,
} from '../api/endpoints';
import type { Category, ModificationType, Product } from '../types';
import type { BulkPriceScope, BulkPriceOperation } from '../types';
import { useConfigStore } from '../store/configStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

export const AdminSettingsPage: React.FC = () => {
  // --- Settings state ---
  const [shopName, setShopName] = useState('');
  const [pickupEnabled, setPickupEnabled] = useState(true);
  const [deliveryEnabled, setDeliveryEnabled] = useState(false);
  const [currency, setCurrency] = useState('RUB');
  const [storeAddress, setStoreAddress] = useState('');
  const [deliveryCity, setDeliveryCity] = useState('');
  const [deliveryCost, setDeliveryCost] = useState('');
  const [freeDeliveryMinAmount, setFreeDeliveryMinAmount] = useState('');
  const [minOrderAmountPickup, setMinOrderAmountPickup] = useState('');
  const [minOrderAmountDelivery, setMinOrderAmountDelivery] = useState('');
  const [supportLink, setSupportLink] = useState('');
  const [adminIds, setAdminIds] = useState('');
  const [currentTelegramId, setCurrentTelegramId] = useState<number | null>(null);
  const [logoUrl, setLogoUrl] = useState('');
  const [bannerAspectShape, setBannerAspectShape] = useState<'square' | 'rectangle'>('rectangle');
  const [bannerSize, setBannerSize] = useState<'small' | 'medium' | 'large' | 'xl'>('medium');
  const [categoryImageSize, setCategoryImageSize] = useState<'small' | 'medium' | 'large' | 'xlarge'>('medium');
  const [bonusEnabled, setBonusEnabled] = useState(false);
  const [bonusWelcomeEnabled, setBonusWelcomeEnabled] = useState(false);
  const [bonusWelcomeAmount, setBonusWelcomeAmount] = useState('0');
  const [bonusPurchaseEnabled, setBonusPurchaseEnabled] = useState(false);
  const [bonusPurchasePercent, setBonusPurchasePercent] = useState('0');
  const [bonusSpendEnabled, setBonusSpendEnabled] = useState(false);
  const [bonusSpendLimitType, setBonusSpendLimitType] = useState<'percent' | 'fixed'>('percent');
  const [bonusSpendLimitValue, setBonusSpendLimitValue] = useState('0');
  const [saved, setSaved] = useState(false);

  // --- Categories state ---
  const [categories, setCategories] = useState<Category[]>([]);
  const [newCatName, setNewCatName] = useState('');
  const [newCatParentId, setNewCatParentId] = useState<number | null>(null);
  const [newCatImageUrl, setNewCatImageUrl] = useState('');
  const [editingCatId, setEditingCatId] = useState<number | null>(null);
  const [editingCatName, setEditingCatName] = useState('');
  const [editingCatParentId, setEditingCatParentId] = useState<number | null>(null);
  const [editingCatImageUrl, setEditingCatImageUrl] = useState('');
  const [uploadingCatImage, setUploadingCatImage] = useState(false);
  const [catLoading, setCatLoading] = useState(false);
  /** id корневых категорий, у которых раскрыт список подкатегорий */
  const [expandedCategoryIds, setExpandedCategoryIds] = useState<number[]>([]);

  // --- Modification types state ---
  const [modTypes, setModTypes] = useState<ModificationType[]>([]);
  const [newModName, setNewModName] = useState('');
  const [newModValues, setNewModValues] = useState('');
  const [editingModId, setEditingModId] = useState<number | null>(null);
  const [editingModName, setEditingModName] = useState('');
  const [newValueForTypeId, setNewValueForTypeId] = useState<number | null>(null);
  const [newValueText, setNewValueText] = useState('');
  const [modLoading, setModLoading] = useState(false);

  // --- Bulk price state ---
  const [bulkScope, setBulkScope] = useState<BulkPriceScope>('all');
  const [bulkProductIds, setBulkProductIds] = useState<number[]>([]);
  const [bulkPriceEquals, setBulkPriceEquals] = useState('');
  const [bulkPriceMin, setBulkPriceMin] = useState('');
  const [bulkPriceMax, setBulkPriceMax] = useState('');
  const [bulkCategoryId, setBulkCategoryId] = useState<number | ''>('');
  const [bulkOperation, setBulkOperation] = useState<BulkPriceOperation>('add_amount');
  const [bulkValue, setBulkValue] = useState('');
  const [bulkRoundTo, setBulkRoundTo] = useState('');
  const [bulkPreviewTotal, setBulkPreviewTotal] = useState<number | null>(null);
  const [bulkProducts, setBulkProducts] = useState<Product[]>([]);
  const [bulkProductsPage, setBulkProductsPage] = useState(1);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkError, setBulkError] = useState('');
  const [bulkSuccess, setBulkSuccess] = useState('');

  type SettingsSection = 'general' | 'admins' | 'delivery' | 'banners' | 'bonuses' | 'categories' | 'modifications' | 'bulk';
  const [activeSection, setActiveSection] = useState<SettingsSection>('general');

  const sections: { id: SettingsSection; label: string }[] = [
    { id: 'general', label: 'Основные' },
    { id: 'admins', label: 'Администраторы' },
    { id: 'delivery', label: 'Доставка' },
    { id: 'banners', label: 'Баннеры и каталог' },
    { id: 'bonuses', label: 'Бонусы' },
    { id: 'categories', label: 'Категории' },
    { id: 'modifications', label: 'Модификации' },
    { id: 'bulk', label: 'Массовые цены' },
  ];

  useEffect(() => {
    adminGetSettings().then(({ data }: any) => {
      setShopName(data.shop_name);
      setLogoUrl(data.logo_url || '');
      setPickupEnabled(data.pickup_enabled);
      setDeliveryEnabled(data.delivery_enabled);
      setCurrency(data.currency);
      setStoreAddress(data.store_address || '');
      setDeliveryCity(data.delivery_city || '');
      setDeliveryCost(String(data.delivery_cost ?? 0));
      setFreeDeliveryMinAmount(String(data.free_delivery_min_amount ?? 0));
      setMinOrderAmountPickup(String(data.min_order_amount_pickup ?? 0));
      setMinOrderAmountDelivery(String(data.min_order_amount_delivery ?? 0));
      setSupportLink(data.support_link ?? '');
      setAdminIds(data.admin_ids ?? '');
      setCurrentTelegramId(data.current_telegram_id ?? null);
      setBannerAspectShape(data.banner_aspect_shape === 'square' ? 'square' : 'rectangle');
      setBannerSize(
        data.banner_size === 'small' ? 'small'
          : data.banner_size === 'large' ? 'large'
          : data.banner_size === 'xl' ? 'xl'
          : 'medium'
      );
      setCategoryImageSize(
        data.category_image_size === 'small' ? 'small'
          : data.category_image_size === 'large' ? 'large'
          : data.category_image_size === 'xlarge' ? 'xlarge'
          : 'medium'
      );
      setBonusEnabled(!!data.bonus_enabled);
      setBonusWelcomeEnabled(!!data.bonus_welcome_enabled);
      setBonusWelcomeAmount(String(data.bonus_welcome_amount ?? 0));
      setBonusPurchaseEnabled(!!data.bonus_purchase_enabled);
      setBonusPurchasePercent(String(data.bonus_purchase_percent ?? 0));
      setBonusSpendEnabled(!!data.bonus_spend_enabled);
      setBonusSpendLimitType(data.bonus_spend_limit_type === 'fixed' ? 'fixed' : 'percent');
      setBonusSpendLimitValue(String(data.bonus_spend_limit_value ?? 0));
    });
    fetchCategories();
    fetchModTypes();
  }, []);

  const fetchCategories = () => {
    adminGetCategories().then(({ data }) => {
      setCategories(data.sort((a, b) => a.sort_order - b.sort_order));
    });
  };

  // Полный плоский список (для массовых цен и др.): корни + все дети
  const flattenedCategories = useMemo(() => {
    const roots = categories.filter((c) => !c.parent_id).sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name));
    const result: Category[] = [];
    roots.forEach((r) => {
      result.push(r);
      categories
        .filter((c) => c.parent_id === r.id)
        .sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name))
        .forEach((ch) => result.push(ch));
    });
    return result;
  }, [categories]);

  // Список для отображения: корни + подкатегории только у раскрытых
  const displayCategories = useMemo(() => {
    const roots = categories.filter((c) => !c.parent_id).sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name));
    const result: Category[] = [];
    roots.forEach((r) => {
      result.push(r);
      if (expandedCategoryIds.includes(r.id)) {
        categories
          .filter((c) => (c.parent_id ?? null) === r.id)
          .sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name))
          .forEach((ch) => result.push(ch));
      }
    });
    return result;
  }, [categories, expandedCategoryIds]);

  const toggleCategoryExpanded = (id: number) => {
    setExpandedCategoryIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const fetchModTypes = () => {
    adminGetModificationTypes().then(({ data }) => {
      setModTypes(data.sort((a, b) => a.sort_order - b.sort_order));
    });
  };

  const handleSave = async () => {
    await adminUpdateSettings({
      shop_name: shopName,
      pickup_enabled: pickupEnabled,
      delivery_enabled: deliveryEnabled,
      currency,
      store_address: storeAddress,
      delivery_city: deliveryCity,
      delivery_cost: parseFloat(deliveryCost) || 0,
      free_delivery_min_amount: parseFloat(freeDeliveryMinAmount) || 0,
      min_order_amount_pickup: parseFloat(minOrderAmountPickup) || 0,
      min_order_amount_delivery: parseFloat(minOrderAmountDelivery) || 0,
      support_link: supportLink.trim() || null,
      admin_ids: adminIds.trim(),
      banner_aspect_shape: bannerAspectShape,
      banner_size: bannerSize,
      category_image_size: categoryImageSize,
      bonus_enabled: bonusEnabled,
      bonus_welcome_enabled: bonusWelcomeEnabled,
      bonus_welcome_amount: parseFloat(bonusWelcomeAmount) || 0,
      bonus_purchase_enabled: bonusPurchaseEnabled,
      bonus_purchase_percent: parseFloat(bonusPurchasePercent) || 0,
      bonus_spend_enabled: bonusSpendEnabled,
      bonus_spend_limit_type: bonusSpendLimitType,
      bonus_spend_limit_value: parseFloat(bonusSpendLimitValue) || 0,
    });
    await useConfigStore.getState().fetchConfig();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  // --- Category handlers ---

  const slugify = (text: string) => {
    let slug = text
      .toLowerCase()
      .replace(/[ёЁ]/g, 'е')
      .replace(/[а-яА-Я]/g, (ch) => {
        const map: Record<string, string> = {
          а:'a',б:'b',в:'v',г:'g',д:'d',е:'e',ж:'zh',з:'z',и:'i',й:'y',к:'k',
          л:'l',м:'m',н:'n',о:'o',п:'p',р:'r',с:'s',т:'t',у:'u',ф:'f',х:'kh',
          ц:'ts',ч:'ch',ш:'sh',щ:'shch',ъ:'',ы:'y',ь:'',э:'e',ю:'yu',я:'ya',
        };
        return map[ch] || ch;
      })
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
    
    // If slug is empty after processing, generate a fallback
    if (!slug) {
      slug = 'category-' + Date.now().toString(36);
    }
    
    return slug;
  };

  const handleAddCategory = async () => {
    const name = newCatName.trim();
    if (!name) return;
    setCatLoading(true);
    try {
      const slug = slugify(name);
      if (!slug) {
        alert('Не удалось создать slug из названия. Попробуйте другое название.');
        setCatLoading(false);
        return;
      }
      const parentId = newCatParentId ?? undefined;
      const roots = categories.filter((c) => !c.parent_id);
      const sortOrder = parentId !== undefined
        ? categories.filter((c) => c.parent_id === parentId).length
        : roots.length;
      await adminCreateCategory({ name, slug, sort_order: sortOrder, parent_id: parentId ?? null, image_url: newCatImageUrl || null });
      setNewCatName('');
      setNewCatParentId(null);
      setNewCatImageUrl('');
      fetchCategories();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'Ошибка создания категории');
    }
    setCatLoading(false);
  };

  const handleStartEdit = (cat: Category) => {
    setEditingCatId(cat.id);
    setEditingCatName(cat.name);
    setEditingCatParentId(cat.parent_id ?? null);
    setEditingCatImageUrl(cat.image_url || '');
  };

  const handleCancelEdit = () => {
    setEditingCatId(null);
    setEditingCatName('');
    setEditingCatParentId(null);
    setEditingCatImageUrl('');
  };

  const handleCategoryImageUpload = async (e: React.ChangeEvent<HTMLInputElement>, setUrl: (url: string) => void) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingCatImage(true);
    try {
      const { data } = await adminUploadCategoryImage(file);
      setUrl(data.url);
    } finally {
      setUploadingCatImage(false);
      e.target.value = '';
    }
  };

  const handleSaveCategory = async () => {
    if (!editingCatId) return;
    const editingCategory = categories.find((c) => c.id === editingCatId);
    const isAllCategory = editingCategory?.slug === 'all';
    if (isAllCategory) {
      setCatLoading(true);
      try {
        await adminUpdateCategory(editingCatId, { image_url: editingCatImageUrl || null });
        setEditingCatId(null);
        setEditingCatImageUrl('');
        fetchCategories();
      } catch (err: any) {
        const detail = err?.response?.data?.detail;
        alert(typeof detail === 'string' ? detail : 'Ошибка обновления категории');
      }
      setCatLoading(false);
      return;
    }
    if (!editingCatName.trim()) return;
    if (editingCatParentId === editingCatId) return;
    setCatLoading(true);
    try {
      const slug = slugify(editingCatName.trim());
      await adminUpdateCategory(editingCatId, {
        name: editingCatName.trim(),
        slug,
        parent_id: editingCatParentId ?? undefined,
        image_url: editingCatImageUrl || null,
      });
      setEditingCatId(null);
      setEditingCatName('');
      setEditingCatParentId(null);
      setEditingCatImageUrl('');
      fetchCategories();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'Ошибка обновления категории');
    }
    setCatLoading(false);
  };

  const handleDeleteCategory = async (id: number) => {
    if (!confirm('Удалить категорию? Товары останутся без категории.')) return;
    setCatLoading(true);
    try {
      await adminDeleteCategory(id);
      fetchCategories();
    } catch {
      alert('Ошибка удаления');
    }
    setCatLoading(false);
  };

  // --- Modification type handlers ---
  const handleAddModType = async () => {
    const name = newModName.trim();
    if (!name) return;
    const values = newModValues.split(',').map((s) => s.trim()).filter(Boolean);
    setModLoading(true);
    try {
      await adminCreateModificationType({ name, sort_order: modTypes.length, values });
      setNewModName('');
      setNewModValues('');
      fetchModTypes();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'Ошибка создания типа модификации');
    }
    setModLoading(false);
  };

  const handleAddModValue = async (typeId: number) => {
    const val = newValueText.trim();
    if (!val) return;
    setModLoading(true);
    try {
      await adminAddModificationTypeValue(typeId, { value: val });
      setNewValueForTypeId(null);
      setNewValueText('');
      fetchModTypes();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'Ошибка добавления значения');
    }
    setModLoading(false);
  };

  const handleDeleteModValue = async (typeId: number, valueId: number) => {
    setModLoading(true);
    try {
      await adminDeleteModificationTypeValue(typeId, valueId);
      fetchModTypes();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'Ошибка удаления');
    }
    setModLoading(false);
  };

  const handleStartEditMod = (mt: ModificationType) => {
    setEditingModId(mt.id);
    setEditingModName(mt.name);
  };

  const handleCancelEditMod = () => {
    setEditingModId(null);
    setEditingModName('');
  };

  const handleSaveModType = async () => {
    if (!editingModId || !editingModName.trim()) return;
    setModLoading(true);
    try {
      await adminUpdateModificationType(editingModId, { name: editingModName.trim() });
      setEditingModId(null);
      setEditingModName('');
      fetchModTypes();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'Ошибка сохранения');
    }
    setModLoading(false);
  };

  const handleMoveModType = async (id: number, direction: 'up' | 'down') => {
    const idx = modTypes.findIndex((m) => m.id === id);
    if (idx < 0) return;
    const swapIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= modTypes.length) return;
    const current = modTypes[idx];
    const swap = modTypes[swapIdx];
    setModLoading(true);
    try {
      await adminUpdateModificationType(current.id, { sort_order: swap.sort_order });
      await adminUpdateModificationType(swap.id, { sort_order: current.sort_order });
      fetchModTypes();
    } finally {
      setModLoading(false);
    }
  };

  const handleDeleteModType = async (id: number) => {
    if (!confirm('Удалить тип модификации? Он не должен использоваться в товарах.')) return;
    setModLoading(true);
    try {
      await adminDeleteModificationType(id);
      fetchModTypes();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : 'Невозможно удалить');
    }
    setModLoading(false);
  };

  const handleMoveCategory = async (id: number, direction: 'up' | 'down') => {
    const idx = displayCategories.findIndex((c) => c.id === id);
    if (idx < 0) return;
    const swapIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= displayCategories.length) return;

    const current = displayCategories[idx];
    const swap = displayCategories[swapIdx];
    // Move only within siblings (same parent_id); treat null and undefined as equal
    if ((current.parent_id ?? null) !== (swap.parent_id ?? null)) return;

    setCatLoading(true);
    try {
      await adminUpdateCategory(current.id, { sort_order: swap.sort_order });
      await adminUpdateCategory(swap.id, { sort_order: current.sort_order });
      fetchCategories();
    } catch {
      alert('Ошибка сортировки');
    }
    setCatLoading(false);
  };

  // --- Bulk price handlers ---
  const fetchBulkPreview = async () => {
    setBulkError('');
    setBulkPreviewTotal(null);
    try {
      const params: Parameters<typeof adminGetProducts>[0] = { page: 1, per_page: 1 };
      if (bulkScope === 'product_ids') {
        if (bulkProductIds.length === 0) {
          setBulkPreviewTotal(0);
          return;
        }
        setBulkPreviewTotal(bulkProductIds.length);
        return;
      }
      if (bulkScope === 'category' && bulkCategoryId !== '') params.category_id = Number(bulkCategoryId);
      if (bulkScope === 'price_equals' && bulkPriceEquals !== '') params.price_equals = Number(bulkPriceEquals);
      if (bulkScope === 'price_range') {
        if (bulkPriceMin !== '') params.price_min = Number(bulkPriceMin);
        if (bulkPriceMax !== '') params.price_max = Number(bulkPriceMax);
      }
      const { data } = await adminGetProducts(params);
      setBulkPreviewTotal(data.total);
    } catch {
      setBulkError('Не удалось загрузить количество');
    }
  };

  const loadBulkProducts = async (page: number = 1) => {
    setBulkLoading(true);
    try {
      const params: Parameters<typeof adminGetProducts>[0] = { page, per_page: 50 };
      if (bulkCategoryId !== '') params.category_id = Number(bulkCategoryId);
      const { data } = await adminGetProducts(params);
      if (page === 1) setBulkProducts(data.items);
      else setBulkProducts((prev) => [...prev, ...data.items]);
      setBulkProductsPage(page);
    } finally {
      setBulkLoading(false);
    }
  };

  const handleBulkApply = async () => {
    const valueNum = parseFloat(bulkValue);
    if (Number.isNaN(valueNum) || valueNum <= 0) {
      setBulkError('Укажите положительное значение');
      return;
    }
    if (bulkScope === 'product_ids' && bulkProductIds.length === 0) {
      setBulkError('Выберите хотя бы один товар');
      return;
    }
    if (bulkScope === 'price_equals' && (bulkPriceEquals === '' || Number.isNaN(Number(bulkPriceEquals)))) {
      setBulkError('Укажите цену для фильтра');
      return;
    }
    if (bulkScope === 'category' && bulkCategoryId === '') {
      setBulkError('Выберите категорию');
      return;
    }

    const body = {
      scope: bulkScope,
      product_ids: bulkScope === 'product_ids' ? bulkProductIds : undefined,
      price_equals: bulkScope === 'price_equals' ? Number(bulkPriceEquals) : undefined,
      price_min: bulkScope === 'price_range' && bulkPriceMin !== '' ? Number(bulkPriceMin) : undefined,
      price_max: bulkScope === 'price_range' && bulkPriceMax !== '' ? Number(bulkPriceMax) : undefined,
      category_id: bulkScope === 'category' && bulkCategoryId !== '' ? Number(bulkCategoryId) : undefined,
      operation: bulkOperation,
      value: valueNum,
      round_to_nearest: bulkRoundTo !== '' && !Number.isNaN(Number(bulkRoundTo)) ? Number(bulkRoundTo) : undefined,
    };
    const previewCount = bulkScope === 'product_ids' ? bulkProductIds.length : (bulkPreviewTotal ?? 0);
    if (previewCount > 5 && !window.confirm(`Изменить цены для ${previewCount} товаров?`)) return;

    setBulkError('');
    setBulkSuccess('');
    setBulkLoading(true);
    try {
      const { data } = await adminBulkPriceUpdate(body);
      setBulkSuccess(`Изменено ${data.updated_count} товаров`);
      setBulkPreviewTotal(null);
      if (bulkScope === 'product_ids') setBulkProductIds([]);
      setTimeout(() => setBulkSuccess(''), 3000);
    } catch (e: unknown) {
      setBulkError(e && typeof e === 'object' && 'response' in e && (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        ? String((e as { response: { data: { detail: string } } }).response.data.detail)
        : 'Ошибка при изменении цен');
    } finally {
      setBulkLoading(false);
    }
  };

  const toggleBulkProduct = (id: number) => {
    setBulkProductIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-tg-text">Настройки</h1>

      {/* Section tabs */}
      <div className="flex gap-2 flex-wrap">
        {sections.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setActiveSection(s.id)}
            className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              activeSection === s.id ? 'bg-tg-button text-tg-button-text' : 'bg-tg-secondary text-tg-text'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* --- Основные --- */}
      {activeSection === 'general' && (
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-tg-text">Основные</h2>
          <Input
            label="Название магазина"
            value={shopName}
            onChange={(e) => setShopName(e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-tg-hint mb-1">Валюта</label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
            >
              <option value="RUB">RUB (₽)</option>
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="UAH">UAH (₴)</option>
            </select>
          </div>
          <Input
            label="Адрес магазина (для самовывоза)"
            placeholder="ул. Пример, д. 1"
            value={storeAddress}
            onChange={(e) => setStoreAddress(e.target.value)}
          />
          <p className="text-xs text-tg-hint -mt-2">Если адрес не указан, самовывоз будет недоступен.</p>
          <Input
            label="Город доставки"
            placeholder="Оставьте пустым для доставки по всей России"
            value={deliveryCity}
            onChange={(e) => setDeliveryCity(e.target.value)}
          />
          <p className="text-xs text-tg-hint -mt-2">Если указан, пользователь сможет заказать доставку только в этом городе.</p>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={pickupEnabled} onChange={(e) => setPickupEnabled(e.target.checked)} className="w-5 h-5 rounded" />
              <span className="text-sm text-tg-text">Самовывоз</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={deliveryEnabled} onChange={(e) => setDeliveryEnabled(e.target.checked)} className="w-5 h-5 rounded" />
              <span className="text-sm text-tg-text">Доставка</span>
            </label>
          </div>
          <Input
            label="Минимальная сумма заказа — самовывоз (₽)"
            type="number"
            min={0}
            step={1}
            placeholder="0 = без ограничения"
            value={minOrderAmountPickup}
            onChange={(e) => setMinOrderAmountPickup(e.target.value)}
          />
          <Input
            label="Минимальная сумма заказа — доставка (₽)"
            type="number"
            min={0}
            step={1}
            placeholder="0 = без ограничения"
            value={minOrderAmountDelivery}
            onChange={(e) => setMinOrderAmountDelivery(e.target.value)}
          />
          <Input
            label="Поддержка — @username или ссылка"
            placeholder="@username или https://t.me/username"
            value={supportLink}
            onChange={(e) => setSupportLink(e.target.value)}
          />
          <p className="text-xs text-tg-hint -mt-2">При нажатии кнопки «Поддержка» в профиле откроется чат с указанным пользователем.</p>
          <Button onClick={handleSave} fullWidth>{saved ? '✓ Сохранено!' : 'Сохранить'}</Button>
        </div>
      )}

      {/* --- Администраторы --- */}
      {activeSection === 'admins' && (
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-tg-text">Администраторы</h2>
          {currentTelegramId != null && (
            <p className="text-sm text-tg-hint">
              Ваш Telegram ID: <strong className="text-tg-text">{currentTelegramId}</strong>. Добавьте его в список, чтобы не потерять доступ.
            </p>
          )}
          <div>
            <label className="block text-sm font-medium text-tg-hint mb-1">Telegram ID админов (через запятую)</label>
            <input
              type="text"
              value={adminIds}
              onChange={(e) => setAdminIds(e.target.value)}
              placeholder="123456789, 987654321"
              className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
            />
            <p className="text-xs text-tg-hint mt-1">Пользователи с этими Telegram ID получат доступ к админ-панели. Узнать ID: пользователь пишет боту /start — ID можно увидеть в логах или через @userinfobot.</p>
          </div>
          <Button onClick={handleSave} fullWidth>{saved ? '✓ Сохранено!' : 'Сохранить'}</Button>
        </div>
      )}

      {/* --- Доставка --- */}
      {activeSection === 'delivery' && (
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-tg-text">Доставка</h2>
          {!deliveryEnabled && (
            <p className="text-sm text-tg-hint">Включите доставку в разделе «Основные», чтобы настроить стоимость.</p>
          )}
          {deliveryEnabled && (
            <>
              <Input label="Стоимость доставки (₽)" type="number" min={0} step={1} value={deliveryCost} onChange={(e) => setDeliveryCost(e.target.value)} />
              <Input label="Бесплатная доставка от (₽) — 0 = всегда платная" type="number" min={0} step={1} value={freeDeliveryMinAmount} onChange={(e) => setFreeDeliveryMinAmount(e.target.value)} />
              <p className="text-xs text-tg-hint">Самовывоз не учитывает стоимость доставки.</p>
            </>
          )}
          <Button onClick={handleSave} fullWidth>{saved ? '✓ Сохранено!' : 'Сохранить'}</Button>
        </div>
      )}

      {/* --- Баннеры и каталог --- */}
      {activeSection === 'banners' && (
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-tg-text">Баннеры и каталог</h2>
          <div>
            <span className="block text-sm font-medium text-tg-hint mb-1">Отображение баннеров (для всех)</span>
            <div className="flex gap-2 mb-2">
              <button type="button" onClick={() => setBannerAspectShape('square')} className={`px-3 py-2 rounded-lg text-sm ${bannerAspectShape === 'square' ? 'bg-tg-button text-tg-button-text' : 'bg-tg-bg text-tg-text'}`}>Квадрат</button>
              <button type="button" onClick={() => setBannerAspectShape('rectangle')} className={`px-3 py-2 rounded-lg text-sm ${bannerAspectShape === 'rectangle' ? 'bg-tg-button text-tg-button-text' : 'bg-tg-bg text-tg-text'}`}>Прямоугольник</button>
            </div>
            <div className="flex gap-2 flex-wrap">
              {(['small', 'medium', 'large', 'xl'] as const).map((s) => (
                <button key={s} type="button" onClick={() => setBannerSize(s)} className={`px-3 py-2 rounded-lg text-sm ${bannerSize === s ? 'bg-tg-button text-tg-button-text' : 'bg-tg-bg text-tg-text'}`}>
                  {s === 'small' ? 'Маленький' : s === 'medium' ? 'Средний' : s === 'large' ? 'Большой' : 'Очень большой'}
                </button>
              ))}
            </div>
          </div>
          <div>
            <span className="block text-sm font-medium text-tg-hint mb-1">Размер картинок категорий (в каталоге)</span>
            <div className="flex gap-2 flex-wrap">
              {(['small', 'medium', 'large', 'xlarge'] as const).map((s) => (
                <button key={s} type="button" onClick={() => setCategoryImageSize(s)} className={`px-3 py-2 rounded-lg text-sm ${categoryImageSize === s ? 'bg-tg-button text-tg-button-text' : 'bg-tg-bg text-tg-text'}`}>
                  {s === 'small' ? 'Маленькая' : s === 'medium' ? 'Средняя' : s === 'large' ? 'Большая' : 'Очень большая'}
                </button>
              ))}
            </div>
          </div>
          <Button onClick={handleSave} fullWidth>{saved ? '✓ Сохранено!' : 'Сохранить'}</Button>
        </div>
      )}

      {/* --- Бонусы --- */}
      {activeSection === 'bonuses' && (
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-tg-text">Бонусная система</h2>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={bonusEnabled} onChange={(e) => setBonusEnabled(e.target.checked)} className="w-5 h-5 rounded" />
            <span className="text-sm text-tg-text">Включить бонусную систему</span>
          </label>
          {bonusEnabled && (
            <>
              <div className="pl-0 space-y-2">
                <span className="block text-xs font-medium text-tg-hint">Приветственные бонусы</span>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={bonusWelcomeEnabled} onChange={(e) => setBonusWelcomeEnabled(e.target.checked)} className="w-4 h-4 rounded" />
                  <span className="text-sm text-tg-text">Включить</span>
                </label>
                <Input label="Сумма бонусов при регистрации" type="number" min={0} value={bonusWelcomeAmount} onChange={(e) => setBonusWelcomeAmount(e.target.value)} />
              </div>
              <div className="pl-0 space-y-2">
                <span className="block text-xs font-medium text-tg-hint">Бонусы за покупки (начисляются при статусе «Выполнен»)</span>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={bonusPurchaseEnabled} onChange={(e) => setBonusPurchaseEnabled(e.target.checked)} className="w-4 h-4 rounded" />
                  <span className="text-sm text-tg-text">Включить</span>
                </label>
                <Input label="Процент от суммы заказа" type="number" min={0} step={0.1} value={bonusPurchasePercent} onChange={(e) => setBonusPurchasePercent(e.target.value)} />
              </div>
              <div className="pl-0 space-y-2">
                <span className="block text-xs font-medium text-tg-hint">Трата бонусов на заказ</span>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={bonusSpendEnabled} onChange={(e) => setBonusSpendEnabled(e.target.checked)} className="w-4 h-4 rounded" />
                  <span className="text-sm text-tg-text">Разрешить списание бонусов при оформлении</span>
                </label>
                <div className="flex gap-2">
                  <button type="button" onClick={() => setBonusSpendLimitType('percent')} className={`px-3 py-2 rounded-lg text-sm ${bonusSpendLimitType === 'percent' ? 'bg-tg-button text-tg-button-text' : 'bg-tg-bg text-tg-text'}`}>% от заказа</button>
                  <button type="button" onClick={() => setBonusSpendLimitType('fixed')} className={`px-3 py-2 rounded-lg text-sm ${bonusSpendLimitType === 'fixed' ? 'bg-tg-button text-tg-button-text' : 'bg-tg-bg text-tg-text'}`}>Фикс. сумма</button>
                </div>
                <Input label={bonusSpendLimitType === 'percent' ? 'Макс. процент от суммы заказа' : 'Макс. сумма (₽)'} type="number" min={0} step={bonusSpendLimitType === 'percent' ? 1 : 0.01} value={bonusSpendLimitValue} onChange={(e) => setBonusSpendLimitValue(e.target.value)} />
              </div>
            </>
          )}
          <Button onClick={handleSave} fullWidth>{saved ? '✓ Сохранено!' : 'Сохранить'}</Button>
        </div>
      )}

      {/* --- Категории --- */}
      {activeSection === 'categories' && (
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-tg-text">Категории</h2>

        {/* Add category form */}
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              placeholder="Название категории"
              value={newCatName}
              onChange={(e) => setNewCatName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddCategory()}
            />
            <Button
              size="sm"
              onClick={handleAddCategory}
              disabled={!newCatName.trim() || catLoading}
              className="flex-shrink-0"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <div>
            <label className="block text-sm font-medium text-tg-hint mb-1">Родительская категория</label>
            <select
              value={newCatParentId ?? ''}
              onChange={(e) => setNewCatParentId(e.target.value === '' ? null : Number(e.target.value))}
              className="w-full px-4 py-2.5 rounded-xl bg-tg-bg text-tg-text border-none outline-none"
            >
              <option value="">Без родителя</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <span className="block text-sm font-medium text-tg-hint mb-1">Картинка категории (необязательно)</span>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={(e) => handleCategoryImageUpload(e, setNewCatImageUrl)}
              disabled={uploadingCatImage}
              className="block w-full text-sm text-tg-text file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-tg-bg file:text-tg-text"
            />
            {uploadingCatImage && <span className="text-xs text-tg-hint">Загрузка…</span>}
            {newCatImageUrl && (
              <div className="mt-2 flex items-center gap-2">
                <img src={newCatImageUrl} alt="" className="w-14 h-14 object-cover rounded-lg bg-tg-bg" />
                <button type="button" onClick={() => setNewCatImageUrl('')} className="text-xs text-tg-link">Убрать</button>
              </div>
            )}
          </div>
        </div>

        {/* Categories list: корни; подкатегории видны только у раскрытых */}
        {displayCategories.length === 0 ? (
          <p className="text-sm text-tg-hint">Категорий пока нет</p>
        ) : (
          <div className="space-y-2">
            {displayCategories.map((cat, index) => {
              const isChild = cat.parent_id != null;
              const parentId = cat.parent_id ?? null;
              const hasChildren = categories.some((c) => (c.parent_id ?? null) === cat.id);
              const isExpanded = expandedCategoryIds.includes(cat.id);
              const prevSibling = index > 0 && (displayCategories[index - 1].parent_id ?? null) === parentId;
              const nextSibling = index < displayCategories.length - 1 && (displayCategories[index + 1].parent_id ?? null) === parentId;
              const isAllCategory = cat.slug === 'all';
              return (
              <div
                key={cat.id}
                className={`bg-tg-secondary rounded-xl p-3 flex items-center gap-2 ${isChild ? 'ml-4' : ''}`}
              >
                {editingCatId === cat.id ? (
                  // Editing mode (для категории «Все» — только картинка, без имени и родителя)
                  <>
                    <div className="flex-1 min-w-0 space-y-1">
                      {!isAllCategory && (
                        <>
                          <input
                            type="text"
                            value={editingCatName}
                            onChange={(e) => setEditingCatName(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveCategory();
                              if (e.key === 'Escape') handleCancelEdit();
                            }}
                            className="w-full px-3 py-1.5 rounded-lg bg-tg-bg text-tg-text text-sm border-none outline-none"
                            autoFocus
                          />
                          <select
                            value={editingCatParentId ?? ''}
                            onChange={(e) => setEditingCatParentId(e.target.value === '' ? null : Number(e.target.value))}
                            className="w-full px-3 py-1.5 rounded-lg bg-tg-bg text-tg-text text-sm border-none outline-none"
                          >
                            <option value="">Без родителя</option>
                            {categories.filter((c) => c.id !== cat.id).map((c) => (
                              <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                          </select>
                        </>
                      )}
                      {isAllCategory && <p className="text-xs text-tg-hint">Только картинка для категории «Все»</p>}
                      <div>
                        <span className="block text-xs text-tg-hint mb-0.5">Картинка</span>
                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp,image/gif"
                          onChange={(e) => handleCategoryImageUpload(e, setEditingCatImageUrl)}
                          disabled={uploadingCatImage}
                          className="block w-full text-xs text-tg-text file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:bg-tg-bg"
                        />
                        {editingCatImageUrl && (
                          <div className="mt-1 flex items-center gap-2">
                            <img src={editingCatImageUrl} alt="" className="w-12 h-12 object-cover rounded bg-tg-bg" />
                            <button type="button" onClick={() => setEditingCatImageUrl('')} className="text-xs text-tg-link">Убрать</button>
                          </div>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={handleSaveCategory}
                      className="w-8 h-8 rounded-lg bg-green-500 text-white flex items-center justify-center flex-shrink-0"
                      disabled={catLoading}
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="w-8 h-8 rounded-lg bg-tg-bg text-tg-hint flex items-center justify-center flex-shrink-0"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </>
                ) : (
                  // View mode
                  <>
                    {hasChildren ? (
                      <button
                        type="button"
                        onClick={() => toggleCategoryExpanded(cat.id)}
                        className="w-7 h-7 flex items-center justify-center rounded-lg bg-tg-bg text-tg-hint flex-shrink-0"
                        aria-label={isExpanded ? 'Свернуть' : 'Развернуть'}
                      >
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </button>
                    ) : (
                      <span className="w-7 flex-shrink-0" aria-hidden />
                    )}
                    {cat.image_url && (
                      <img src={cat.image_url} alt="" className="w-10 h-10 object-cover rounded-lg bg-tg-bg flex-shrink-0" />
                    )}
                    <span className="flex-1 text-sm text-tg-text truncate min-w-0">
                      {cat.name}
                    </span>

                    {/* Sort controls (within siblings only); у категории «Все» порядок не меняется */}
                    {!isAllCategory && (
                    <div className="flex flex-col flex-shrink-0">
                      <button
                        onClick={() => handleMoveCategory(cat.id, 'up')}
                        disabled={!prevSibling || catLoading}
                        className="w-6 h-4 flex items-center justify-center text-tg-hint disabled:opacity-30"
                      >
                        <ChevronUp className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleMoveCategory(cat.id, 'down')}
                        disabled={!nextSibling || catLoading}
                        className="w-6 h-4 flex items-center justify-center text-tg-hint disabled:opacity-30"
                      >
                        <ChevronDown className="w-3 h-3" />
                      </button>
                    </div>
                    )}
                    {isAllCategory && <span className="w-6 flex-shrink-0" aria-hidden />}

                    <button
                      onClick={() => handleStartEdit(cat)}
                      className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center flex-shrink-0"
                    >
                      <Edit className="w-4 h-4 text-tg-link" />
                    </button>
                    {!isAllCategory && (
                    <button
                      onClick={() => handleDeleteCategory(cat.id)}
                      className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center flex-shrink-0"
                      disabled={catLoading}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                    )}
                  </>
                )}
              </div>
            );
            })}
          </div>
        )}
      </div>
      )}

      {/* --- Модификации --- */}
      {activeSection === 'modifications' && (
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-tg-text">Модификации</h2>
        <p className="text-sm text-tg-hint">Типы вариантов для товаров. Укажите название и варианты через запятую (например: S, M, L).</p>
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              placeholder="Название (например: Размер)"
              value={newModName}
              onChange={(e) => setNewModName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddModType()}
            />
            <Button
              size="sm"
              onClick={handleAddModType}
              disabled={!newModName.trim() || modLoading}
              className="flex-shrink-0"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <Input
            placeholder="Варианты через запятую (например: S, M, L, XL)"
            value={newModValues}
            onChange={(e) => setNewModValues(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddModType()}
          />
        </div>
        {modTypes.length === 0 ? (
          <p className="text-sm text-tg-hint">Типов модификаций пока нет</p>
        ) : (
          <div className="space-y-3">
            {modTypes.map((mt, index) => (
              <div key={mt.id} className="bg-tg-secondary rounded-xl p-3 space-y-2">
                {editingModId === mt.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={editingModName}
                      onChange={(e) => setEditingModName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveModType();
                        if (e.key === 'Escape') handleCancelEditMod();
                      }}
                      className="flex-1 px-3 py-1.5 rounded-lg bg-tg-bg text-tg-text text-sm border-none outline-none"
                      autoFocus
                    />
                    <button
                      onClick={handleSaveModType}
                      className="w-8 h-8 rounded-lg bg-green-500 text-white flex items-center justify-center flex-shrink-0"
                      disabled={modLoading}
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={handleCancelEditMod}
                      className="w-8 h-8 rounded-lg bg-tg-bg text-tg-hint flex items-center justify-center flex-shrink-0"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-2">
                      <span className="flex-1 text-sm font-medium text-tg-text">{mt.name}</span>
                      <div className="flex flex-col flex-shrink-0">
                        <button
                          onClick={() => handleMoveModType(mt.id, 'up')}
                          disabled={index === 0 || modLoading}
                          className="w-6 h-4 flex items-center justify-center text-tg-hint disabled:opacity-30"
                        >
                          <ChevronUp className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleMoveModType(mt.id, 'down')}
                          disabled={index === modTypes.length - 1 || modLoading}
                          className="w-6 h-4 flex items-center justify-center text-tg-hint disabled:opacity-30"
                        >
                          <ChevronDown className="w-3 h-3" />
                        </button>
                      </div>
                      <button
                        onClick={() => handleStartEditMod(mt)}
                        className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center flex-shrink-0"
                      >
                        <Edit className="w-4 h-4 text-tg-link" />
                      </button>
                      <button
                        onClick={() => handleDeleteModType(mt.id)}
                        className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center flex-shrink-0"
                        disabled={modLoading}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5 pl-1">
                      {(mt.values || []).map((v) => (
                        <span
                          key={v.id}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-tg-bg text-tg-text text-xs"
                        >
                          {v.value}
                          <button
                            type="button"
                            onClick={() => handleDeleteModValue(mt.id, v.id)}
                            disabled={modLoading}
                            className="text-red-500 hover:bg-red-500/10 rounded p-0.5"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                      {newValueForTypeId === mt.id ? (
                        <span className="inline-flex gap-1">
                          <input
                            type="text"
                            value={newValueText}
                            onChange={(e) => setNewValueText(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleAddModValue(mt.id);
                              if (e.key === 'Escape') {
                                setNewValueForTypeId(null);
                                setNewValueText('');
                              }
                            }}
                            placeholder="Значение"
                            className="w-20 px-2 py-0.5 rounded-lg bg-tg-bg text-tg-text text-xs border-none outline-none"
                            autoFocus
                          />
                          <button
                            type="button"
                            onClick={() => handleAddModValue(mt.id)}
                            disabled={!newValueText.trim() || modLoading}
                            className="rounded-lg bg-green-500 text-white px-2 py-0.5 text-xs"
                          >
                            +
                          </button>
                          <button
                            type="button"
                            onClick={() => { setNewValueForTypeId(null); setNewValueText(''); }}
                            className="text-tg-hint text-xs"
                          >
                            Отмена
                          </button>
                        </span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setNewValueForTypeId(mt.id)}
                          className="text-xs text-tg-link"
                        >
                          + Добавить значение
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      )}

      {/* --- Массовое изменение цен --- */}
      {activeSection === 'bulk' && (
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-tg-text">Массовое изменение цен</h2>

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Область</label>
          <select
            value={bulkScope}
            onChange={(e) => {
              setBulkScope(e.target.value as BulkPriceScope);
              setBulkPreviewTotal(null);
              setBulkError('');
            }}
            className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
          >
            <option value="all">Все товары</option>
            <option value="product_ids">По выбору товаров</option>
            <option value="price_equals">Где цена равна</option>
            <option value="price_range">Где цена в диапазоне</option>
            <option value="category">По категории</option>
          </select>
        </div>

        {bulkScope === 'product_ids' && (
          <div className="space-y-2">
            <p className="text-sm text-tg-hint">Загрузите список и отметьте товары</p>
            <Button size="sm" onClick={() => loadBulkProducts(1)} disabled={bulkLoading}>
              {bulkProducts.length === 0 ? 'Загрузить товары' : 'Обновить список'}
            </Button>
            {bulkProducts.length > 0 && (
              <div className="max-h-48 overflow-y-auto space-y-1 rounded-xl bg-tg-secondary p-2">
                {bulkProducts.map((p) => (
                  <label key={p.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={bulkProductIds.includes(p.id)}
                      onChange={() => toggleBulkProduct(p.id)}
                      className="w-4 h-4 rounded"
                    />
                    <span className="text-sm text-tg-text truncate flex-1">{p.name}</span>
                    <span className="text-sm text-tg-hint">{p.price}</span>
                  </label>
                ))}
                {bulkProducts.length >= 50 && (
                  <Button size="sm" onClick={() => loadBulkProducts(bulkProductsPage + 1)} disabled={bulkLoading}>
                    Загрузить ещё
                  </Button>
                )}
              </div>
            )}
            <p className="text-xs text-tg-hint">Выбрано: {bulkProductIds.length}</p>
          </div>
        )}

        {bulkScope === 'price_equals' && (
          <Input
            type="number"
            step="0.01"
            min="0"
            label="Цена равна"
            placeholder="0"
            value={bulkPriceEquals}
            onChange={(e) => setBulkPriceEquals(e.target.value)}
          />
        )}

        {bulkScope === 'price_range' && (
          <div className="flex gap-2">
            <Input
              type="number"
              step="0.01"
              min="0"
              label="Мин. цена"
              placeholder="0"
              value={bulkPriceMin}
              onChange={(e) => setBulkPriceMin(e.target.value)}
            />
            <Input
              type="number"
              step="0.01"
              min="0"
              label="Макс. цена"
              placeholder="—"
              value={bulkPriceMax}
              onChange={(e) => setBulkPriceMax(e.target.value)}
            />
          </div>
        )}

        {bulkScope === 'category' && (
          <div>
            <label className="block text-sm font-medium text-tg-hint mb-1">Категория</label>
            <select
              value={bulkCategoryId}
              onChange={(e) => setBulkCategoryId(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
            >
              <option value="">Выберите категорию</option>
              {flattenedCategories.map((c) => (
                <option key={c.id} value={c.id}>{c.parent_id ? '— ' : ''}{c.name}</option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Операция</label>
          <select
            value={bulkOperation}
            onChange={(e) => setBulkOperation(e.target.value as BulkPriceOperation)}
            className="w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none"
          >
            <option value="add_amount">Увеличить на сумму</option>
            <option value="subtract_amount">Уменьшить на сумму</option>
            <option value="add_percent">Увеличить на %</option>
            <option value="subtract_percent">Уменьшить на %</option>
            <option value="set_to">Установить цену на</option>
          </select>
        </div>

        <Input
          type="number"
          step={bulkOperation.includes('percent') ? '0.1' : '0.01'}
          min="0"
          label={bulkOperation === 'set_to' ? 'Новая цена' : bulkOperation.includes('percent') ? 'Процент' : 'Сумма'}
          placeholder={bulkOperation === 'set_to' ? '0' : bulkOperation.includes('percent') ? '10' : '0'}
          value={bulkValue}
          onChange={(e) => setBulkValue(e.target.value)}
        />

        <Input
          type="number"
          step="1"
          min="0"
          label="Округлить до (необязательно)"
          placeholder="10, 50, 100…"
          value={bulkRoundTo}
          onChange={(e) => setBulkRoundTo(e.target.value)}
        />

        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" onClick={fetchBulkPreview} disabled={bulkLoading}>
            Показать количество
          </Button>
          {bulkPreviewTotal !== null && (
            <span className="text-sm text-tg-hint">Будет изменено: {bulkPreviewTotal} товаров</span>
          )}
        </div>

        {bulkError && <p className="text-sm text-red-500">{bulkError}</p>}
        {bulkSuccess && <p className="text-sm text-green-600">{bulkSuccess}</p>}

        <Button onClick={handleBulkApply} fullWidth disabled={bulkLoading}>
          {bulkLoading ? 'Применяем…' : 'Применить'}
        </Button>
      </div>
      )}
    </div>
  );
};
