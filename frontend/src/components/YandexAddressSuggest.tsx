import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MapPin, Search } from 'lucide-react';

interface YandexAddressSuggestProps {
  apiKey: string;
  value: string;
  onChange: (address: string) => void;
  placeholder?: string;
  deliveryCity?: string | null;
  label?: string;
}

interface Suggestion {
  text: string;
}

export const YandexAddressSuggest: React.FC<YandexAddressSuggestProps> = ({
  apiKey,
  value,
  onChange,
  placeholder,
  deliveryCity,
  label,
}) => {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchSuggestions = useCallback(
    async (searchQuery: string) => {
      if (searchQuery.length < 2) {
        setSuggestions([]);
        setShowSuggestions(false);
        setLoading(false);
        return;
      }
      const searchStr = deliveryCity ? `${deliveryCity}, ${searchQuery}` : searchQuery;
      try {
        const response = await fetch(
          `https://geocode-maps.yandex.ru/1.x/?apikey=${apiKey}&format=json&geocode=${encodeURIComponent(searchStr)}&lang=ru_RU&results=5`
        );
        const data = await response.json();
        const features = data.response?.GeoObjectCollection?.featureMember || [];
        const results: Suggestion[] = features
          .map((f: any) => ({
            text: f.GeoObject.metaDataProperty?.GeocoderMetaData?.text || '',
          }))
          .filter((r: Suggestion) => r.text);
        const list = deliveryCity
          ? results.filter((r) => r.text.toLowerCase().includes(deliveryCity.toLowerCase()))
          : results;
        setSuggestions(list);
        setShowSuggestions(list.length > 0);
      } catch {
        setSuggestions([]);
        setShowSuggestions(false);
      }
      setLoading(false);
    },
    [apiKey, deliveryCity]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setQuery(v);
    onChange(v);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (v.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    setLoading(true);
    timeoutRef.current = setTimeout(() => fetchSuggestions(v), 300);
  };

  const handleSelect = (suggestion: Suggestion) => {
    setQuery(suggestion.text);
    onChange(suggestion.text);
    setShowSuggestions(false);
    setSuggestions([]);
  };

  return (
    <div ref={wrapperRef} className="w-full relative">
      {label && (
        <label className="block text-sm font-medium text-tg-hint mb-1">{label}</label>
      )}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tg-hint pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder={placeholder ?? (deliveryCity ? `Введите адрес в ${deliveryCity}` : 'Введите адрес доставки')}
          className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none focus:ring-2 focus:ring-tg-button placeholder-tg-hint"
        />
        {loading && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-tg-hint">
            …
          </span>
        )}
      </div>
      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-20 w-full mt-1 bg-tg-bg border border-tg-secondary rounded-xl shadow-lg overflow-hidden max-h-48 overflow-y-auto">
          {suggestions.map((s, i) => (
            <li key={i}>
              <button
                type="button"
                onClick={() => handleSelect(s)}
                className="w-full px-3 py-2.5 text-left text-sm text-tg-text hover:bg-tg-secondary flex items-start gap-2 border-b border-tg-secondary last:border-b-0"
              >
                <MapPin className="w-4 h-4 text-tg-hint flex-shrink-0 mt-0.5" />
                <span className="line-clamp-2">{s.text}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
