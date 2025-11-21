(function () {
  var statusNodes = document.querySelectorAll('[data-job-status]');
  var controlNodes = document.querySelectorAll('[data-job-control]');
  if (!statusNodes.length && !controlNodes.length) {
    return;
  }

  var tiles = mapNodes(statusNodes, createTileController);
  var controls = mapNodes(controlNodes, createControlController);

  var channel = createRealtimeChannel(tiles, controls);
  channel.start();

  function mapNodes(list, factory) {
    var result = [];
    for (var i = 0; i < list.length; i += 1) {
      var instance = factory(list[i]);
      if (instance) {
        result.push(instance);
      }
    }
    return result;
  }
})();

function createTileController(node) {
  var dataset = node.dataset || {};
  var action = dataset.jobAction || null;
  var targetValue = dataset.jobTarget || null;
  var targetField = dataset.jobTargetField || 'peer';
  var emptyMessage = dataset.jobEmptyMessage || 'No recent activity yet.';
  var messageEl = node.querySelector('[data-role="message"]');
  var stateEl = node.querySelector('[data-role="state"]');
  var queuedEl = node.querySelector('[data-role="queued"]');
  var startedEl = node.querySelector('[data-role="started"]');
  var finishedEl = node.querySelector('[data-role="finished"]');
  var lastBadgeState = null;

  var controller = {
    element: node,
    apply: apply,
    matches: matches,
    renderIdle: renderIdle,
  };

  return controller;

  function matches(job) {
    if (!job) {
      return false;
    }
    var currentId = node.getAttribute('data-job-id');
    if (currentId && job.id === currentId) {
      return true;
    }
    if (!job.target) {
      return false;
    }
    if (action && job.target.action !== action) {
      return false;
    }
    if (targetValue) {
      var scopedValue = targetField ? job.target[targetField] : null;
      if (scopedValue !== targetValue) {
        return false;
      }
    }
    return true;
  }

  function apply(job) {
    if (!job) {
      renderIdle();
      return;
    }
    if (job.id) {
      node.setAttribute('data-job-id', job.id);
    }
    var state = (job.state || job.status || 'queued').toString().toLowerCase();
    node.setAttribute('data-job-state', state);
    updateBadge(state);
    updateMessage(job, state);
    renderTime(queuedEl, job.queued_at || job.queuedAt);
    renderTime(startedEl, job.started_at || job.startedAt);
    renderTime(finishedEl, job.finished_at || job.finishedAt);
  }

  function renderIdle() {
    node.removeAttribute('data-job-id');
    node.setAttribute('data-job-state', 'idle');
    updateBadge('idle');
    if (messageEl) {
      messageEl.textContent = emptyMessage;
    }
    renderTime(queuedEl, null);
    renderTime(startedEl, null);
    renderTime(finishedEl, null);
  }

  function updateBadge(state) {
    if (!stateEl) {
      return;
    }
    var normalized = normalizeState(state);
    stateEl.textContent = formatStateLabel(normalized);
    var base = 'realtime-status__badge--';
    if (lastBadgeState) {
      stateEl.classList.remove(base + lastBadgeState);
    }
    stateEl.classList.add(base + normalized);
    lastBadgeState = normalized;
  }

  function updateMessage(job, state) {
    if (!messageEl) {
      return;
    }
    var text = job.message || job.status_label || formatStateLabel(state);
    messageEl.textContent = text;
  }
}

function createControlController(node) {
  var dataset = node.dataset || {};
  var action = dataset.jobAction || null;
  var targetValue = dataset.jobTarget || null;
  var targetField = dataset.jobTargetField || 'peer';

  return {
    element: node,
    matches: matches,
    apply: apply,
  };

  function matches(job) {
    if (!job) {
      return false;
    }
    var currentId = node.getAttribute('data-job-id');
    if (currentId && job.id === currentId) {
      return true;
    }
    if (!job.target) {
      return false;
    }
    if (action && job.target.action !== action) {
      return false;
    }
    if (targetValue) {
      var scopedValue = targetField ? job.target[targetField] : null;
      if (scopedValue !== targetValue) {
        return false;
      }
    }
    return true;
  }

  function apply(job) {
    if (!job) {
      enable();
      return;
    }
    var state = (job.state || job.status || '').toLowerCase();
    if (job.id) {
      node.setAttribute('data-job-id', job.id);
    }
    if (state === 'queued' || state === 'pending' || state === 'running') {
      node.setAttribute('disabled', '');
    } else {
      enable();
    }
  }

  function enable() {
    node.removeAttribute('disabled');
    node.removeAttribute('data-job-id');
  }
}

