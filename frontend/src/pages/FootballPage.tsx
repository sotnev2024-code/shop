import React from 'react';

export const FootballPage: React.FC = () => {
  const base = window.location.origin;
  const src = `${base}/deepseek_html_20260309_6abba1.html`;

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

