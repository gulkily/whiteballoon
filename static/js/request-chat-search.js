(function () {
  const container = document.querySelector('[data-chat-search]');
  if (!container || !window.fetch) {
    return;
  }

  const form = container.querySelector('[data-chat-search-form]');
  const input = container.querySelector('[data-chat-search-input]');
  const resultsList = container.querySelector('[data-chat-search-results]');
  const statusEl = container.querySelector('[data-chat-search-status]');
  const requestId = container.getAttribute('data-request-id');
  if (!form || !input || !resultsList || !requestId) {
    return;
  }

  let debounceTimer;
  let currentAbort;

  const setStatus = (message) => {
    if (!statusEl) {
      return;
    }
    statusEl.textContent = message || '';
  };

  const clearResults = () => {
    resultsList.innerHTML = '';
  };

  const createTopicTag = (label, ghost = false) => {
    const span = document.createElement('span');
    span.className = ghost
      ? 'meta-chip meta-chip--small meta-chip--ghost'
      : 'meta-chip meta-chip--small';
    span.textContent = label;
    return span;
  };

  const highlightBody = (body, tokens) => {
    if (!tokens || !tokens.length) {
      return body;
    }
    let highlighted = body;
    tokens.forEach((token) => {
      if (!token) {
        return;
      }
      const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const pattern = new RegExp(`(${escaped})`, 'gi');
      highlighted = highlighted.replace(pattern, '<mark>$1</mark>');
    });
    return highlighted;
  };

  const renderResults = (results, displayNames) => {
    clearResults();
    if (!results || !results.length) {
      return;
    }
    const nameMap = displayNames || {};
    results.forEach((match) => {
      const item = document.createElement('li');
      item.className = 'card request-chat-search__result';

      const identity = document.createElement('div');
      identity.className = 'request-chat-search__identity';

      const authorLink = document.createElement('a');
      authorLink.className = 'request-chat-search__result-author';
      authorLink.href = `/people/${match.username}`;
      const displayName = nameMap[String(match.user_id)];
      if (displayName) {
        authorLink.textContent = displayName;
        authorLink.title = `@${match.username}`;
      } else {
        authorLink.textContent = `@${match.username}`;
      }
      identity.appendChild(authorLink);

      if (match.created_at) {
        const timeLink = document.createElement('a');
        timeLink.className = 'request-chat-search__result-time';
        timeLink.href = `#${match.anchor}`;
        const time = document.createElement('time');
        time.dateTime = match.created_at;
        time.textContent = new Date(match.created_at).toLocaleString();
        timeLink.appendChild(time);
        identity.appendChild(timeLink);
      }

      item.appendChild(identity);

      const body = document.createElement('p');
      body.className = 'request-chat-search__result-body';
      body.innerHTML = highlightBody(match.body || '', match.matched_tokens || []);
      item.appendChild(body);

      const topicWrapper = document.createElement('div');
      topicWrapper.className = 'request-chat-search__tags';
      (match.topics || []).forEach((topic) => {
        topicWrapper.appendChild(createTopicTag(topic));
      });
      (match.ai_topics || []).forEach((topic) => {
        topicWrapper.appendChild(createTopicTag(topic, true));
      });
      if (topicWrapper.childElementCount > 0) {
        item.appendChild(topicWrapper);
      }

      resultsList.appendChild(item);
    });
  };

  const runSearch = () => {
    const query = input.value.trim();
    if (currentAbort) {
      currentAbort.abort();
    }
    const controller = new AbortController();
    currentAbort = controller;

    if (!query) {
      clearResults();
      setStatus('');
      return;
    }

    const url = new URL(`/requests/${requestId}/chat-search`, window.location.origin);
    url.searchParams.set('q', query);

    setStatus('Searching…');
    fetch(url.toString(), {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Search failed (${response.status})`);
        }
        return response.json();
      })
      .then((payload) => {
        const results = payload.results || [];
        const displayNames = payload.display_names || {};
        renderResults(results, displayNames);
        if (!results.length) {
          setStatus('No matches');
        } else {
          setStatus(`${results.length} result${results.length === 1 ? '' : 's'}`);
        }
      })
      .catch((error) => {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Chat search failed', error);
        setStatus('Search failed. Try again.');
      });
  };

  form.addEventListener('submit', (event) => {
    if (!window.fetch) {
      return;
    }
    event.preventDefault();
    runSearch();
  });

  input.addEventListener('input', () => {
    if (!window.fetch) {
      return;
    }
    if (debounceTimer) {
      window.clearTimeout(debounceTimer);
    }
    debounceTimer = window.setTimeout(runSearch, 350);
  });
})();