function normalizeState(state) {
  return state ? state.replace(/\s+/g, '-').toLowerCase() : 'idle';
}

function formatStateLabel(state) {
  if (!state) {
    return 'Idle';
  }
  var spaced = state.replace(/[-_]+/g, ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function renderTime(slot, value) {
  if (!slot) {
    return;
  }
  slot.textContent = '';
  if (!value) {
    var span = document.createElement('span');
    span.className = 'muted';
    span.textContent = '—';
    slot.appendChild(span);
    return;
  }
  var date = value instanceof Date ? value : new Date(value);
  if (isNaN(date.getTime())) {
    var fallback = document.createElement('span');
    fallback.textContent = value;
    slot.appendChild(fallback);
    return;
  }
  var timeEl = document.createElement('time');
  timeEl.dateTime = date.toISOString();
  timeEl.textContent = formatRelativeTime(date);
  slot.appendChild(timeEl);
}

function formatRelativeTime(date) {
  var deltaSeconds = Math.round((Date.now() - date.getTime()) / 1000);
  var future = deltaSeconds < 0;
  var absolute = Math.abs(deltaSeconds);
  var value;
  var unit;

  if (absolute < 60) {
    value = absolute;
    unit = 's';
  } else if (absolute < 3600) {
    value = Math.round(absolute / 60);
    unit = 'm';
  } else if (absolute < 86400) {
    value = Math.round(absolute / 3600);
    unit = 'h';
  } else {
    value = Math.round(absolute / 86400);
    unit = 'd';
  }

  if (future) {
    return 'in ' + value + unit;
  }
  return value + unit + ' ago';
}

function createRealtimeChannel(tiles, controls) {
  var source = null;
  var reconnectTimer = null;
  var reconnectDelay = 1000;
  var maxDelay = 30000;
  var pollTimer = null;
  var pollInterval = 3000;
  var tileList = tiles || [];
  var controlList = controls || [];

  return {
    start: start,
  };

  function start() {
    connect();
    if (!supportsEventSource()) {
      startPolling();
    }
  }

  function connect() {
    if (!supportsEventSource()) {
      return;
    }
    closeSource();
    try {
      source = new EventSource('/api/admin/jobs/events');
    } catch (err) {
      source = null;
      startPolling();
      scheduleReconnect();
      return;
    }

    source.addEventListener('open', function () {
      reconnectDelay = 1000;
      stopPolling();
    });

    source.addEventListener('job-update', function (event) {
      try {
        var payload = JSON.parse(event.data);
        dispatch(payload);
      } catch (err) {
        // ignore malformed payloads
      }
    });

    source.addEventListener('error', function () {
      closeSource();
      startPolling();
      scheduleReconnect();
    });
  }

  function dispatch(job) {
    for (var i = 0; i < tileList.length; i += 1) {
      var tile = tileList[i];
      if (tile.matches(job)) {
        tile.apply(job);
      }
    }
    for (var j = 0; j < controlList.length; j += 1) {
      var control = controlList[j];
      if (control.matches(job)) {
        control.apply(job);
      }
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer || !supportsEventSource()) {
      return;
    }
    reconnectTimer = window.setTimeout(function () {
      reconnectTimer = null;
      connect();
    }, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, maxDelay);
  }

  function startPolling() {
    if (pollTimer) {
      return;
    }
    pollTimer = window.setInterval(fetchSnapshots, pollInterval);
    fetchSnapshots();
  }

  function stopPolling() {
    if (!pollTimer) {
      return;
    }
    window.clearInterval(pollTimer);
    pollTimer = null;
  }

  function fetchSnapshots() {
    var url = '/api/admin/jobs?limit=100';
    if (window.fetch) {
      fetch(url, { credentials: 'same-origin' })
        .then(function (response) {
          if (!response.ok) {
            throw new Error('Request failed');
          }
          return response.json();
        })
        .then(handleSnapshotPayload)
        .catch(function () {
          // ignore
        });
    } else {
      var xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
          try {
            var data = JSON.parse(xhr.responseText);
            handleSnapshotPayload(data);
          } catch (err) {}
        }
      };
      xhr.send();
    }
  }

  function handleSnapshotPayload(payload) {
    if (!payload || !payload.jobs || !payload.jobs.length) {
      return;
    }
    for (var i = 0; i < payload.jobs.length; i += 1) {
      dispatch(payload.jobs[i]);
    }
  }

  function closeSource() {
    if (source) {
      source.close();
      source = null;
    }
  }
}

function supportsEventSource() {
  return typeof window !== 'undefined' && typeof window.EventSource !== 'undefined';
}
