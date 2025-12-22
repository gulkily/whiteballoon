(() => {
  const ENDPOINT = '/peer-auth/notifications';
  const POLL_INTERVAL = 15000;

  function initNotice(notice) {
    if (!notice) {
      return;
    }

    const countNode = notice.querySelector('[data-peer-auth-count]');
    const linkNode = notice.querySelector('[data-peer-auth-link]');
    let timerId;

    const setVisible = (visible) => {
      notice.hidden = !visible;
    };

    const updateCount = (count) => {
      if (!countNode) {
        return;
      }
      if (count <= 0) {
        countNode.textContent = '';
        countNode.setAttribute('aria-label', '0 pending logins');
        return;
      }
      const displayValue = count > 9 ? '9+' : String(count);
      countNode.textContent = displayValue;
      countNode.setAttribute('aria-label', `${count} pending logins`);
    };

    const handlePayload = (payload) => {
      if (!payload || typeof payload.pending_count !== 'number' || payload.pending_count <= 0) {
        setVisible(false);
        updateCount(0);
        return;
      }
      setVisible(true);
      updateCount(payload.pending_count);
      if (linkNode && payload.next_request && payload.next_request.username) {
        linkNode.setAttribute('title', `Review pending login for @${payload.next_request.username}`);
      }
    };

    const schedule = () => {
      timerId = window.setTimeout(fetchStatus, POLL_INTERVAL);
    };

    const fetchStatus = async () => {
      try {
        const response = await fetch(ENDPOINT, {
          headers: { Accept: 'application/json' },
          credentials: 'same-origin',
          cache: 'no-store',
        });
        if (response.status === 403 || response.status === 404) {
          notice.remove();
          return;
        }
        if (!response.ok) {
          throw new Error(`Peer auth notification request failed (${response.status})`);
        }
        const payload = await response.json();
        handlePayload(payload);
      } catch (error) {
        console.error('Unable to refresh peer auth notifications', error);
      } finally {
        schedule();
      }
    };

    fetchStatus();
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.fetch !== 'function') {
      return;
    }
    document.querySelectorAll('[data-peer-auth-notice]').forEach((notice) => {
      initNotice(notice);
    });
  });
})();
