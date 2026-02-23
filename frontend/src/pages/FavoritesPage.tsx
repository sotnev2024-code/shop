import React, { useEffect } from 'react';
import { Heart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useFavoritesStore } from '../store/favoritesStore';
import { ProductCard } from '../components/ProductCard';
import { Button } from '../components/ui/Button';

export const FavoritesPage: React.FC = () => {
  const navigate = useNavigate();
  const { items, loading, fetchFavorites } = useFavoritesStore();

  useEffect(() => {
    fetchFavorites();
  }, [fetchFavorites]);

  if (!loading && items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4 pb-24">
        <Heart className="w-16 h-16 text-tg-hint mb-4" />
        <h2 className="text-xl font-bold text-tg-text mb-2">Нет избранного</h2>
        <p className="text-sm text-tg-hint text-center mb-6">
          Нажмите на сердечко, чтобы добавить товар в избранное
        </p>
        <Button onClick={() => navigate('/')}>Перейти в каталог</Button>
      </div>
    );
  }

  return (
    <div className="pb-20">
      <div className="px-4 pt-4 pb-3">
        <h1 className="text-xl font-bold text-tg-text">Избранное</h1>
      </div>

      <div className="px-4 grid grid-cols-2 gap-3">
        {items.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
};





