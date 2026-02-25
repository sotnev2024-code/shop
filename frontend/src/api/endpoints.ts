import api from './client';
import type {
  AppConfig,
  Banner,
  BulkPriceRequest,
  BulkPriceResponse,
  CartResponse,
  Category,
  ModificationType,
  Order,
  OrderListResponse,
  OwnerConfig,
  Product,
  ProductListResponse,
  ProductVariant,
  PromoCheckResponse,
  PromoCode,
  Stats,
} from '../types';

// Config
export const getConfig = () => api.get<AppConfig>('/config');

// Categories
export const getCategories = () => api.get<Category[]>('/categories');

// Banners (public, for catalog)
export const getBanners = () => api.get<Banner[]>('/banners');

// Products
export const getProducts = (params: {
  page?: number;
  per_page?: number;
  category_id?: number;
  search?: string;
  min_price?: number;
  max_price?: number;
  in_stock?: boolean;
  sort_by?: string;
  sort_order?: string;
}) => api.get<ProductListResponse>('/products', { params });

export const getProduct = (id: number) => api.get<Product>(`/products/${id}`);

// Cart
export const getCart = () => api.get<CartResponse>('/cart');
export const addToCart = (
  product_id: number,
  quantity: number = 1,
  modification_type_id?: number | null,
  modification_value?: string | null
) =>
  api.post('/cart', {
    product_id,
    quantity,
    ...(modification_type_id != null && { modification_type_id }),
    ...(modification_value != null && modification_value !== '' && { modification_value }),
  });
export const updateCartItem = (item_id: number, quantity: number) =>
  api.patch(`/cart/${item_id}`, { quantity });
export const removeFromCart = (item_id: number) => api.delete(`/cart/${item_id}`);
export const clearCart = () => api.delete('/cart');
export const validateCart = () => api.post<{
  items: import('../types').CartItem[];
  total_price: number;
  total_items: number;
  removed: Array<{ product_id: number; product_name: string; old_quantity: number }>;
  adjusted: Array<{ product_id: number; product_name: string; old_quantity: number; new_quantity: number }>;
}>('/cart/validate');

// Favorites
export const getFavorites = () => api.get<Product[]>('/favorites');
export const addToFavorites = (product_id: number) =>
  api.post(`/favorites/${product_id}`);
export const removeFromFavorites = (product_id: number) =>
  api.delete(`/favorites/${product_id}`);
export const validateFavorites = () =>
  api.post<{ removed: Array<{ product_id: number; product_name: string }> }>('/favorites/validate');

// User (me, bonuses)
export const getMe = () => api.get<{ bonus_balance: number }>('/user/me');
export const getBonusTransactions = (params?: { limit?: number; offset?: number }) =>
  api.get<{ items: Array<{ id: number; amount: number; kind: string; order_id: number | null; created_at: string }> }>('/user/bonus-transactions', { params });

// Orders
export const createOrder = (data: {
  customer_name: string;
  customer_phone: string;
  address?: string;
  address_coords?: { lat: number; lng: number };
  delivery_type?: string;
  delivery_service?: string;
  promo_code?: string;
  bonus_to_use?: number;
}) => api.post<Order>('/orders', data);

export const getOrders = () => api.get<OrderListResponse>('/orders');
export const getOrder = (id: number) => api.get<Order>(`/orders/${id}`);

// Promo
export const checkPromo = (code: string, cart_total?: number, delivery_type?: string) =>
  api.post<PromoCheckResponse>('/promo/check', { code, cart_total, delivery_type });

// Payments
export const createPayment = (order_id: number) =>
  api.post(`/payments/create/${order_id}`);
export const confirmPayment = (order_id: number) =>
  api.post(`/payments/confirm/${order_id}`);

// Admin
export const getStats = () => api.get<Stats>('/admin/stats');
export const adminGetOrders = (params?: { status?: string; page?: number }) =>
  api.get<OrderListResponse>('/admin/orders', { params });
export const adminUpdateOrder = (id: number, data: { status: string; tracking_number?: string }) =>
  api.patch<Order>(`/admin/orders/${id}`, data);
export const adminGetProducts = (params?: {
  page?: number;
  per_page?: number;
  category_id?: number;
  price_equals?: number;
  price_min?: number;
  price_max?: number;
}) => api.get<ProductListResponse>('/admin/products', { params });
export const adminCreateProduct = (data: any) => api.post<Product>('/admin/products', data);
export const adminUpdateProduct = (id: number, data: any) => api.patch<Product>(`/admin/products/${id}`, data);
export const adminDeleteProduct = (id: number) => api.delete(`/admin/products/${id}`);
export const adminBulkPriceUpdate = (data: BulkPriceRequest) =>
  api.post<BulkPriceResponse>('/admin/products/bulk-price', data);
