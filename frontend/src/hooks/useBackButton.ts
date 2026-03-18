import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * Hook to show Telegram BackButton on sub-pages.
 * On click, navigates back. Hides the button on unmount.
 */
export function useBackButton(customCallback?: () => void) {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg?.BackButton) return;

    try {
      const handler = () => {
        if (customCallback) {
          customCallback();
        } else {
          // If we have no history (e.g. deep link), go to home page
          const isInitialPage = window.history.length <= 1 || (window.history.state && window.history.state.idx === 0);
          if (isInitialPage && location.pathname !== '/') {
            navigate('/', { replace: true });
          } else {
            navigate(-1);
          }
        }
      };

      tg.BackButton.show();
      tg.BackButton.onClick(handler);

      return () => {
        try {
          tg.BackButton.offClick(handler);
          tg.BackButton.hide();
        } catch {
          // Ignore
        }
      };
    } catch {
      return undefined;
    }
  }, [navigate, location, customCallback]);
}





