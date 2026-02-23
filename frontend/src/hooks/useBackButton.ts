import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Hook to show Telegram BackButton on sub-pages.
 * On click, navigates back. Hides the button on unmount.
 */
export function useBackButton(customCallback?: () => void) {
  const navigate = useNavigate();

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg?.BackButton) return;
    try {
      const handler = () => {
        if (customCallback) customCallback();
        else navigate(-1);
      };
      tg.BackButton.show();
      tg.BackButton.onClick(handler);
      return () => {
        try {
          tg.BackButton.offClick(handler);
          tg.BackButton.hide();
        } catch {
          // BackButton not supported in WebApp 6.0
        }
      };
    } catch {
      return undefined;
    }
  }, [navigate, customCallback]);
}





