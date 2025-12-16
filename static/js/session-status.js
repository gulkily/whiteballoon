(() => {
  const STATUS_ENDPOINT = '/login/status';
  const DEFAULT_INTERVAL = 15000;

  function initNotice(notice) {
    if (!notice) {
      return;
    }

    const textNode = notice.querySelector('[data-session-status-text]');
    const actionNode = notice.querySelector('[data-session-status-action]');
    const actionWrapper = actionNode?.parentElement;
    const defaultText = notice.dataset.defaultText || textNode?.textContent || '';
    const defaultActionUrl = notice.dataset.defaultActionUrl || actionNode?.getAttribute('href') || '';
    const defaultActionLabel = notice.dataset.defaultActionLabel || actionNode?.textContent || '';
    const pollInterval = Number(notice.dataset.pollInterval || '') || DEFAULT_INTERVAL;
    let timerId;

    const setAction = (url, label) => {
      if (!actionNode || !actionWrapper) {
        return;
      }
      if (url && label) {
        actionNode.setAttribute('href', url);
        actionNode.textContent = label;
        actionWrapper.hidden = false;
        return;
      }
      actionWrapper.hidden = true;
    };

    const updateText = (message) => {
      if (!textNode) {
        return;
      }
      textNode.textContent = message || '';
    };

    const handlePayload = (payload) => {
      if (!payload || !payload.state) {
        return;
      }

      if (payload.state === 'authenticated') {
        notice.remove();
        return;
      }

      const message = payload.message || defaultText;
      updateText(message);

      if (payload.action_url && payload.action_label) {
        setAction(payload.action_url, payload.action_label);
      } else if (payload.state === 'pending') {
        setAction(defaultActionUrl, defaultActionLabel || 'View details');
      } else {
        setAction(null, null);
      }
    };

    const schedule = () => {
      timerId = window.setTimeout(fetchStatus, pollInterval);
    };

    const fetchStatus = async () => {
      try {
        const response = await fetch(STATUS_ENDPOINT, {
          headers: { Accept: 'application/json' },
          credentials: 'same-origin',
          cache: 'no-store',
        });
        if (!response.ok) {
          throw new Error(`Status fetch failed (${response.status})`);
        }
        const payload = await response.json();
        handlePayload(payload);
      } catch (error) {
        console.error('Unable to refresh session status notice', error);
      } finally {
        schedule();
      }
    };

    fetchStatus();

    return () => {
      if (timerId) {
        window.clearTimeout(timerId);
      }
    };
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.fetch !== 'function') {
      return;
    }
    const notices = document.querySelectorAll('[data-session-status-notice]');
    notices.forEach((notice) => initNotice(notice));
  });
})();
