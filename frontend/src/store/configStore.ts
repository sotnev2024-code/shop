import { create } from 'zustand';
import type { AppConfig } from '../types';
import { getConfig } from '../api/endpoints';

interface ConfigState {
  config: AppConfig | null;
  loading: boolean;
  fetchConfig: () => Promise<void>;
}

export const useConfigStore = create<ConfigState>((set) => ({
  config: null,
  loading: true,
  fetchConfig: async () => {
    try {
      const { data } = await getConfig();
      set({ config: data, loading: false });
    } catch (err) {
      // 401 = нет initData или неверный — в браузере без Telegram конфиг не загрузится
      set({ loading: false });
    }
  },
}));





