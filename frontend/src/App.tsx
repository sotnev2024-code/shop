import React, { useEffect, useCallback } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { useConfigStore } from './store/configStore';
import { useCartStore } from './store/cartStore';
import { useFavoritesStore } from './store/favoritesStore';

// Pages
import { CatalogPage } from './pages/CatalogPage';
import { ProductPage } from './pages/ProductPage';
import { CartPage } from './pages/CartPage';
import { FavoritesPage } from './pages/FavoritesPage';
import { CheckoutPage } from './pages/CheckoutPage';
import { OrdersPage } from './pages/OrdersPage';
import { OrderStatusPage } from './pages/OrderStatusPage';
import { ProfilePage } from './pages/ProfilePage';
import { ProfileBonusesPage } from './pages/ProfileBonusesPage';
import { SettingsPage } from './pages/SettingsPage';
import { HelpPage } from './pages/HelpPage';
import { OwnerPanelPage } from './pages/OwnerPanelPage';

// Admin
import { AdminLayout } from './admin/AdminLayout';
import { DashboardPage } from './admin/DashboardPage';
import { AdminOrdersPage } from './admin/AdminOrdersPage';
import { AdminProductsPage } from './admin/AdminProductsPage';
import { AdminBannersPage } from './admin/AdminBannersPage';
import { AdminPromoPage } from './admin/AdminPromoPage';
import { AdminMailingPage } from './admin/AdminMailingPage';
import { AdminSettingsPage } from './admin/AdminSettingsPage';

// Components
import { BottomNav } from './components/BottomNav';

const SHOW_NAV_PATHS = ['/', '/favorites', '/cart', '/profile'];

const App: React.FC = () => {
  const location = useLocation();
  const fetchConfig = useConfigStore((s) => s.fetchConfig);
  const fetchCart = useCartStore((s) => s.fetchCart);
  const validateCart = useCartStore((s) => s.validateCart);
  const fetchFavorites = useFavoritesStore((s) => s.fetchFavorites);
  const validateFavorites = useFavoritesStore((s) => s.validateFavorites);
  const configLoading = useConfigStore((s) => s.loading);

  const initApp = useCallback(async () => {
    // Initialize Telegram WebApp
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      if (typeof tg.enableClosingConfirmation === 'function') {
        try {
          tg.enableClosingConfirmation();
        } catch {
          // Not supported in Telegram WebApp 6.0
        }
      }
    }

    // Load initial data
    fetchConfig();
    await fetchFavorites();
    await fetchCart();

    // Validate favorites: remove out-of-stock
    const favRemoved = await validateFavorites();

    // Validate cart: remove out-of-stock, adjust quantities (by modification)
    const { removed, adjusted } = await validateCart();

    const messages: string[] = [];
    if (favRemoved.length > 0) {
      messages.push(`Убрано из избранного (нет в наличии): ${favRemoved.map((r) => r.product_name).join(', ')}`);
    }
    if (removed.length > 0) {
      messages.push(`Убрано из корзины (нет в наличии): ${removed.map((r) => r.product_name).join(', ')}`);
    }
    if (adjusted.length > 0) {
      const parts = adjusted.map(
        (a) => `${a.product_name}: ${a.old_quantity} → ${a.new_quantity} шт.`
      );
      messages.push(`Количество в корзине изменено: ${parts.join(', ')}`);
    }
    if (messages.length > 0) {
      const tg = window.Telegram?.WebApp;
      if (tg?.showAlert) {
        tg.showAlert(messages.join('\n'));
      } else {
        alert(messages.join('\n'));
      }
    }
  }, [fetchConfig, fetchCart, validateCart, fetchFavorites, validateFavorites]);

  useEffect(() => {
    initApp();
  }, [initApp]);

  if (configLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin w-10 h-10 border-4 border-tg-button border-t-transparent rounded-full" />
      </div>
    );
  }

  const showNav = SHOW_NAV_PATHS.includes(location.pathname);

  return (
    <div className="min-h-screen bg-tg-bg">
      <Routes>
        {/* Shop pages */}
        <Route path="/" element={<CatalogPage />} />
        <Route path="/product/:id" element={<ProductPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/favorites" element={<FavoritesPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/order/:id" element={<OrderStatusPage />} />

        {/* Profile pages */}
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/profile/bonuses" element={<ProfileBonusesPage />} />
        <Route path="/profile/settings" element={<SettingsPage />} />
        <Route path="/profile/help" element={<HelpPage />} />

        {/* Owner (super-admin) panel */}
        <Route path="/owner" element={<OwnerPanelPage />} />

        {/* Admin pages */}
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="orders" element={<AdminOrdersPage />} />
          <Route path="products" element={<AdminProductsPage />} />
          <Route path="banners" element={<AdminBannersPage />} />
          <Route path="promos" element={<AdminPromoPage />} />
          <Route path="mailing" element={<AdminMailingPage />} />
          <Route path="settings" element={<AdminSettingsPage />} />
        </Route>
      </Routes>

      {showNav && <BottomNav />}
    </div>
  );
};

export default App;
