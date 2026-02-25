import React, { useEffect, useState, useRef } from 'react';
import { Plus, Trash2, Edit, Upload, X, Film } from 'lucide-react';
import {
  adminGetProducts, adminGetCategories, adminGetModificationTypes,
  adminCreateProduct, adminDeleteProduct, adminUpdateProduct,
  adminUploadMedia, adminDeleteMedia, adminGetProductVariants, adminSetProductVariants,
} from '../api/endpoints';
import type { Product, Category, ProductMedia, ModificationType } from '../types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';

export const AdminProductsPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [modTypes, setModTypes] = useState<ModificationType[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategoryId, setFilterCategoryId] = useState('');

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [oldPrice, setOldPrice] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [categoryIds, setCategoryIds] = useState<number[]>([]);
  const [stock, setStock] = useState('0');

  // Media state — existing (from server) + pending (local files for new products)
  const [mediaItems, setMediaItems] = useState<ProductMedia[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  // Variants: one modification type + list of (value, quantity)
  const [variantModTypeId, setVariantModTypeId] = useState<string>('');
  const [variantRows, setVariantRows] = useState<{ value: string; quantity: number }[]>([]);

  const fetchProducts = () => {
    setLoading(true);
    const params: { per_page: number; category_id?: number; search?: string } = { per_page: 100 };
    if (filterCategoryId) params.category_id = Number(filterCategoryId);
    if (searchQuery.trim()) params.search = searchQuery.trim();
    adminGetProducts(params)
      .then(({ data }) => setProducts(data.items))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchProducts();
  }, [filterCategoryId, searchQuery]);

  useEffect(() => {
    adminGetCategories().then(({ data }) => setCategories(data));
    adminGetModificationTypes().then(({ data }) => setModTypes(data));
  }, []);

  const resetForm = () => {
    setName('');
    setDescription('');
    setPrice('');
    setOldPrice('');
    setImageUrl('');
    setCategoryIds([]);
    setStock('0');
    setEditId(null);
    setMediaItems([]);
    setPendingFiles([]);
    setVariantModTypeId('');
    setVariantRows([]);
    setShowForm(false);
    setErrorMsg('');
  };

  const handleEdit = async (product: Product) => {
    setEditId(product.id);
    setName(product.name);
    setDescription(product.description || '');
    setPrice(Number(product.price).toFixed(2));
    setOldPrice(product.old_price != null ? Number(product.old_price).toFixed(2) : '');
    setImageUrl(product.image_url || '');
    setCategoryIds(product.category_ids?.length ? product.category_ids : (product.category_id != null ? [product.category_id] : []));
    setStock(String(product.stock_quantity));
    setMediaItems(product.media || []);
    setPendingFiles([]);
    setErrorMsg('');
    try {
      const { data: variants } = await adminGetProductVariants(product.id);
      if (variants.length > 0) {
        const typeId = variants[0].modification_type_id;
        setVariantModTypeId(String(typeId));
        const modType = modTypes.find((m) => m.id === typeId);
        if (modType?.values?.length) {
          setVariantRows(
            modType.values.map((v) => ({
              value: v.value,
              quantity: variants.find((ev) => ev.value === v.value)?.quantity ?? 0,
            }))
          );
        } else {
          setVariantRows(variants.map((v) => ({ value: v.value, quantity: v.quantity })));
        }
      } else {
        setVariantModTypeId('');
        setVariantRows([]);
      }
    } catch {
      setVariantModTypeId('');
      setVariantRows([]);
    }
  };

  const handleSubmit = async () => {
    setErrorMsg('');
    setSaving(true);

    const totalVariantQty = variantModTypeId
      ? variantRows.reduce((s, r) => s + (typeof r.quantity === 'number' ? r.quantity : 0), 0)
      : null;
    const roundPrice = (v: number) => Math.round(v * 100) / 100;
    const priceNum = parseFloat(price);
    const oldPriceNum = oldPrice ? parseFloat(oldPrice) : null;
    const data = {
      name,
      description: description || null,
      price: Number.isNaN(priceNum) ? 0 : roundPrice(priceNum),
      old_price: oldPriceNum != null && !Number.isNaN(oldPriceNum) ? roundPrice(oldPriceNum) : null,
      image_url: imageUrl || null,
      category_ids: categoryIds,
      stock_quantity: variantModTypeId ? totalVariantQty! : parseInt(stock),
      is_available: true,
    };

    try {
      let productId = editId;

      if (editId) {
        await adminUpdateProduct(editId, data);
      } else {
        const { data: newProduct } = await adminCreateProduct(data);
        productId = newProduct.id;
      }

      // Save variants (one modification type per product, list of value/quantity)
      if (productId) {
        const typeId = variantModTypeId ? parseInt(variantModTypeId, 10) : 0;
        const validRows = variantRows.filter((r) => r.value.trim() !== '');
        if (typeId && validRows.length > 0) {
          await adminSetProductVariants(productId, validRows.map((r) => ({
            modification_type_id: typeId,
            value: r.value.trim(),
            quantity: typeof r.quantity === 'number' ? r.quantity : parseInt(String(r.quantity), 10) || 0,
          })));
        } else {
          await adminSetProductVariants(productId, []);
        }
      }

      // Upload any pending files (e.g. video for new product)
      const uploadErrors: string[] = [];
      if (productId && pendingFiles.length > 0) {
        setUploading(true);
        for (const file of pendingFiles) {
          try {
            await adminUploadMedia(productId, file);
          } catch (err: any) {
            const msg = err?.response?.data?.detail ?? err?.message ?? 'неизвестная ошибка';
            uploadErrors.push(`${file.name}: ${msg}`);
            console.error('Upload error for file:', file.name, err);
          }
        }
        setUploading(false);
        if (uploadErrors.length > 0) {
          setEditId(productId);
          setMediaItems([]);
          setPendingFiles([]);
          setErrorMsg(`Товар сохранён. Не удалось загрузить файлы — попробуйте загрузить снова: ${uploadErrors.join('; ')}`);
          fetchProducts();
          setSaving(false);
          return;
        }
      }

      resetForm();
      fetchProducts();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setErrorMsg(typeof detail === 'string' ? detail : 'Ошибка сохранения товара');
      console.error('Product save error:', err);
    }

    setSaving(false);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Удалить товар?')) {
      await adminDeleteProduct(id);
      fetchProducts();
    }
  };

  // Handle file selection — for existing products upload immediately, for new ones collect locally
  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    if (editId) {
      // Existing product — upload immediately
      setUploading(true);
      try {
        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          const { data: media } = await adminUploadMedia(editId, file);
          setMediaItems((prev) => [...prev, media]);
        }
      } catch (err) {
        console.error('Upload error:', err);
        alert('Ошибка загрузки файла');
      }
      setUploading(false);
    } else {
      // New product — collect files locally
      const newFiles = Array.from(files);
      setPendingFiles((prev) => [...prev, ...newFiles]);
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDeleteMedia = async (mediaId: number) => {
    if (!editId) return;
    try {
      await adminDeleteMedia(editId, mediaId);
      setMediaItems((prev) => prev.filter((m) => m.id !== mediaId));
    } catch {
      alert('Ошибка удаления');
    }
  };

  const handleRemovePendingFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  // Get first media thumbnail for list display
  const getProductThumbnail = (p: Product) => {
    if (p.media && p.media.length > 0) {
      const first = p.media.find((m) => m.media_type === 'image') || p.media[0];
      return first.url;
    }
    return p.image_url;
  };

  const renderProductForm = (options: { showCancel?: boolean }) => (
    <div className="space-y-3">
      <Input label="Название" value={name} onChange={(e) => setName(e.target.value)} />
      <Textarea label="Описание" value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Цена" type="number" value={price} onChange={(e) => setPrice(e.target.value)} />
        <Input label="Старая цена" type="number" value={oldPrice} onChange={(e) => setOldPrice(e.target.value)} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-tg-hint mb-1">Категории (можно несколько)</label>
          <div className="max-h-32 overflow-y-auto rounded-xl bg-tg-bg p-2 space-y-1">
            {(() => {
              const flat: { id: number; name: string; depth: number }[] = [];
              const walk = (list: Category[], depth = 0) => {
                list.filter((c) => c.slug !== 'all').forEach((c) => {
                  flat.push({ id: c.id, name: c.name, depth });
                  if (c.children?.length) walk(c.children, depth + 1);
                });
              };
              walk(categories);
              return flat.map((c) => (
                <label key={c.id} className="flex items-center gap-2 py-0.5 cursor-pointer" style={{ paddingLeft: c.depth * 12 }}>
                  <input
                    type="checkbox"
                    checked={categoryIds.includes(c.id)}
                    onChange={(e) => {
                      if (e.target.checked) setCategoryIds((prev) => [...prev, c.id]);
                      else setCategoryIds((prev) => prev.filter((id) => id !== c.id));
                    }}
                    className="rounded border-tg-hint"
                  />
                  <span className="text-sm text-tg-text">{c.name}</span>
                </label>
              ));
            })()}
          </div>
        </div>
        {variantModTypeId ? (
          <div>
            <label className="block text-sm font-medium text-tg-hint mb-1">Остаток всего</label>
            <div className="px-4 py-2.5 rounded-xl bg-tg-bg text-tg-text border-none">
              {variantRows.reduce((s, r) => s + (typeof r.quantity === 'number' ? r.quantity : 0), 0)} шт.
            </div>
            <p className="text-xs text-tg-hint mt-0.5">Сумма по вариантам выше</p>
          </div>
        ) : (
          <Input label="Остаток" type="number" value={stock} onChange={(e) => setStock(e.target.value)} />
        )}
      </div>
      <div className="space-y-2">
        <label className="block text-sm font-medium text-tg-hint">Варианты (модификация)</label>
        <select
          value={variantModTypeId}
          onChange={(e) => {
            const typeId = e.target.value;
            setVariantModTypeId(typeId);
            if (!typeId) { setVariantRows([]); return; }
            const selected = modTypes.find((mt) => String(mt.id) === typeId);
            if (selected?.values?.length) setVariantRows(selected.values.map((v) => ({ value: v.value, quantity: 0 })));
            else setVariantRows([]);
          }}
          className="w-full px-4 py-2.5 rounded-xl bg-tg-bg text-tg-text border-none outline-none"
        >
          <option value="">Без вариантов</option>
          {modTypes.map((mt) => (
            <option key={mt.id} value={mt.id}>{mt.name}</option>
          ))}
        </select>
        {variantModTypeId && (
          <div className="space-y-2 pl-2 border-l-2 border-tg-hint/30">
            {variantRows.map((row, idx) => (
              <div key={row.value} className="flex gap-2 items-center">
                <span className="text-sm text-tg-text w-16 flex-shrink-0">{row.value}</span>
                <Input
                  type="number"
                  min={0}
                  placeholder="Кол-во"
                  value={row.quantity}
                  onChange={(e) =>
                    setVariantRows((prev) => {
                      const next = [...prev];
                      next[idx] = { ...next[idx], quantity: parseInt(e.target.value, 10) || 0 };
                      return next;
                    })
                  }
                  className="w-24"
                />
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="space-y-2">
        <label className="block text-sm font-medium text-tg-hint">Фото и видео товара</label>
        {mediaItems.length > 0 && (
          <div className="grid grid-cols-4 gap-2">
            {mediaItems.map((m) => (
              <div key={m.id} className="relative aspect-square rounded-lg overflow-hidden bg-gray-100 group">
                {m.media_type === 'video' ? (
                  <div className="w-full h-full flex items-center justify-center bg-gray-200"><Film className="w-6 h-6 text-gray-500" /></div>
                ) : (
                  <img src={m.url} alt="" className="w-full h-full object-cover" />
                )}
                <button type="button" onClick={() => handleDeleteMedia(m.id)} className="absolute top-1 right-1 w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
        {pendingFiles.length > 0 && (
          <div className="grid grid-cols-4 gap-2">
            {pendingFiles.map((file, index) => (
              <div key={index} className="relative aspect-square rounded-lg overflow-hidden bg-gray-100 group">
                {file.type.startsWith('video/') ? (
                  <div className="w-full h-full flex items-center justify-center bg-gray-200"><Film className="w-6 h-6 text-gray-500" /></div>
                ) : (
                  <img src={URL.createObjectURL(file)} alt="" className="w-full h-full object-cover" />
                )}
                <button type="button" onClick={() => handleRemovePendingFile(index)} className="absolute top-1 right-1 w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${dragOver ? 'border-tg-button bg-tg-button/5' : 'border-tg-hint/30 hover:border-tg-button/50'}`}
        >
          <input ref={fileInputRef} type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm" className="hidden" onChange={(e) => handleFileSelect(e.target.files)} />
          {uploading ? <div className="text-sm text-tg-hint">Загрузка...</div> : <><Upload className="w-6 h-6 text-tg-hint mx-auto" /><p className="text-sm text-tg-hint">Перетащите файлы сюда или нажмите</p></>}
        </div>
      </div>
      {errorMsg && <div className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2">{errorMsg}</div>}
      <div className="flex gap-2">
        {options.showCancel && (
          <Button variant="secondary" onClick={() => { setEditId(null); setErrorMsg(''); }}>Отмена</Button>
        )}
        <Button onClick={handleSubmit} disabled={!name || !price || saving}>
          {saving ? (uploading ? 'Загрузка файлов...' : 'Сохранение...') : editId ? 'Сохранить' : 'Создать'}
        </Button>
      </div>
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-tg-text">Товары</h1>
        <Button size="sm" onClick={() => { resetForm(); setShowForm(!showForm); }}>
          <Plus className="w-4 h-4 mr-1" />
          {showForm ? 'Закрыть' : 'Добавить'}
        </Button>
      </div>

      {/* Search and category filter */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <input
          type="text"
          placeholder="Поиск по названию..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 min-w-[140px] px-4 py-2 rounded-xl bg-tg-secondary text-tg-text border-none outline-none focus:ring-2 focus:ring-tg-button"
        />
        <select
          value={filterCategoryId}
          onChange={(e) => setFilterCategoryId(e.target.value)}
          className="px-4 py-2 rounded-xl bg-tg-secondary text-tg-text border-none outline-none focus:ring-2 focus:ring-tg-button"
        >
          <option value="">Все категории</option>
          {categories.filter((c) => c.slug !== 'all').map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Add form (only when adding new, not when editing inline) */}
      {showForm && !editId && (
        <div className="bg-tg-secondary rounded-2xl p-4 mb-4">
          <h3 className="font-semibold text-tg-text mb-3">Новый товар</h3>
          {renderProductForm({ showCancel: false })}
        </div>
      )}

      {/* Products list */}
      <div className="space-y-2">
        {products.map((p) => {
          const thumbnail = getProductThumbnail(p);
          const mediaCount = p.media?.length || 0;
          const totalStock = p.variants?.length
            ? p.variants.reduce((s, v) => s + (v.quantity ?? 0), 0)
            : p.stock_quantity;
          return (
            <div key={p.id}>
              <div className="bg-tg-secondary rounded-xl p-3 flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-gray-100 flex-shrink-0 overflow-hidden relative">
                  {thumbnail ? (
                    <img src={thumbnail} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-lg">📦</div>
                  )}
                  {mediaCount > 1 && (
                    <div className="absolute bottom-0 right-0 bg-black/60 text-white text-[9px] px-1 rounded-tl">
                      {mediaCount}
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-tg-text truncate">{p.name}</div>
                  <div className="text-sm font-bold text-tg-text">
                    {p.price} ₽
                    <span className="text-xs text-tg-hint ml-2">
                      {totalStock > 0 ? `(${totalStock} шт.)` : 'нет'}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleEdit(p)}
                    className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center"
                  >
                    <Edit className="w-4 h-4 text-tg-link" />
                  </button>
                  <button
                    onClick={() => handleDelete(p.id)}
                    className="w-8 h-8 rounded-lg bg-tg-bg flex items-center justify-center"
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
              {editId === p.id && (
                <div className="mt-2 rounded-xl bg-tg-bg/50 p-4 border border-tg-hint/20">
                  {renderProductForm({ showCancel: true })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
