(function () {
  const container = document.querySelector('[data-chat-search]');
  if (!container) {
    return;
  }

  const form = container.querySelector('[data-chat-search-form]');
  const input = container.querySelector('[data-chat-search-input]');
  const resultsList = container.querySelector('[data-chat-search-results]');
  const statusEl = container.querySelector('[data-chat-search-status]');
  const template = document.querySelector('#chat-search-result-template');
  const requestId = container.getAttribute('data-request-id');
  if (!form || !input || !resultsList || !template || !requestId) {
    return;
  }

  let debounceTimer;
  let currentAbort;

  const setStatus = (message) => {
    if (statusEl) {
      statusEl.textContent = message || '';
    }
  };

  const clearResults = () => {
    resultsList.innerHTML = '';
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

    if (!window.fetch) {
      form.submit();
      return;
    }

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
        clearResults();
        const results = payload.results || [];
        results.forEach((entry) => {
          const fragment = template.content.cloneNode(true);
          const author = fragment.querySelector('[data-author]');
          const profileLink = fragment.querySelector('[data-author-link]');
          const timeLink = fragment.querySelector('[data-time-link]');
          const time = fragment.querySelector('[data-time]');
          const body = fragment.querySelector('[data-body]');
          const tags = fragment.querySelector('[data-tags]');

          if (profileLink) {
            profileLink.href = `/people/${entry.username}`;
            profileLink.textContent = entry.display_name || `@${entry.username}`;
            profileLink.title = entry.display_name ? `@${entry.username}` : '';
          }
          if (author && profileLink) {
            author.replaceWith(profileLink);
          }

          if (timeLink && time) {
            time.textContent = new Date(entry.created_at).toLocaleString();
            time.dateTime = entry.created_at || '';
            timeLink.href = `#${entry.comment_anchor || entry.anchor}`;
          }
          if (body) {
            body.innerHTML = entry.body;
          }
          if (tags) {
            tags.innerHTML = '';
            (entry.topics || []).forEach((topic) => {
              const span = document.createElement('span');
              span.className = 'meta-chip meta-chip--small';
              span.textContent = topic;
              tags.appendChild(span);
            });
            (entry.ai_topics || []).forEach((topic) => {
              const span = document.createElement('span');
              span.className = 'meta-chip meta-chip--small meta-chip--ghost';
              span.textContent = topic;
              tags.appendChild(span);
            });
            if (!tags.children.length) {
              tags.remove();
            }
          }

          resultsList.appendChild(fragment);
        });
        setStatus(
          results.length ? `${results.length} result${results.length === 1 ? '' : 's'}` : 'No matches'
        );
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
    event.preventDefault();
    runSearch();
  });

  input.addEventListener('input', () => {
    if (debounceTimer) {
      window.clearTimeout(debounceTimer);
    }
    debounceTimer = window.setTimeout(runSearch, 350);
  });
})();