export const adminUploadMedia = (productId: number, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  // Do not set Content-Type: axios must add multipart/form-data with boundary for file to be parsed
  return api.post<import('../types').ProductMedia>(`/admin/products/${productId}/media`, formData);
};
export const adminDeleteMedia = (productId: number, mediaId: number) =>
  api.delete(`/admin/products/${productId}/media/${mediaId}`);
export const adminGetCategories = () => api.get<Category[]>('/admin/categories');
export const adminUploadCategoryImage = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<{ url: string }>('/admin/categories/upload', formData);
};
export const adminCreateCategory = (data: { name: string; slug: string; sort_order?: number; parent_id?: number | null; image_url?: string | null }) =>
  api.post<Category>('/admin/categories', data);
export const adminUpdateCategory = (id: number, data: { name?: string; slug?: string; sort_order?: number; is_active?: boolean; parent_id?: number | null; image_url?: string | null }) =>
  api.patch<Category>(`/admin/categories/${id}`, data);
export const adminDeleteCategory = (id: number) => api.delete(`/admin/categories/${id}`);
export const adminGetModificationTypes = () => api.get<ModificationType[]>('/admin/modification-types');
export const adminCreateModificationType = (data: { name: string; sort_order?: number; values?: string[] }) =>
  api.post<ModificationType>('/admin/modification-types', data);
export const adminUpdateModificationType = (id: number, data: { name?: string; sort_order?: number }) =>
  api.patch<ModificationType>(`/admin/modification-types/${id}`, data);
export const adminDeleteModificationType = (id: number) => api.delete(`/admin/modification-types/${id}`);
export const adminGetModificationTypeValues = (typeId: number) =>
  api.get<import('../types').ModificationValue[]>(`/admin/modification-types/${typeId}/values`);
export const adminAddModificationTypeValue = (typeId: number, data: { value: string; sort_order?: number }) =>
  api.post<import('../types').ModificationValue>(`/admin/modification-types/${typeId}/values`, data);
export const adminDeleteModificationTypeValue = (typeId: number, valueId: number) =>
  api.delete(`/admin/modification-types/${typeId}/values/${valueId}`);
export const adminGetProductVariants = (productId: number) =>
  api.get<ProductVariant[]>(`/admin/products/${productId}/variants`);
export const adminSetProductVariants = (productId: number, items: { modification_type_id: number; value: string; quantity: number }[]) =>
  api.put<ProductVariant[]>(`/admin/products/${productId}/variants`, items);
export const adminCreateProductVariant = (productId: number, data: { modification_type_id: number; value: string; quantity: number }) =>
  api.post<ProductVariant>(`/admin/products/${productId}/variants`, data);
export const adminUpdateProductVariant = (productId: number, variantId: number, data: { value?: string; quantity?: number }) =>
  api.patch<ProductVariant>(`/admin/products/${productId}/variants/${variantId}`, data);
export const adminDeleteProductVariant = (productId: number, variantId: number) =>
  api.delete(`/admin/products/${productId}/variants/${variantId}`);
export const adminGetPromos = () => api.get<PromoCode[]>('/admin/promos');
export const adminCreatePromo = (data: any) => api.post<PromoCode>('/admin/promos', data);
export const adminDeletePromo = (id: number) => api.delete(`/admin/promos/${id}`);
export const adminGetBanners = () => api.get<Banner[]>('/admin/banners');
export const adminUploadBannerImage = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<{ url: string }>('/admin/banners/upload', formData);
};
export const adminCreateBanner = (data: {
  image_url: string;
  link?: string | null;
  sort_order?: number;
  is_active?: boolean;
}) => api.post<Banner>('/admin/banners', data);
export const adminUpdateBanner = (id: number, data: {
  image_url?: string;
  link?: string | null;
  sort_order?: number;
  is_active?: boolean;
}) => api.patch<Banner>(`/admin/banners/${id}`, data);
export const adminDeleteBanner = (id: number) => api.delete(`/admin/banners/${id}`);
export const adminSendMailing = (text: string) =>
  api.post('/admin/mailing', null, { params: { text } });
export const adminGetSettings = () => api.get('/admin/settings');
export const adminUpdateSettings = (data: any) =>
  api.patch('/admin/settings', data);

// Owner (super-admin)
export const ownerGetConfig = () => api.get<OwnerConfig>('/owner/config');
export const ownerUpdateConfig = (data: Partial<OwnerConfig>) =>
  api.patch<OwnerConfig>('/owner/config', data);

