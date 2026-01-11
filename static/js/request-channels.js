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

  const defaultFilter = container.dataset.defaultFilter || 'all';
  const list = container.querySelector('[data-channel-list]');
  const priority = container.querySelector('[data-channel-priority]');
  const priorityList = container.querySelector('[data-channel-priority-list]');
  const searchInput = container.querySelector('[data-channel-search]');
  let listButtons = list ? Array.from(list.querySelectorAll('[data-channel-node]')) : [];
  let priorityButtons = priorityList
    ? Array.from(priorityList.querySelectorAll('[data-channel-node]'))
    : [];
  let buttons = [...priorityButtons, ...listButtons];
  const filters = container.querySelector('[data-channel-filters]');
  const chatPane = container.querySelector('[data-channel-pane]');
  const emptyState = container.querySelector('[data-channel-empty]');
  const resultsAnnouncer = container.querySelector('[data-channel-results-announcer]');
  const channelMeta = {};
  const channelStore = new Map();
  const resultCache = new Map();
  const visibleCount = container.querySelector('[data-channel-result-count-value]');
  let activeFilter = defaultFilter;
  let searchTerm = '';
  let searchDebounce = null;
  let inflightController = null;
  const presenceHeartbeatInterval = 8000;
  const presencePollInterval = 9000;
  const presencePayloadTtl = presencePollInterval * 2 + 2000;
  const presenceScopeTtl = presencePollInterval * 2 + 2000;
  const presenceStoragePrefix = 'wb-presence';
  const presenceTabKey = presenceStoragePrefix + ':tab';
  const presenceHeartbeatKey = presenceStoragePrefix + ':heartbeat';
  const presencePollKey = presenceStoragePrefix + ':poll';
  const presencePayloadKey = presenceStoragePrefix + ':payload';
  const presenceScopeKey = presenceStoragePrefix + ':scope';
  var presenceTabId = null;
  var lastTypingSignal = 0;
  var typingIndicator = null;
  var announcer = null;
  let jumpButton = null;

  if (Array.isArray(state.requests)) {
    state.requests.forEach(registerChannel);
  }

  if (listButtons.length) {
    bindChannelButtons();
    resultCache.set(buildQueryKey('all', ''), state.requests || []);
  }

  function scheduleSearch() {
    if (!list) return;
    const key = buildQueryKey();
    if (resultCache.has(key)) {
      renderChannelList(resultCache.get(key) || []);
      return;
    }
    if (searchDebounce) {
      clearTimeout(searchDebounce);
    }
    searchDebounce = setTimeout(() => {
      searchDebounce = null;
      executeRemoteSearch(key);
    }, 350);
  }

  function executeRemoteSearch(cacheKey) {
    const params = buildQueryParams();
    if (!params) return;
    if (inflightController) {
      inflightController.abort();
    }
    const controller = new AbortController();
    inflightController = controller;
    setLoading(true);
    fetch(`/api/requests?${params}`, {
      headers: { 'X-Requested-With': 'Fetch', Accept: 'application/json' },
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to load requests');
        }
        return response.json();
      })
      .then((payload) => {
        const normalized = Array.isArray(payload)
          ? payload.map(normalizeChannelPayload)
          : [];
        resultCache.set(cacheKey, normalized);
        if (buildQueryKey() === cacheKey) {
          renderChannelList(normalized);
        }
      })
      .catch((error) => {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Channel search failed', error);
      })
      .finally(() => {
        if (inflightController === controller) {
          inflightController = null;
          setLoading(false);
        }
      });
  }

  function buildQueryParams() {
    const params = new URLSearchParams();
    params.set('include_channel_meta', '1');
    params.set('limit', '200');
    const trimmed = searchTerm.trim();
    if (trimmed) {
      params.set('search', trimmed);
    }
    if (activeFilter === 'open' || activeFilter === 'completed') {
      params.append('status', activeFilter);
    } else if (activeFilter === 'pinned') {
      params.set('pinned_only', '1');
    }
    return params.toString();
  }

  function normalizeChannelPayload(entry) {
    const description = (entry.description || '').trim();
    const firstLine = description.split(/\r?\n/)[0]?.trim() || '';
    const title = (firstLine || `Request #${entry.id || ''}`).slice(0, 120);
    return {
      id: entry.id,
      title,
      preview: truncateText(description, 160),
      status: entry.status || 'open',
      updated_at: entry.updated_at,
      is_pinned: Boolean(entry.is_pinned),
      pin_rank: entry.pin_rank ?? null,
      comment_count: entry.comment_count ?? 0,
      unread_count: entry.unread_count ?? 0,
    };
  }

  function truncateText(value, limit) {
    if (!value) return '';
    if (value.length <= limit) return value;
    return `${value.slice(0, limit - 3)}...`;
  }

  function registerChannel(channel) {
    if (!channel || !channel.id) return;
    const id = Number(channel.id);
    if (!Number.isFinite(id)) return;
    channel.id = id;
    channelMeta[id] = channel;
    channelStore.set(id, channel);
  }

  function registerChannels(rows) {
    if (!Array.isArray(rows)) return;
    rows.forEach(registerChannel);
  }

  function syncButtonCache() {
    listButtons = list ? Array.from(list.querySelectorAll('[data-channel-node]')) : [];
    priorityButtons = priorityList
      ? Array.from(priorityList.querySelectorAll('[data-channel-node]'))
      : [];
    buttons = [...priorityButtons, ...listButtons];
  }

  function getPinnedChannels() {
    const pinned = [];
    channelStore.forEach((row) => {
      if (row && row.is_pinned) {
        pinned.push(row);
      }
    });
    pinned.sort(comparePinnedChannels);
    return pinned;
  }

  function comparePinnedChannels(a, b) {
    const aRank = Number.isFinite(a.pin_rank) ? a.pin_rank : Number.MAX_SAFE_INTEGER;
    const bRank = Number.isFinite(b.pin_rank) ? b.pin_rank : Number.MAX_SAFE_INTEGER;
    if (aRank !== bRank) {
      return aRank - bRank;
    }
    const aId = Number(a.id);
    const bId = Number(b.id);
    if (Number.isFinite(aId) && Number.isFinite(bId)) {
      return aId - bId;
    }
    return 0;
  }

  function renderPriorityList(rows) {
    if (!priorityList) return;
    priorityList.innerHTML = '';
    if (!rows || !rows.length) return;
    const fragment = document.createDocumentFragment();
    rows.forEach((row) => {
      fragment.appendChild(createChannelButton(row));
    });
    priorityList.appendChild(fragment);
  }

  function removePinnedFromList(pinnedIds) {
    if (!list || !pinnedIds || !pinnedIds.size) return;
    list.querySelectorAll('[data-channel-node]').forEach((btn) => {
      const channelId = Number(btn.dataset.channelId);
      if (pinnedIds.has(channelId)) {
        btn.remove();
      }
    });
  }

  function updateListEmptyState() {
    if (!list) return;
    const hasVisibleList = listButtons.some((btn) => btn.style.display !== 'none');
    const hasPriority = priorityButtons.length > 0;
    let empty = list.querySelector('[data-channel-list-empty]');
    if (hasVisibleList || hasPriority) {
      if (empty) {
        empty.remove();
      }
      return;
    }
    if (!empty) {
      empty = document.createElement('p');
      empty.className = 'muted';
      empty.textContent = 'No requests match the current filters.';
      empty.setAttribute('data-channel-list-empty', '');
      list.appendChild(empty);
    }
  }

  function syncPriorityList() {
    if (!priorityList) {
      syncButtonCache();
      updateListEmptyState();
      return;
    }
    const pinnedRows = getPinnedChannels();
    const pinnedIds = new Set(pinnedRows.map((row) => Number(row.id)));
    const priorityRows = [...pinnedRows];
    const activeId = Number(state.active_channel_id);
    if (Number.isFinite(activeId) && !pinnedIds.has(activeId)) {
      const activeButton = list
        ? list.querySelector(`[data-channel-id="${activeId}"]`)
        : null;
      const activeVisible = activeButton && activeButton.style.display !== 'none';
      if (!activeVisible) {
        const activeRow = channelStore.get(activeId) || channelMeta[activeId];
        if (activeRow) {
          priorityRows.push(activeRow);
        }
      }
    }
    renderPriorityList(priorityRows);
    removePinnedFromList(pinnedIds);
    if (priority) {
      if (priorityRows.length) {
        priority.removeAttribute('hidden');
      } else {
        priority.setAttribute('hidden', 'hidden');
      }
    }
    syncButtonCache();
    updateListEmptyState();
    bindChannelButtons();
  }

  function renderChannelList(rows) {
    if (!list) return;
    state.requests = rows;
    registerChannels(rows);
    list.innerHTML = '';
    const fragment = document.createDocumentFragment();
    rows.forEach((row) => {
      fragment.appendChild(createChannelButton(row));
    });
    list.appendChild(fragment);
    syncButtonCache();
    applyFilters();
    announceResults(rows.length);
  }

  function updateChannelQuery(channelId) {
    try {
      const url = new URL(window.location.href);
      if (Number(channelId)) {
        url.searchParams.set('channel', channelId);
      } else {
        url.searchParams.delete('channel');
      }
      history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
    } catch (error) {
      // Ignore if History API unsupported
    }
  }

  function createChannelButton(channel) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'request-channel';
    button.dataset.channelId = channel.id;
    button.dataset.channelStatus = channel.status;
    button.dataset.channelPinned = channel.is_pinned ? 'true' : 'false';
    button.setAttribute('data-channel-node', '');
    if (Number(channel.id) === Number(state.active_channel_id)) {
      button.setAttribute('aria-current', 'true');
    }

    const title = document.createElement('span');
    title.className = 'request-channel__title';
    title.textContent = channel.title;

    const meta = document.createElement('span');
    meta.className = 'request-channel__meta';
    const status = document.createElement('span');
    status.className = 'request-channel__status';
    status.textContent = (channel.status || '').replace(/^(.)/, (match) => match.toUpperCase());
    const time = document.createElement('span');
    time.className = 'request-channel__time';
    time.dataset.channelTime = '';
    if (channel.updated_at) {
      time.setAttribute('data-timestamp', channel.updated_at);
    }
    const presence = document.createElement('span');
    presence.className = 'request-channel__presence';
    presence.setAttribute('data-channel-presence', '');
    presence.setAttribute('hidden', 'hidden');
    meta.append(status, time, presence);

    const badges = document.createElement('div');
    badges.className = 'request-channel__badges';
    if (channel.is_pinned) {
      const pin = document.createElement('span');
      pin.className = 'request-channel__pin';
      pin.setAttribute('aria-label', 'Pinned channel');
      pin.textContent = '📌';
      badges.appendChild(pin);
    }
    if (channel.comment_count) {
      const replies = document.createElement('span');
      replies.className = 'request-channel__badge';
      replies.setAttribute('data-channel-replies', '');
      replies.textContent = `${channel.comment_count} replies`;
      badges.appendChild(replies);
    }
    if (channel.unread_count) {
      const unread = document.createElement('span');
      unread.className = 'request-channel__badge request-channel__badge--unread';
      unread.setAttribute('data-channel-unread', '');
      unread.textContent = channel.unread_count;
      badges.appendChild(unread);
    }

    button.append(title, meta, badges);
    registerChannel(channel);
    return button;
  }

  function bindChannelButtons() {
    syncButtonCache();
    buttons.forEach((btn) => {
      if (!btn.dataset.channelBound) {
        btn.dataset.channelBound = 'true';
        btn.addEventListener('click', () => {
          const channelId = Number(btn.dataset.channelId);
          selectChannel(channelId, btn);
        });
      }
      updateRelativeTime(btn);
    });
  }

  function setLoading(isLoading) {
    if (!list) return;
    if (isLoading) {
      list.setAttribute('aria-busy', 'true');
      container.setAttribute('data-loading', 'true');
    } else {
      list.removeAttribute('aria-busy');
      container.removeAttribute('data-loading');
    }
  }

  function announceResults(count) {
    if (!resultsAnnouncer) return;
    resultsAnnouncer.textContent = `${count} channel${count === 1 ? '' : 's'} loaded`;
    if (visibleCount) {
      visibleCount.textContent = count;
    }
  }

  wireChatPane(chatPane);
  restoreScrollState({ stick: true, distance: 0 });
  const heartbeat = setInterval(pingPresenceHeartbeat, presenceHeartbeatInterval);
  const presencePoller = setInterval(refreshPresence, presencePollInterval);
  refreshPresence();
  window.addEventListener('storage', handlePresenceStorage);
  window.addEventListener('pagehide', clearPresenceScope);
  window.addEventListener('beforeunload', () => {
    clearInterval(heartbeat);
    clearInterval(presencePoller);
    clearPresenceScope();
  });

  function buildQueryKey(filter = activeFilter, term = searchTerm) {
    return `${filter}::${term.trim().toLowerCase()}`;
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      searchTerm = searchInput.value;
      applyFilters();
      scheduleSearch();
    });
  }

  if (filters) {
    filters.addEventListener('click', (event) => {
      const target = event.target;
      const button = target instanceof Element ? target.closest('[data-channel-filter]') : null;
      if (!button) return;
      activeFilter = button.dataset.channelFilter || defaultFilter;
      syncFilterButtons();
      applyFilters();
      scheduleSearch();
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

  syncFilterButtons();
  applyFilters();
  if (activeFilter !== 'all') {
    scheduleSearch();
  }

  function selectChannel(channelId, button) {
    buttons.forEach((btn) => btn.removeAttribute('aria-current'));
    if (button) {
      button.setAttribute('aria-current', 'true');
    }
    state.active_channel_id = channelId;
    syncPriorityList();
    updateChannelQuery(channelId);
    if (emptyState && chatPane) {
      emptyState.setAttribute('hidden', 'hidden');
      chatPane.removeAttribute('aria-busy');
    }
    loadChannel(channelId, { preserveScroll: false });
    sendPresencePing(false);
  }

  function updateRelativeTime(button) {
    const target = button.querySelector('[data-channel-time]');
    if (!target) return;
    const iso = target.getAttribute('data-timestamp');
    if (!iso) return;
    const date = new Date(iso);
    if (isNaN(date.getTime())) return;
    let label = '';
    if (typeof window.formatFriendlyTime === 'function') {
      label = window.formatFriendlyTime(date);
    }
    if (!label) {
      label = date.toLocaleString();
    }
    target.textContent = label;
  }

  function applyFilters() {
    updateStatusVisibility();
    const normalizedSearch = searchTerm.trim().toLowerCase();
    listButtons.forEach((btn) => {
      const status = (btn.dataset.channelStatus || '').toLowerCase();
      const isPinned = btn.dataset.channelPinned === 'true';
      const matchesSearch = btn.textContent.toLowerCase().includes(normalizedSearch);
      let matchesFilter = true;
      if (activeFilter === 'open' || activeFilter === 'completed') {
        matchesFilter = status === activeFilter;
      } else if (activeFilter === 'pinned') {
        matchesFilter = isPinned;
      }
      btn.style.display = matchesSearch && matchesFilter ? '' : 'none';
    });
    syncPriorityList();
  }

  function updateStatusVisibility() {
    if (!container) return;
    container.classList.toggle('request-channels--single-status', isSingleStatusView());
  }

  function isSingleStatusView(filter = activeFilter) {
    return filter === 'open' || filter === 'completed';
  }

  function syncFilterButtons() {
    if (!filters) return;
    filters.querySelectorAll('[data-channel-filter]').forEach((node) => {
      const isActive = node.dataset.channelFilter === activeFilter;
      node.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
  }

  function captureScrollState() {
    const log = chatPane?.querySelector('[data-channel-log]');
    if (!log) {
      return { stick: true, distance: 0 };
    }
    const distance = log.scrollHeight - log.clientHeight - log.scrollTop;
    return { stick: distance < 32, distance };
  }

  function restoreScrollState(state) {
    const log = chatPane?.querySelector('[data-channel-log]');
    if (!log) {
      return;
    }
    if (state.stick) {
      log.scrollTop = log.scrollHeight;
      setJumpVisibility(false);
    } else {
      const target = Math.max(log.scrollHeight - log.clientHeight - state.distance, 0);
      log.scrollTop = target;
      setJumpVisibility(true);
    }
  }

  function isNearBottom(log) {
    if (!log) return true;
    const distance = log.scrollHeight - log.clientHeight - log.scrollTop;
    return distance < 32;
  }

  function setJumpVisibility(show) {
    if (!jumpButton) return;
    if (show) {
      jumpButton.removeAttribute('hidden');
    } else {
      jumpButton.setAttribute('hidden', 'hidden');
    }
  }

  function wireChatPane(pane) {
    if (!pane) return;
    const composer = pane.querySelector('[data-channel-composer]');
    typingIndicator = pane.querySelector('[data-channel-typing]');
    announcer = pane.querySelector('[data-channel-announcer]');
    jumpButton = pane.querySelector('[data-channel-jump]');
    if (composer && !composer.dataset.channelComposerBound) {
      composer.dataset.channelComposerBound = 'true';
      composer.addEventListener('submit', handleComposerSubmit);
      const input = composer.querySelector('[data-channel-composer-input]');
      if (input) {
        input.addEventListener('input', handleTypingEvent);
      }
    }
    const log = pane.querySelector('[data-channel-log]');
    if (log && !log.dataset.channelScrollBound) {
      log.dataset.channelScrollBound = 'true';
      log.addEventListener('scroll', () => {
        if (isNearBottom(log)) {
          setJumpVisibility(false);
        }
      });
    }
    if (jumpButton && !jumpButton.dataset.channelJumpBound) {
      jumpButton.dataset.channelJumpBound = 'true';
      jumpButton.addEventListener('click', () => {
        const targetLog = pane.querySelector('[data-channel-log]');
        if (targetLog) {
          targetLog.scrollTo({ top: targetLog.scrollHeight, behavior: 'smooth' });
        }
        setJumpVisibility(false);
      });
    }
  }

  function handleTypingEvent() {
    const now = Date.now();
    if (now - lastTypingSignal < 2000) {
      return;
    }
    lastTypingSignal = now;
    sendPresencePing(true);
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

  async function loadChannel(channelId, options = {}) {
    if (!chatPane || !channelId) {
      return;
    }
    const preserveScroll = options.preserveScroll !== false;
    const scrollState = preserveScroll ? captureScrollState() : { stick: true, distance: 0 };
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
      restoreScrollState(scrollState);
      if (payload.channel) {
        updateChannelRowMeta(payload.channel);
      }
      announce('Channel updated');
    } catch (error) {
      console.error('Failed to load channel', error);
    } finally {
      chatPane.removeAttribute('aria-busy');
    }
  }

  function updateChannelRowMeta(channel) {
    const channelId = Number(channel.id);
    const existing = channelStore.get(channelId) || channelMeta[channelId] || {};
    const merged = { ...existing, ...channel, id: channelId };
    registerChannel(merged);
    const button = buttons.find((btn) => Number(btn.dataset.channelId) === channelId);
    if (!button) return;
    let replyBadge = button.querySelector('[data-channel-replies]');
    if (typeof channel.comment_count === 'number' && channel.comment_count > 0) {
      if (!replyBadge) {
        const holder = button.querySelector('.request-channel__badges');
        if (holder) {
          replyBadge = document.createElement('span');
          replyBadge.className = 'request-channel__badge';
          replyBadge.setAttribute('data-channel-replies', '');
          const unread = holder.querySelector('[data-channel-unread]');
          holder.insertBefore(replyBadge, unread || null);
        }
      }
      if (replyBadge) {
        replyBadge.textContent = `${channel.comment_count} replies`;
      }
    } else if (replyBadge) {
      replyBadge.remove();
    }
    const unreadBadge = button.querySelector('[data-channel-unread]');
    if (unreadBadge) {
      unreadBadge.remove();
    }
  }

  function safeStorageGet(key) {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      return null;
    }
  }

  function safeStorageSet(key, value) {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      return false;
    }
  }

  function safeStorageRemove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      return false;
    }
  }

  function readJsonStorage(key) {
    const raw = safeStorageGet(key);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (error) {
      return null;
    }
  }

  function writeJsonStorage(key, value) {
    return safeStorageSet(key, JSON.stringify(value));
  }

  function getPresenceTabId() {
    if (presenceTabId) {
      return presenceTabId;
    }
    let stored = null;
    try {
      stored = sessionStorage.getItem(presenceTabKey);
    } catch (error) {
      stored = null;
    }
    if (!stored) {
      stored = `tab-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
      try {
        sessionStorage.setItem(presenceTabKey, stored);
      } catch (error) {
        /* no-op */
      }
    }
    presenceTabId = stored;
    return stored;
  }

  function normalizePresenceIds(ids) {
    if (!Array.isArray(ids)) return [];
    const list = [];
    ids.forEach((id) => {
      const value = Number(id);
      if (Number.isFinite(value)) {
        list.push(value);
      }
    });
    return list;
  }

  function shouldSendPresencePing(key, intervalMs) {
    const now = Date.now();
    const payload = readJsonStorage(key);
    const lastAt = payload && typeof payload.at === 'number' ? payload.at : 0;
    if (now - lastAt < intervalMs) {
      return false;
    }
    writeJsonStorage(key, { at: now, tab: getPresenceTabId() });
    return true;
  }

  function readPresenceScope() {
    const scopes = readJsonStorage(presenceScopeKey);
    if (!scopes || typeof scopes !== 'object') {
      return {};
    }
    return scopes;
  }

  function writePresenceScope(scopes) {
    if (!scopes || typeof scopes !== 'object') {
      return false;
    }
    return writeJsonStorage(presenceScopeKey, scopes);
  }

  function prunePresenceScopes(scopes, now) {
    if (!scopes || typeof scopes !== 'object') {
      return { scopes: {}, changed: true };
    }
    const cleaned = {};
    let changed = false;
    Object.keys(scopes).forEach((tabId) => {
      const entry = scopes[tabId] || {};
      const updatedAt = Number(entry.updated_at) || 0;
      if (!updatedAt || now - updatedAt > presenceScopeTtl) {
        changed = true;
        return;
      }
      const ids = normalizePresenceIds(entry.ids);
      cleaned[tabId] = { updated_at: updatedAt, ids: ids };
      if (!entry.ids || ids.length !== entry.ids.length) {
        changed = true;
      }
    });
    if (Object.keys(cleaned).length !== Object.keys(scopes).length) {
      changed = true;
    }
    return { scopes: cleaned, changed: changed };
  }

  function upsertPresenceScope(ids) {
    const tabId = getPresenceTabId();
    const now = Date.now();
    const scopes = readPresenceScope();
    scopes[tabId] = { updated_at: now, ids: normalizePresenceIds(ids) };
    const result = prunePresenceScopes(scopes, now);
    writePresenceScope(result.scopes);
  }

  function readPresenceScopeIds() {
    const now = Date.now();
    const scopes = readPresenceScope();
    const result = prunePresenceScopes(scopes, now);
    if (result.changed) {
      writePresenceScope(result.scopes);
    }
    const idSet = new Set();
    Object.keys(result.scopes).forEach((tabId) => {
      const entry = result.scopes[tabId];
      const ids = entry && Array.isArray(entry.ids) ? entry.ids : [];
      ids.forEach((id) => {
        const value = Number(id);
        if (Number.isFinite(value)) {
          idSet.add(value);
        }
      });
    });
    return Array.from(idSet);
  }

  function clearPresenceScope() {
    const tabId = getPresenceTabId();
    const scopes = readPresenceScope();
    if (!scopes[tabId]) {
      return;
    }
    delete scopes[tabId];
    writePresenceScope(scopes);
  }

  function storePresencePayload(presence) {
    return writeJsonStorage(presencePayloadKey, {
      updated_at: Date.now(),
      presence: presence || {},
    });
  }

  function readPresencePayload() {
    const payload = readJsonStorage(presencePayloadKey);
    if (!payload || typeof payload.updated_at !== 'number') {
      return null;
    }
    if (Date.now() - payload.updated_at > presencePayloadTtl) {
      return null;
    }
    return payload.presence || null;
  }

  function applyPresencePayload(presence) {
    if (!presence) return;
    updatePresenceIndicators(presence);
  }

  async function sendPresencePing(isTyping) {
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

  function pingPresenceHeartbeat() {
    const requestId = Number(state.active_channel_id);
    if (!Number.isFinite(requestId)) return;
    const key = `${presenceHeartbeatKey}:${requestId}`;
    if (!shouldSendPresencePing(key, presenceHeartbeatInterval)) {
      return;
    }
    sendPresencePing(false);
  }

  function buildPresenceIdList() {
    const idSet = new Set(
      buttons
        .map((btn) => Number(btn.dataset.channelId))
        .filter((id) => Number.isFinite(id)),
    );
    if (Number(state.active_channel_id)) {
      idSet.add(Number(state.active_channel_id));
    }
    return Array.from(idSet).filter((id) => Number.isFinite(id));
  }

  async function refreshPresence() {
    const ids = buildPresenceIdList();
    if (!ids.length) {
      clearPresenceScope();
      return;
    }
    upsertPresenceScope(ids);
    const scopeIds = readPresenceScopeIds();
    const pollIds = scopeIds.length ? scopeIds : ids;
    if (!pollIds.length) return;
    if (!shouldSendPresencePing(presencePollKey, presencePollInterval)) {
      applyPresencePayload(readPresencePayload());
      return;
    }
    const params = pollIds.map((id) => `id=${id}`).join('&');
    try {
      const response = await fetch(`/requests/channels/presence?${params}`, {
        headers: { 'X-Requested-With': 'Fetch', Accept: 'application/json' },
      });
      if (!response.ok) return;
      const payload = await response.json();
      const presence = payload.presence || {};
      storePresencePayload(presence);
      updatePresenceIndicators(presence);
    } catch (error) {
      console.warn('Presence polling failed', error);
    }
  }

  function handlePresenceStorage(event) {
    if (!event || event.key !== presencePayloadKey) return;
    const payload = readPresencePayload();
    if (payload) {
      updatePresenceIndicators(payload);
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
