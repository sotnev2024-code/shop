import React, { useEffect, useRef, useState, useCallback } from 'react';
import { MapPin, Search } from 'lucide-react';

interface YandexMapPickerProps {
  apiKey: string;
  deliveryCity?: string | null;
  onAddressSelect: (address: string, coords: { lat: number; lng: number }) => void;
  initialAddress?: string;
}

declare global {
  interface Window {
    ymaps3?: any;
    __ymaps3_ready?: boolean;
  }
}

export const YandexMapPicker: React.FC<YandexMapPickerProps> = ({
  apiKey,
  deliveryCity,
  onAddressSelect,
  initialAddress,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const [searchQuery, setSearchQuery] = useState(initialAddress || '');
  const [suggestions, setSuggestions] = useState<Array<{ text: string; coords: [number, number] }>>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedAddress, setSelectedAddress] = useState(initialAddress || '');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Keep callbacks stable via refs
  const onAddressSelectRef = useRef(onAddressSelect);
  onAddressSelectRef.current = onAddressSelect;
  const deliveryCityRef = useRef(deliveryCity);
  deliveryCityRef.current = deliveryCity;

  // ---- Geocoding helpers (stable — use refs for mutable props) ----

  const geocodeAddress = useCallback(
    async (address: string): Promise<{ lat: number; lng: number; text: string } | null> => {
      try {
        const response = await fetch(
          `https://geocode-maps.yandex.ru/1.x/?apikey=${apiKey}&format=json&geocode=${encodeURIComponent(address)}&lang=ru_RU`
        );
        const data = await response.json();
        const features = data.response?.GeoObjectCollection?.featureMember;
        if (features && features.length > 0) {
          const pos = features[0].GeoObject.Point.pos.split(' ');
          const text = features[0].GeoObject.metaDataProperty?.GeocoderMetaData?.text || address;
          return { lat: parseFloat(pos[1]), lng: parseFloat(pos[0]), text };
        }
      } catch (err) {
        console.error('Geocoding error:', err);
      }
      return null;
    },
    [apiKey],
  );

  const reverseGeocode = useCallback(
    async (lat: number, lng: number): Promise<string> => {
      try {
        const response = await fetch(
          `https://geocode-maps.yandex.ru/1.x/?apikey=${apiKey}&format=json&geocode=${lng},${lat}&lang=ru_RU`
        );
        const data = await response.json();
        const features = data.response?.GeoObjectCollection?.featureMember;
        if (features && features.length > 0) {
          return features[0].GeoObject.metaDataProperty?.GeocoderMetaData?.text || '';
        }
      } catch (err) {
        console.error('Reverse geocoding error:', err);
      }
      return '';
    },
    [apiKey],
  );

  const panTo = useCallback((lat: number, lng: number) => {
    if (mapRef.current) {
      try {
        mapRef.current.setLocation({ center: [lng, lat], zoom: 16, duration: 300 });
      } catch {
        /* ignore */
      }
    }
  }, []);

  // ---- Map initialisation ----

  useEffect(() => {
    let cancelled = false;
    let initStarted = false;

    const getYmaps3 = () =>
      (typeof globalThis !== 'undefined' && (globalThis as any).ymaps3) ||
      (typeof window !== 'undefined' && (window as any).ymaps3);

    const initMap = async () => {
      const ymaps3 = getYmaps3();
      if (!ymaps3 || initStarted) return;
      initStarted = true;

      // Wait for container to be in DOM (ref can lag one tick)
      let container = mapContainerRef.current;
      for (let i = 0; i < 20 && !container && !cancelled; i++) {
        await new Promise((r) => setTimeout(r, 50));
        container = mapContainerRef.current;
      }
      if (cancelled || !container) {
        initStarted = false;
        return;
      }

      try {
        await ymaps3.ready;
        if (cancelled) return;

        const { YMap, YMapDefaultSchemeLayer, YMapDefaultFeaturesLayer } = ymaps3;

        // Determine centre
        let center: [number, number] = [55.7558, 37.6173]; // Moscow default
        if (deliveryCityRef.current) {
          const geo = await geocodeAddress(deliveryCityRef.current);
          if (geo) center = [geo.lat, geo.lng];
        }

        if (cancelled || !mapContainerRef.current) return;

        const map = new YMap(mapContainerRef.current, {
          location: { center: [center[1], center[0]], zoom: deliveryCityRef.current ? 12 : 10 },
        });
        map.addChild(new YMapDefaultSchemeLayer({}));
        map.addChild(new YMapDefaultFeaturesLayer({}));
        mapRef.current = map;
        if (!cancelled) setIsLoading(false);
      } catch (err) {
        console.error('Map init error:', err);
        initStarted = false;
        if (!cancelled) {
          setError('Ошибка инициализации карты');
          setIsLoading(false);
        }
      }
    };

    const runInit = async () => {
      let ymaps3 = getYmaps3();
      if (!ymaps3) {
        const deadline = Date.now() + 15000;
        while (!cancelled && Date.now() < deadline) {
          await new Promise((r) => setTimeout(r, 100));
          ymaps3 = getYmaps3();
          if (ymaps3) break;
        }
      }
      if (cancelled) return;
      if (ymaps3) {
        await initMap();
      } else {
        setError('Не удалось загрузить карту');
        setIsLoading(false);
      }
    };

    const existing = document.querySelector('script[src*="api-maps.yandex.ru"]');
    if (existing) {
      // Script already in page: run init now (may be already loaded) and on load
      runInit();
      existing.addEventListener('load', () => runInit());
    } else if (getYmaps3()) {
      runInit();
    } else {
      const script = document.createElement('script');
      script.src = `https://api-maps.yandex.ru/v3/?apikey=${apiKey}&lang=ru_RU`;
      script.async = true;
      script.onload = () => runInit();
      script.onerror = () => {
        if (!cancelled) {
          setError('Не удалось загрузить карту');
          setIsLoading(false);
        }
      };
      document.head.appendChild(script);
    }

    return () => {
      cancelled = true;
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey]);

  // ---- Map click → reverse geocode & set address ----

  const handleMapClick = useCallback(
    async (lat: number, lng: number) => {
      const address = await reverseGeocode(lat, lng);
      const city = deliveryCityRef.current;
      if (city && address && !address.toLowerCase().includes(city.toLowerCase())) {
        window.Telegram?.WebApp?.showAlert?.(`Доставка доступна только в: ${city}`);
        return;
      }
      setSelectedAddress(address);
      setSearchQuery(address);
      onAddressSelectRef.current(address, { lat, lng });
      panTo(lat, lng);
    },
    [reverseGeocode, panTo],
  );

  // ---- Search / Suggest ----

  const handleSearch = useCallback(
    (query: string) => {
      setSearchQuery(query);
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);

      if (query.length < 3) {
        setSuggestions([]);
        setShowSuggestions(false);
        return;
      }

      searchTimeoutRef.current = setTimeout(async () => {
        const city = deliveryCityRef.current;
        const searchStr = city ? `${city}, ${query}` : query;
        try {
          const response = await fetch(
            `https://geocode-maps.yandex.ru/1.x/?apikey=${apiKey}&format=json&geocode=${encodeURIComponent(searchStr)}&lang=ru_RU&results=5`
          );
          const data = await response.json();
          const features = data.response?.GeoObjectCollection?.featureMember || [];

          const results = features
            .map((f: any) => {
              const pos = f.GeoObject.Point.pos.split(' ');
              return {
                text: f.GeoObject.metaDataProperty?.GeocoderMetaData?.text || '',
                coords: [parseFloat(pos[1]), parseFloat(pos[0])] as [number, number],
              };
            })
            .filter((r: any) => {
              if (city) return r.text.toLowerCase().includes(city.toLowerCase());
              return true;
            });

          setSuggestions(results);
          setShowSuggestions(results.length > 0);
        } catch {
          setSuggestions([]);
          setShowSuggestions(false);
        }
      }, 300);
    },
    [apiKey],
  );

  const handleSelectSuggestion = useCallback(
    (suggestion: { text: string; coords: [number, number] }) => {
      setSearchQuery(suggestion.text);
      setSelectedAddress(suggestion.text);
      setShowSuggestions(false);
      onAddressSelectRef.current(suggestion.text, {
        lat: suggestion.coords[0],
        lng: suggestion.coords[1],
      });
      panTo(suggestion.coords[0], suggestion.coords[1]);
    },
    [panTo],
  );

  // ---- Render ----

  return (
    <div className="space-y-2">
      {error && (
        <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-sm text-amber-800">
          {error}. Введите адрес вручную в поле ниже.
        </div>
      )}
      {/* Search input */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tg-hint" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            placeholder={deliveryCity ? `Введите адрес в ${deliveryCity}` : 'Введите адрес доставки'}
            className="w-full pl-9 pr-3 py-2.5 bg-tg-secondary rounded-xl text-sm text-tg-text placeholder:text-tg-hint focus:outline-none focus:ring-2 focus:ring-tg-button/30"
          />
        </div>

        {showSuggestions && (
          <div className="absolute z-20 w-full mt-1 bg-tg-bg border border-tg-secondary rounded-xl shadow-lg overflow-hidden max-h-48 overflow-y-auto">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSelectSuggestion(s)}
                className="w-full px-3 py-2.5 text-left text-sm text-tg-text hover:bg-tg-secondary border-b border-tg-secondary last:border-b-0 flex items-start gap-2"
              >
                <MapPin className="w-4 h-4 text-tg-hint flex-shrink-0 mt-0.5" />
                <span className="line-clamp-2">{s.text}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Map container */}
      <div className="relative rounded-xl overflow-hidden border border-tg-secondary">
        {error ? (
          <div className="w-full h-48 bg-tg-secondary flex items-center justify-center">
            <span className="text-sm text-tg-hint">Карта недоступна</span>
          </div>
        ) : (
          <>
            <div ref={mapContainerRef} className="w-full h-48" onClick={(e) => e.stopPropagation()} />
            {isLoading && (
              <div className="absolute inset-0 bg-tg-secondary flex items-center justify-center">
                <div className="text-sm text-tg-hint">Загрузка карты...</div>
              </div>
            )}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-full pointer-events-none z-10">
              <MapPin className="w-8 h-8 text-red-500 drop-shadow-lg" />
            </div>
          </>
        )}
      </div>

      {selectedAddress && (
        <div className="flex items-start gap-2 p-2 bg-tg-secondary rounded-xl">
          <MapPin className="w-4 h-4 text-tg-button flex-shrink-0 mt-0.5" />
          <span className="text-sm text-tg-text">{selectedAddress}</span>
        </div>
      )}

      {deliveryCity && (
        <p className="text-xs text-tg-hint">📍 Доставка доступна только в: {deliveryCity}</p>
      )}
    </div>
  );
};
