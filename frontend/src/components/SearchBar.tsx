import React, { useState, useEffect, useRef } from 'react';
import { Search, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

/**
 * Normalize Russian text for search:
 * - Replace ё with е
 * - Trim whitespace
 */
function normalizeSearch(text: string): string {
  return text.replace(/ё/g, 'е').replace(/Ё/g, 'Е').trim();
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  placeholder = 'Поиск товаров...',
}) => {
  const [query, setQuery] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Debounce search: trigger after 300ms of no typing
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      onSearch(normalizeSearch(query));
    }, 300);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query]); // intentionally not including onSearch to avoid re-triggering

  const handleClear = () => {
    setQuery('');
    onSearch('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Immediate search on submit
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    onSearch(normalizeSearch(query));
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-tg-hint" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none focus:ring-2 focus:ring-tg-button placeholder-tg-hint"
      />
      {query && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2"
        >
          <X className="w-5 h-5 text-tg-hint" />
        </button>
      )}
    </form>
  );
};
