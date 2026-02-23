import React from 'react';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea: React.FC<TextareaProps> = ({ label, error, className = '', ...props }) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-tg-hint mb-1">{label}</label>
      )}
      <textarea
        className={`w-full px-4 py-2.5 rounded-xl bg-tg-secondary text-tg-text border-none outline-none focus:ring-2 focus:ring-tg-button placeholder-tg-hint resize-y min-h-[100px] ${className}`}
        {...props}
      />
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  );
};



