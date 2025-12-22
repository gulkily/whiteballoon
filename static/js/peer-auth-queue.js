(() => {
  const ENDPOINT = '/peer-auth/refresh';
  const INTERVAL = 15000;

  function initQueue(container) {
    const countNode = document.querySelector('[data-peer-auth-count-value]');
    let timerId;

    const updateCount = (count) => {
      if (!countNode) {
        return;
      }
      countNode.textContent = typeof count === 'number' ? String(count) : '0';
    };

    const render = (html, count) => {
      if (typeof html === 'string') {
        container.innerHTML = html;
      }
      updateCount(count);
    };

    const schedule = () => {
      timerId = window.setTimeout(fetchData, INTERVAL);
    };

    const fetchData = async () => {
      try {
        const response = await fetch(ENDPOINT, {
          headers: { Accept: 'application/json' },
          credentials: 'same-origin',
          cache: 'no-store',
        });
        if (response.status === 403 || response.status === 404) {
          container.removeAttribute('data-peer-auth-list');
          if (timerId) {
            window.clearTimeout(timerId);
          }
          return;
        }
        if (!response.ok) {
          throw new Error(`Peer auth refresh failed (${response.status})`);
        }
        const payload = await response.json();
        render(payload.html, payload.pending_count);
      } catch (error) {
        console.error('Unable to refresh peer auth queue', error);
      } finally {
        schedule();
      }
    };

    fetchData();
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.fetch !== 'function') {
      return;
    }
    const container = document.querySelector('[data-peer-auth-list]');
    if (!container) {
      return;
    }
    initQueue(container);
  });
})();
