(function () {
  const container = document.querySelector('[data-request-channels]');
  if (!container) return;

  const dataNode = document.getElementById('channel-bootstrap');
  let state = { requests: [], active_channel_id: null };
  try {
    if (dataNode && dataNode.textContent) {
      state = JSON.parse(dataNode.textContent) || state;
    }
  } catch (error) {
    console.warn('Unable to bootstrap request channels', error);
  }

  const list = container.querySelector('[data-channel-list]');
  const searchInput = container.querySelector('[data-channel-search]');
  const buttons = list ? Array.from(list.querySelectorAll('[data-channel-node]')) : [];
  const filters = container.querySelector('[data-channel-filters]');
  const chatPane = container.querySelector('[data-channel-pane]');
  const emptyState = container.querySelector('[data-channel-empty]');
  const channelMeta = {};

  if (buttons.length) {
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const channelId = Number(btn.dataset.channelId);
        selectChannel(channelId, btn);
      });
      updateRelativeTime(btn);
    });
  }

  let lastTypingSignal = 0;
  let typingIndicator = null;
  let announcer = null;

  wireChatPane(chatPane);
  const heartbeat = setInterval(() => pingPresence(false), 8000);
  const presencePoller = setInterval(refreshPresence, 9000);
  refreshPresence();
  window.addEventListener('beforeunload', () => {
    clearInterval(heartbeat);
    clearInterval(presencePoller);
  });

  let activeFilter = 'all';
  let searchTerm = '';

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      searchTerm = searchInput.value.trim().toLowerCase();
      applyFilters();
    });
  }

  if (filters) {
    filters.addEventListener('click', (event) => {
      const target = event.target;
      const button = target instanceof Element ? target.closest('[data-channel-filter]') : null;
      if (!button) return;
      activeFilter = button.dataset.channelFilter || 'all';
      filters.querySelectorAll('[data-channel-filter]').forEach((node) => {
        node.setAttribute('aria-pressed', node === button ? 'true' : 'false');
      });
      applyFilters();
    });
  }

  container.addEventListener('keydown', (event) => {
    if (!event.altKey) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      focusRelativeChannel(1);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusRelativeChannel(-1);
    }
  });

  function selectChannel(channelId, button) {
    buttons.forEach((btn) => btn.removeAttribute('aria-current'));
    if (button) {
      button.setAttribute('aria-current', 'true');
    }
    state.active_channel_id = channelId;
    if (emptyState && chatPane) {
      emptyState.setAttribute('hidden', 'hidden');
      chatPane.removeAttribute('aria-busy');
    }
    loadChannel(channelId);
    pingPresence(false);
  }

  function updateRelativeTime(button) {
    const target = button.querySelector('[data-channel-time]');
    if (!target) return;
    const iso = target.getAttribute('data-timestamp');
    if (!iso) return;
    const date = new Date(iso);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    let label = 'just now';
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      label = hours === 1 ? '1 hour ago' : `${hours} hours ago`;
    } else if (minutes > 1) {
      label = `${minutes} minutes ago`;
    } else if (minutes === 1) {
      label = '1 minute ago';
    }
    target.textContent = label;
  }

  function applyFilters() {
    buttons.forEach((btn) => {
      const status = (btn.dataset.channelStatus || '').toLowerCase();
      const isPinned = btn.dataset.channelPinned === 'true';
      const matchesSearch = btn.textContent.toLowerCase().includes(searchTerm);
      let matchesFilter = true;
      if (activeFilter === 'open' || activeFilter === 'completed') {
        matchesFilter = status === activeFilter;
      } else if (activeFilter === 'pinned') {
        matchesFilter = isPinned;
      }
      btn.style.display = matchesSearch && matchesFilter ? '' : 'none';
    });
  }

  function wireChatPane(pane) {
    if (!pane) return;
    const composer = pane.querySelector('[data-channel-composer]');
    typingIndicator = pane.querySelector('[data-channel-typing]');
    announcer = pane.querySelector('[data-channel-announcer]');
    if (composer && !composer.dataset.channelComposerBound) {
      composer.dataset.channelComposerBound = 'true';
      composer.addEventListener('submit', handleComposerSubmit);
      const input = composer.querySelector('[data-channel-composer-input]');
      if (input) {
        input.addEventListener('input', handleTypingEvent);
      }
    }
  }

  function handleTypingEvent() {
    const now = Date.now();
    if (now - lastTypingSignal < 2000) {
      return;
    }
    lastTypingSignal = now;
    pingPresence(true);
  }

  async function handleComposerSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const channelId = Number(form.dataset.channelId);
    const errorsBox = form.querySelector('[data-channel-errors]');
    const submitButton = form.querySelector('[data-channel-send]');
    const formData = new FormData(form);
    if (submitButton) submitButton.setAttribute('disabled', 'disabled');
    showComposerErrors(errorsBox, []);
    const message = (form.querySelector('[data-channel-composer-input]')?.value || '').trim();
    const log = chatPane?.querySelector('[data-channel-log]');
    const placeholder = addOptimisticMessage(log, message);

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'Fetch',
          Accept: 'application/json',
        },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        showComposerErrors(errorsBox, payload.errors || ['Unable to send message.']);
        return;
      }
      form.reset();
      showComposerErrors(errorsBox, []);
      await loadChannel(channelId);
      announce('Message sent');
    } catch (error) {
      form.submit();
    } finally {
      if (placeholder) {
        placeholder.remove();
      }
      submitButton?.removeAttribute('disabled');
    }
  }

  function showComposerErrors(errorsBox, messages) {
    if (!errorsBox) return;
    if (!messages || !messages.length) {
      errorsBox.setAttribute('hidden', 'hidden');
      errorsBox.innerHTML = '';
      return;
    }
    const list = messages.map((msg) => `<li>${msg}</li>`).join('');
    errorsBox.innerHTML = `<ul>${list}</ul>`;
    errorsBox.removeAttribute('hidden');
  }

  async function loadChannel(channelId) {
    if (!chatPane || !channelId) {
      return;
    }
    chatPane.setAttribute('aria-busy', 'true');
    try {
      const response = await fetch(`/requests/channels/${channelId}/panel`, {
        headers: { 'X-Requested-With': 'Fetch', Accept: 'application/json' },
      });
      if (!response.ok) {
        window.location.href = `/requests/${channelId}`;
        return;
      }
      const payload = await response.json();
      chatPane.innerHTML = payload.html;
      wireChatPane(chatPane);
      chatPane.scrollTop = chatPane.scrollHeight;
      if (payload.channel) {
        updateChannelRowMeta(payload.channel);
        channelMeta[payload.channel.id] = payload.channel;
      }
      announce('Channel updated');
    } catch (error) {
      console.error('Failed to load channel', error);
    } finally {
      chatPane.removeAttribute('aria-busy');
    }
  }

  function updateChannelRowMeta(channel) {
    const button = buttons.find((btn) => Number(btn.dataset.channelId) === Number(channel.id));
    if (!button) return;
    const replyBadge = button.querySelector('.request-channel__badge');
    if (replyBadge && typeof channel.comment_count === 'number') {
      replyBadge.textContent = `${channel.comment_count} replies`;
    }
    const unreadBadge = button.querySelector('[data-channel-unread]');
    if (unreadBadge) {
      unreadBadge.remove();
    }
    channelMeta[channel.id] = channel;
  }

  async function pingPresence(isTyping) {
    if (!state.active_channel_id) return;
    try {
      await fetch('/requests/channels/presence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'Fetch',
          Accept: 'application/json',
        },
        body: JSON.stringify({ request_id: state.active_channel_id, typing: Boolean(isTyping) }),
      });
    } catch (error) {
      // ignore network blips
    }
  }

  async function refreshPresence() {
    const ids = buttons
      .map((btn) => Number(btn.dataset.channelId))
      .filter((id) => Number.isFinite(id));
    if (!ids.length) return;
    const params = ids.map((id) => `id=${id}`).join('&');
    try {
      const response = await fetch(`/requests/channels/presence?${params}`, {
        headers: { 'X-Requested-With': 'Fetch', Accept: 'application/json' },
      });
      if (!response.ok) return;
      const payload = await response.json();
      updatePresenceIndicators(payload.presence || {});
    } catch (error) {
      console.warn('Presence polling failed', error);
    }
  }

  function updatePresenceIndicators(presence) {
    if (!presence) return;
    Object.keys(presence).forEach((requestId) => {
      const data = presence[requestId] || {};
      const button = buttons.find((btn) => Number(btn.dataset.channelId) === Number(requestId));
      if (button) {
        const target = button.querySelector('[data-channel-presence]');
        if (target) {
          if (data.online) {
            target.textContent = data.online;
            target.removeAttribute('hidden');
          } else {
            target.setAttribute('hidden', 'hidden');
          }
        }
      }
      if (Number(requestId) === Number(state.active_channel_id) && typingIndicator) {
        const names = Array.isArray(data.typing) ? data.typing : [];
        if (names.length) {
          typingIndicator.textContent = `${names.join(', ')} typing…`;
          typingIndicator.removeAttribute('hidden');
        } else {
          typingIndicator.textContent = '';
          typingIndicator.setAttribute('hidden', 'hidden');
        }
      }
    });
  }

  function addOptimisticMessage(log, body) {
    if (!log || !body) return null;
    let list = log.querySelector('.channel-chat__list');
    if (!list) {
      list = document.createElement('ul');
      list.className = 'channel-chat__list';
      log.innerHTML = '';
      log.appendChild(list);
    }
    const temp = document.createElement('li');
    temp.className = 'channel-message channel-message--pending';
    temp.innerHTML = `
      <div class="channel-message__avatar" aria-hidden="true">You</div>
      <div class="channel-message__content">
        <div class="channel-message__meta">
          <span class="channel-message__author">Sending…</span>
        </div>
        <div class="channel-message__text">${escapeHtml(body).replace(/\n/g, '<br />')}</div>
      </div>`;
    list.appendChild(temp);
    log.scrollTo({ top: log.scrollHeight });
    return temp;
  }

  function escapeHtml(value) {
    if (!value) return '';
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function focusRelativeChannel(offset) {
    const visible = buttons.filter((btn) => btn.style.display !== 'none' && btn.offsetParent !== null);
    if (!visible.length) {
      return;
    }
    const currentIndex = visible.findIndex((btn) => btn.getAttribute('aria-current') === 'true');
    let nextIndex = currentIndex + offset;
    if (nextIndex < 0) {
      nextIndex = visible.length - 1;
    } else if (nextIndex >= visible.length) {
      nextIndex = 0;
    }
    const target = visible[nextIndex];
    if (target) {
      target.focus();
      selectChannel(Number(target.dataset.channelId), target);
    }
  }

  function announce(message) {
    if (!announcer || !message) return;
    announcer.textContent = message;
  }
})();
