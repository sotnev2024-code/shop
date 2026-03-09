import React from 'react';

export const FootballPage: React.FC = () => {
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

