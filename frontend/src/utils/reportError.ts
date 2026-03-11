/** Report client errors to backend for centralized logging. */

let reportedCount = 0;
const MAX_REPORTS_PER_SESSION = 50;

export function reportError(message: string, stack?: string, url?: string): void {
  if (reportedCount >= MAX_REPORTS_PER_SESSION) return;
  reportedCount += 1;

  try {
    const base = typeof window !== 'undefined' && window.location?.origin ? window.location.origin : '';
    const apiUrl = `${base}/api/v1/errors/report`;
    fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message?.slice(0, 500) || 'Unknown error',
        stack: stack?.slice(0, 8000),
        url: url || (typeof window !== 'undefined' ? window.location?.href : undefined),
        source: 'frontend',
      }),
      keepalive: true, // Allow request to complete even if page unloads
    }).catch(() => {});
  } catch {
    // Silently ignore - avoid recursion
  }
}

export function initErrorReporting(): void {
  if (typeof window === 'undefined') return;

  window.addEventListener('error', (event) => {
    reportError(
      event.message || String(event.error),
      event.error?.stack,
      event.filename || event.target?.toString?.()
    );
  });

  window.addEventListener('unhandledrejection', (event) => {
    const msg = event.reason instanceof Error ? event.reason.message : String(event.reason);
    const stack = event.reason instanceof Error ? event.reason.stack : undefined;
    reportError(msg, stack, window.location?.href);
  });
}
