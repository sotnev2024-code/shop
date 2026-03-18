import React from 'react';
import { useBackButton } from '../hooks/useBackButton';

export const FootballPage: React.FC = () => {
  useBackButton();
  const src = `/footpredict.html`;

  return (
    <div className="w-full h-screen bg-black">
      <iframe
        src={src}
        title="Football Bets"
        className="w-full h-full border-none"
        style={{ border: 'none' }}
      />
    </div>
  );
};

