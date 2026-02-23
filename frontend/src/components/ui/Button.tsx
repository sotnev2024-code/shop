import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  className = '',
  ...props
}) => {
  const base = 'inline-flex items-center justify-center rounded-xl font-medium transition-all active:scale-[0.97]';

  const variants = {
    primary: 'bg-tg-button text-tg-button-text hover:opacity-90',
    secondary: 'bg-tg-secondary text-tg-text hover:opacity-80',
    danger: 'bg-red-500 text-white hover:bg-red-600',
    ghost: 'bg-transparent text-tg-link hover:bg-tg-secondary',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${fullWidth ? 'w-full' : ''} ${className} disabled:opacity-50`}
      {...props}
    >
      {children}
    </button>
  );
};





