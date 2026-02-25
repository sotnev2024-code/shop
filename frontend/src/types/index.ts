export interface AppConfig {
  shop_name: string;
  checkout_type: 'basic' | 'enhanced' | 'payment' | 'full';
  product_source: string;
  delivery_enabled: boolean;
  pickup_enabled: boolean;
  promo_enabled: boolean;
  mailing_enabled: boolean;
  currency: string;
  yandex_maps_enabled: boolean;
  yandex_maps_key: string | null;
  payment_enabled: boolean;
  support_link: string;
  is_admin: boolean;
  is_owner: boolean;
  bot_photo_url: string | null;
  bot_username: string | null;
  store_address: string | null;
  delivery_city: string | null;
  delivery_cost: number;
  free_delivery_min_amount: number;
  banner_aspect_shape: 'square' | 'rectangle';
  banner_size: 'small' | 'medium' | 'large' | 'xl';
  category_image_size: 'small' | 'medium' | 'large' | 'xlarge';
  bonus_enabled: boolean;
  bonus_welcome_enabled: boolean;
  bonus_welcome_amount: number;
  bonus_purchase_enabled: boolean;
  bonus_purchase_percent: number;
  bonus_spend_enabled: boolean;
  bonus_spend_limit_type: 'percent' | 'fixed';
  bonus_spend_limit_value: number;
}

export interface ProductMedia {
  id: number;
  media_type: 'image' | 'video';
  url: string;
  sort_order: number;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  sort_order: number;
  is_active: boolean;
  parent_id?: number | null;
  image_url?: string | null;
  children?: Category[];
}

export interface ModificationValue {
  id: number;
  modification_type_id: number;
  value: string;
  sort_order: number;
}

export interface ModificationType {
  id: number;
  name: string;
  sort_order: number;
  values?: ModificationValue[];
}

export interface ProductVariantShort {
  value: string;
  quantity: number;
}

export interface ProductVariant extends ProductVariantShort {
  id: number;
  product_id: number;
  modification_type_id: number;
}

export interface Product {
  id: number;
  name: string;
  description: string | null;
  price: number;
  old_price: number | null;
  image_url: string | null;
  is_available: boolean;
  stock_quantity: number;
  category_id: number | null;
  category_ids: number[];
  external_id: string | null;
  created_at: string;
  category: Category | null;
  categories: Category[];
  is_favorite: boolean;
  media: ProductMedia[];
  modification_type?: { id: number; name: string } | null;
  variants?: ProductVariantShort[];
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  per_page: number;
}

export type BulkPriceScope = 'all' | 'product_ids' | 'price_equals' | 'price_range' | 'category';
export type BulkPriceOperation = 'add_amount' | 'subtract_amount' | 'add_percent' | 'subtract_percent' | 'set_to';

export interface BulkPriceRequest {
  scope: BulkPriceScope;
  product_ids?: number[];
  price_equals?: number;
  price_min?: number;
  price_max?: number;
  category_id?: number;
  operation: BulkPriceOperation;
  value: number;
  round_to_nearest?: number;
}

export interface BulkPriceResponse {
  updated_count: number;
  product_ids: number[];
}

export interface CartItem {
  id: number;
  product_id: number;
  quantity: number;
  product: Product;
  modification_type_id?: number | null;
  modification_value?: string | null;
  modification_label?: string | null;
}

export interface CartResponse {
  items: CartItem[];
  total_price: number;
  total_items: number;
}

export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  price_at_order: number;
  product_name: string;
  modification_type_id?: number | null;
  modification_value?: string | null;
  modification_label?: string | null;
}

export interface Order {
  id: number;
  status: string;
  total: number;
  discount: number;
  bonus_used?: number;
  delivery_fee?: number;
  delivery_type: string | null;
  customer_name: string;
  customer_phone: string;
  address: string | null;
  payment_status: string | null;
  delivery_service: string | null;
  tracking_number: string | null;
  created_at: string;
  items: OrderItem[];
}

export interface OrderListResponse {
  items: Order[];
  total: number;
}

export interface PromoCheckResponse {
  valid: boolean;
  discount_type: string | null;
  discount_value: number | null;
  message: string;
}

// Owner (super-admin) config
export interface OwnerConfig {
  checkout_type: string;
  product_source: string;
  promo_enabled: boolean;
  mailing_enabled: boolean;
  delivery_enabled: boolean;
  pickup_enabled: boolean;
  delivery_sdek_enabled: boolean;
  delivery_pochta_enabled: boolean;
  delivery_yandex_enabled: boolean;
  moysklad_token: string | null;
  one_c_endpoint: string | null;
  one_c_login: string | null;
  one_c_password: string | null;
  payment_provider_token: string | null;
  yandex_maps_key: string | null;
  support_link: string | null;
  sync_interval_minutes: number;
}

export interface Banner {
  id: number;
  image_url: string;
  link: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string;
}

// Admin types
export interface Stats {
  users: { total: number; new_month: number };
  orders: { total: number; month: number; week: number };
  revenue: { total: number; month: number };
  products: { total: number };
}

export interface PromoCode {
  id: number;
  code: string;
  discount_type: string;
  discount_value: number;
  min_order_amount: number;
  max_uses: number | null;
  used_count: number;
  first_order_only: boolean;
  valid_from: string | null;
  valid_until: string | null;
  is_active: boolean;
  created_at: string;
}

