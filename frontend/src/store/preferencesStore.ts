import { create } from 'zustand';

const STORAGE_KEY_VIDEOS = 'pref_show_videos_in_catalog';

function getStoredShowVideos(): boolean {
  try {
    const v = localStorage.getItem(STORAGE_KEY_VIDEOS);
    if (v === 'false') return false;
    if (v === 'true') return true;
  } catch {
    // ignore
  }
  return true; // default
}

interface PreferencesState {
  showVideosInCatalog: boolean;
  setShowVideosInCatalog: (value: boolean) => void;
  hydrate: () => void;
}

export const usePreferencesStore = create<PreferencesState>((set) => ({
  showVideosInCatalog: getStoredShowVideos(),
  setShowVideosInCatalog: (value: boolean) => {
    try {
      localStorage.setItem(STORAGE_KEY_VIDEOS, String(value));
    } catch {
      // ignore
    }
    set({ showVideosInCatalog: value });
  },
  hydrate: () => {
    set({ showVideosInCatalog: getStoredShowVideos() });
  },
}));
