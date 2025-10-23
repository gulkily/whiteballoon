(() => {
  const API_BASE = '/api/requests';

  function init() {
    const card = document.querySelector('[data-request-card]');
    const list = document.querySelector('[data-request-list]');
    if (!card || !list) {
      return;
    }

    setupForm(card, list);
    setupList(list);
  }

  function setupForm(card, list) {
    const collapsed = card.querySelector('[data-request-collapsed]');
    const form = card.querySelector('[data-request-form]');
    if (!form) {
      return;
    }

    const showButton = collapsed?.querySelector('[data-request-action="show-form"]');
    const cancelButton = form.querySelector('[data-request-action="cancel-form"]');
    const descriptionField = form.querySelector('textarea[name="description"]');

    if (collapsed) {
      collapsed.hidden = false;
    }

    hideForm(card);

    showButton?.addEventListener('click', (event) => {
      event.preventDefault();
      hideStatus(card);
      showForm(card);
      descriptionField?.focus();
    });

    cancelButton?.addEventListener('click', (event) => {
      event.preventDefault();
      hideStatus(card);
      hideForm(card);
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      hideStatus(card);

      const formData = new FormData(form);
      const description = (formData.get('description') || '').toString().trim();
      const contactEmailRaw = formData.get('contact_email');
      const contact_email = contactEmailRaw ? contactEmailRaw.toString().trim() || null : null;

      if (!description) {
        showStatus(card, 'Description is required.', 'error');
        return;
      }

      const submitButton = form.querySelector('button[type="submit"]');
      submitButton?.setAttribute('disabled', 'true');
      showStatus(card, 'Posting request…', 'info');

      try {
        const response = await fetch(API_BASE, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          body: JSON.stringify({ description, contact_email }),
        });

        if (!response.ok) {
          throw new Error(`Request creation failed with status ${response.status}`);
        }

        await refreshList(list);
        form.reset();
        hideForm(card);
        showStatus(card, 'Request posted.', 'success');
      } catch (error) {
        console.error(error);
        showStatus(card, 'Unable to post the request. Please try again.', 'error');
      } finally {
        submitButton?.removeAttribute('disabled');
      }
    });
  }

  function setupList(list) {
    list.addEventListener('submit', async (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) {
        return;
      }

      if (!form.matches('[data-request-complete]')) {
        return;
      }

      event.preventDefault();

      const requestId = form.dataset.requestId;
      if (!requestId) {
        return;
      }

      const button = form.querySelector('button[type="submit"]');
      button?.setAttribute('disabled', 'true');

      try {
        const response = await fetch(`${API_BASE}/${requestId}/complete`, {
          method: 'POST',
          headers: {
            Accept: 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Complete request failed with status ${response.status}`);
        }

        await refreshList(list);
      } catch (error) {
        console.error(error);
        button?.removeAttribute('disabled');
        showGlobalMessage('Unable to mark the request complete.');
      }
    });
  }

  async function refreshList(list) {
    const response = await fetch(API_BASE, { headers: { Accept: 'application/json' } });
    if (!response.ok) {
      throw new Error('Failed to refresh request list.');
    }

    const requests = await response.json();
    renderRequests(list, Array.isArray(requests) ? requests : []);
  }

  function renderRequests(list, requests) {
    if (!requests.length) {
      list.innerHTML = '<div class="card"><p class="muted">No requests yet. Be the first to share a need.</p></div>';
      return;
    }

    const items = requests.map(renderRequestItem).join('');
    list.innerHTML = `<div class="requests-grid">${items}</div>`;
  }

  function renderRequestItem(item) {
    const createdAt = formatDate(item.created_at);
    const completedAt = item.completed_at ? formatDate(item.completed_at) : null;
    const badgeClass = item.status === 'completed' ? 'badge badge--completed' : 'badge';

    const completeSection =
      item.status === 'completed'
        ? `<span class="muted">Completed ${completedAt ?? 'recently'}</span>`
        : `<form method="post" action="/requests/${item.id}/complete" data-request-complete data-request-id="${item.id}" class="inline">\n            <button type="submit" class="button">Mark completed</button>\n          </form>`;

    const contactSection = item.contact_email
      ? `<span class="muted">Contact: ${escapeHtml(item.contact_email)}</span>`
      : '';

    return `<article class=\"request-item\">\n  <header class=\"request-meta\">\n    <span class=\"${badgeClass}\">${capitalize(item.status)}</span>\n    <time datetime=\"${escapeHtml(item.created_at)}\" class=\"muted\">${createdAt}</time>\n  </header>\n  <div>\n    <p>${escapeHtml(item.description || 'No additional details.')}</p>\n  </div>\n  <footer class=\"actions\">\n    ${completeSection}\n    ${contactSection}\n  </footer>\n</article>`;
  }

  function showForm(card) {
    const form = card.querySelector('[data-request-form]');
    const collapsed = card.querySelector('[data-request-collapsed]');
    if (form) {
      form.hidden = false;
    }
    if (collapsed) {
      collapsed.hidden = true;
    }
    card.classList.add('is-expanded');
    card.classList.remove('is-collapsed');
  }

  function hideForm(card) {
    const form = card.querySelector('[data-request-form]');
    const collapsed = card.querySelector('[data-request-collapsed]');
    if (form) {
      form.hidden = true;
    }
    if (collapsed) {
      collapsed.hidden = false;
    }
    card.classList.remove('is-expanded');
    card.classList.add('is-collapsed');
  }

  function hideStatus(card) {
    const status = card.querySelector('[data-request-status]');
    if (status) {
      status.textContent = '';
      status.dataset.tone = '';
    }
  }

  function showStatus(card, message, tone) {
    const status = card.querySelector('[data-request-status]');
    if (status) {
      status.textContent = message;
      status.dataset.tone = tone;
    }
  }

  function showGlobalMessage(message) {
    const card = document.querySelector('[data-request-card]');
    if (card) {
      showStatus(card, message, 'error');
    }
  }

  function formatDate(value) {
    try {
      const date = new Date(value);
      return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch (error) {
      return value?.toString().replace('T', ' ').replace('Z', '') ?? '';
    }
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    }[char]));
  }

  function capitalize(value) {
    if (!value) {
      return '';
    }
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  document.addEventListener('DOMContentLoaded', init);

})();
