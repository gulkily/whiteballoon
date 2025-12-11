(function () {
  const queryParamMap = {
    resource: 'insight_resource',
    request: 'insight_request',
    urgency: 'insight_urgency',
    sentiment: 'insight_sentiment',
  };

  function init() {
    const card = document.querySelector('[data-insight-card]');
    if (!card) {
      return;
    }

    const chips = card.querySelectorAll('[data-insight-chip]');
    if (!chips.length) {
      return;
    }

    chips.forEach((chip) => {
      chip.addEventListener('click', (event) => {
        event.preventDefault();
        toggleChip(chip);
        applyFilters();
      });
    });

    const resetBtn = card.querySelector('[data-insight-reset]');
    if (resetBtn) {
      resetBtn.addEventListener('click', (event) => {
        event.preventDefault();
        chips.forEach((chip) => chip.classList.remove('is-active'));
        applyFilters();
      });
    }

    applyFilters();
  }

  function toggleChip(chip) {
    chip.classList.toggle('is-active');
  }

  function applyFilters() {
    const filters = collectFilters();
    filterComments(filters);
    updateUrl(filters);
    updateCounter(filters);
  }

  function collectFilters() {
    const chips = document.querySelectorAll('[data-insight-chip].is-active');
    const filters = { resource: [], request: [], urgency: [], sentiment: [] };
    chips.forEach((chip) => {
      const type = chip.getAttribute('data-insight-chip');
      const value = chip.getAttribute('data-insight-value');
      if (filters[type] && value) {
        filters[type].push(value);
      }
    });
    return filters;
  }

  function filterComments(filters) {
    const items = document.querySelectorAll('[data-comment-insight]');
    let visibleCount = 0;
    items.forEach((item) => {
    const metadata = item.getAttribute('data-comment-insight') || '';
    let parsed = {};
    if (metadata) {
      try {
        parsed = JSON.parse(metadata);
      } catch (error) {
        parsed = {};
      }
    }
    const matches = matchesFilters(parsed, filters);
      item.style.display = matches ? '' : 'none';
      if (matches) {
        visibleCount += 1;
      }
    });
    const list = document.querySelector('[data-comment-list]');
    if (list) {
      list.setAttribute('data-visible-count', String(visibleCount));
    }
  }

  function matchesFilters(metadata, filters) {
    function missing(values, selected) {
      if (!selected.length) {
        return false;
      }
      return !selected.some((value) => values.includes(value));
    }

    const resource = metadata.resource_tags || [];
    if (filters.resource.length && missing(resource, filters.resource)) {
      return false;
    }
    const request = metadata.request_tags || [];
    if (filters.request.length && missing(request, filters.request)) {
      return false;
    }
    const urgency = (metadata.urgency || '').toLowerCase();
    if (filters.urgency.length && !filters.urgency.includes(urgency)) {
      return false;
    }
    const sentiment = (metadata.sentiment || '').toLowerCase();
    if (filters.sentiment.length && !filters.sentiment.includes(sentiment)) {
      return false;
    }
    return true;
  }

  function updateUrl(filters) {
    const params = new URLSearchParams(window.location.search);
    Object.entries(queryParamMap).forEach(([type, param]) => {
      params.delete(param);
      const values = filters[type];
      values.forEach((value) => params.append(param, value));
    });
    const next = params.toString();
    const url = next ? `${window.location.pathname}?${next}` : window.location.pathname;
    window.history.replaceState({}, '', url);
  }

  function updateCounter(filters) {
    const counter = document.querySelector('[data-insight-counter]');
    if (!counter) {
      return;
    }
    const filtersActive = Object.values(filters).some((values) => values.length);
    const list = document.querySelector('[data-comment-list]');
    const total = list ? Number(list.getAttribute('data-total-count') || list.children.length) : 0;
    const visible = list ? Number(list.getAttribute('data-visible-count') || total) : total;
    counter.textContent = filtersActive ? `Showing ${visible} of ${total}` : '';
  }

  document.addEventListener('DOMContentLoaded', init);
})();
