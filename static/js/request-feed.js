(() => {
  const API_BASE = '/api/requests';

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-request-card]').forEach((card) => setupForm(card));
    document.querySelectorAll('[data-request-list]').forEach((list) => setupList(list));
  });
  document.addEventListener('click', handleCopyLinkClick);

  function setupForm(card) {
    const form = card.querySelector('[data-request-form]');
    const collapsed = card.querySelector('[data-request-collapsed]');
    const showButton = collapsed?.querySelector('[data-request-action="show-form"]');
    const cancelButton = form?.querySelector('[data-request-action="cancel-form"]');
    const readonly = card.dataset.readonly === 'true';

    if (collapsed) {
      collapsed.hidden = false;
    }
    hideForm(card);

    showButton?.addEventListener('click', (event) => {
      event.preventDefault();
      hideStatus(card);
      showForm(card);
      form?.querySelector('textarea[name="description"]')?.focus();
    });

    cancelButton?.addEventListener('click', (event) => {
      event.preventDefault();
      hideStatus(card);
      hideForm(card);
    });

    if (!form || readonly) {
      return;
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      hideStatus(card);

      const description = (form.querySelector('textarea[name="description"]')?.value || '').trim();
      const contactValue = (form.querySelector('input[name="contact_email"]')?.value || '').trim();
      const contact_email = contactValue || null;

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
          credentials: 'same-origin',
          cache: 'no-store',
          body: JSON.stringify({ description, contact_email }),
        });

        if (!response.ok) {
          throw new Error(`Request creation failed with status ${response.status}`);
        }

        await refreshVisibleLists();
        window.location.reload();
        return;
      } catch (error) {
        console.error(error);
        showStatus(card, 'Unable to post the request. Please try again.', 'error');
      } finally {
        submitButton?.removeAttribute('disabled');
      }
    });
  }

  function setupList(list) {
    const readonly = list.dataset.readonly === 'true';
    if (readonly) {
      return;
    }

    list.addEventListener('submit', async (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement) || !form.matches('[data-request-complete]')) {
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
          credentials: 'same-origin',
          cache: 'no-store',
        });

        if (!response.ok) {
          throw new Error(`Complete request failed with status ${response.status}`);
        }

        await refreshVisibleLists();
      } catch (error) {
        console.error(error);
        button?.removeAttribute('disabled');
        showGlobalMessage('Unable to mark the request complete.');
      }
    });
  }

  async function refreshVisibleLists() {
    const lists = document.querySelectorAll('[data-request-list][data-readonly="false"]');
    for (const list of lists) {
      try {
        const response = await fetch(API_BASE, {
          headers: { Accept: 'application/json' },
          credentials: 'same-origin',
          cache: 'no-store',
        });
        if (!response.ok) {
          throw new Error('Failed to refresh request list.');
        }
        const requests = await safeParseJson(response);
        if (Array.isArray(requests)) {
          renderRequests(list, requests);
        }
      } catch (error) {
        console.error(error);
        showGlobalMessage('Unable to refresh requests. Please reload.');
      }
    }
  }

  function renderRequests(list, requests) {
    if (!requests.length) {
      list.innerHTML = '<div class="card"><p class="muted">No requests yet. Be the first to share a need.</p></div>';
      return;
    }

    const items = requests
      .filter((entry) => !entry.is_pinned)
      .map(renderRequestItem)
      .join('');
    list.innerHTML = `<div class="requests-grid">${items}</div>`;
  }

  function renderRequestItem(item) {
    const requestUrl = `/requests/${item.id}`;
    const createdAt = formatDate(item.created_at);
    const completedAt = item.completed_at ? formatDate(item.completed_at) : null;
    const canComplete = Boolean(item.can_complete);
    const creatorSlug = item.created_by_username || '';
    const creatorName = escapeHtml(creatorSlug || 'Community member');
    const creatorHref = creatorSlug ? `/people/${encodeURIComponent(creatorSlug)}` : '';
    const creatorTitle = creatorSlug ? `View ${creatorSlug}'s profile` : 'Community member';
    const requestIcon = item.status === 'completed' ? '💫' : '✨';
    const requesterValue = creatorSlug ? `${requestIcon} @${creatorSlug}` : `${requestIcon} Community member`;

    const requesterChip = creatorSlug
      ? `<span class="meta-chip meta-chip--requester"><span class="meta-chip__label">Requester</span><a class="meta-chip__value meta-chip__value--link" href="${escapeHtml(
          creatorHref,
        )}" title="${escapeHtml(creatorTitle)}">${escapeHtml(requesterValue)}</a></span>`
      : `<span class="meta-chip meta-chip--requester"><span class="meta-chip__label">Requester</span><span class="meta-chip__value">${escapeHtml(
          requesterValue,
        )}</span></span>`;

    const statusChip = `<span class="meta-chip meta-chip--status"><span class="meta-chip__label">Status</span><span class="meta-chip__value">${capitalize(
      item.status,
    )}</span></span>`;

    const timestampChip = `<a class="meta-chip meta-chip--timestamp" href="${escapeHtml(requestUrl)}" title="View request details"><span class="meta-chip__label">Updated</span><time class="meta-chip__value" datetime="${escapeHtml(
      item.created_at,
    )}">${createdAt}</time></a>`;

    const actions = buildRequestActions(item, requestUrl, canComplete, canPinRequests());
    const actionMenu = renderActionMenu(actions, 'Request actions');
    const actionBlock = actionMenu ? `<div class="request-meta__actions">${actionMenu}</div>` : '';
    const pinBadge = item.is_pinned
      ? '<span class="meta-chip meta-chip--pinned"><span class="meta-chip__label">Pinned</span><span class="meta-chip__value">Priority</span></span>'
      : '';

    const statusSection = item.status === 'completed'
      ? `<span class="muted"${item.completed_at ? ` title="${escapeHtml(item.completed_at)}"` : ''}>Completed ${completedAt ?? 'recently'}</span>`
      : '';

    const contactSection = item.contact_email
      ? `<span class="muted">Contact: ${escapeHtml(item.contact_email)}</span>`
      : '';

    return `<article class="request-item">\n  <header class="request-meta">\n    <div class="request-meta__header">\n      <div class="request-meta__chips">\n        ${pinBadge}\n        ${requesterChip}\n        ${statusChip}\n        ${timestampChip}\n      </div>\n      ${actionBlock}\n    </div>\n  </header>\n  <div>\n    <p>${escapeHtml(item.description || 'No additional details.')}</p>\n  </div>\n  <footer class="actions">\n    ${statusSection}\n    ${contactSection}\n  </footer>\n</article>`;
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
    const card = document.querySelector('[data-request-card][data-readonly="false"]');
    if (card) {
      showStatus(card, message, 'error');
    }
  }

  function showCopyFeedback(message) {
    const card = document.querySelector('[data-request-card][data-readonly="false"]');
    if (card) {
      showStatus(card, message, 'info');
    }
  }

  async function safeParseJson(response) {
    try {
      return await response.clone().json();
    } catch (error) {
      console.error('Failed to parse response JSON', error);
      return null;
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

  function handleCopyLinkClick(event) {
    const target = event.target instanceof Element ? event.target.closest('[data-request-copy-link]') : null;
    if (!target) {
      return;
    }
    event.preventDefault();
    copyRequestLink(target);
  }

  async function copyRequestLink(target) {
    const relativeUrl = target.getAttribute('data-request-copy-link');
    if (!relativeUrl) {
      return;
    }
    const absoluteUrl = new URL(relativeUrl, window.location.origin).toString();
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(absoluteUrl);
      } else {
        fallbackCopy(absoluteUrl);
      }
      indicateCopySuccess(target);
    } catch (error) {
      try {
        fallbackCopy(absoluteUrl);
        indicateCopySuccess(target);
      } catch (fallbackError) {
        console.error('Unable to copy request link.', fallbackError);
        showGlobalMessage('Unable to copy link. Please copy manually.');
      }
    }
  }

  function fallbackCopy(value) {
    const textarea = document.createElement('textarea');
    textarea.value = value;
    textarea.setAttribute('readonly', 'true');
    textarea.style.position = 'absolute';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }

  function indicateCopySuccess(target) {
    target.setAttribute('data-copied', 'true');
    showCopyFeedback('Link copied to clipboard.');
    window.setTimeout(() => {
      target.removeAttribute('data-copied');
    }, 2000);
  }

  function canPinRequests() {
    const list = document.querySelector('[data-request-list]');
    return list?.dataset.canPin === 'true';
  }

  function buildRequestActions(item, requestUrl, canComplete, allowPinning) {
    const actions = [];
    if (item.status !== 'completed' && canComplete) {
      actions.push({
        type: 'form',
        label: 'Mark completed',
        href: `${requestUrl}/complete`,
        method: 'POST',
        formAttributes: {
          'data-request-complete': '',
          'data-request-id': item.id,
        },
      });
    }

    actions.push({
      type: 'button',
      label: 'Copy link',
      attributes: {
        'data-request-copy-link': requestUrl,
        'data-request-copy-label': `Request #${item.id}`,
      },
    });

    if (allowPinning) {
      const nextValue = window.location.pathname || '/';
      if (item.is_pinned) {
        actions.push({
          type: 'form',
          label: 'Unpin from main page',
          href: `${requestUrl}/unpin`,
          method: 'POST',
          hiddenFields: [
            { name: 'next', value: nextValue },
          ],
        });
        ['up', 'down'].forEach((direction) => {
          actions.push({
            type: 'form',
            label: `Move ${direction === 'up' ? 'up' : 'down'}`,
            href: `${requestUrl}/pin/reorder`,
            method: 'POST',
            hiddenFields: [
              { name: 'direction', value: direction },
              { name: 'next', value: nextValue },
            ],
          });
        });
      } else {
        actions.push({
          type: 'form',
          label: 'Pin to main page',
          href: `${requestUrl}/pin`,
          method: 'POST',
          hiddenFields: [
            { name: 'next', value: nextValue },
          ],
        });
      }
    }

    return actions;
  }

  function renderActionMenu(actions, triggerLabel) {
    if (!actions.length) {
      return '';
    }
    const label = escapeHtml(triggerLabel || 'Actions');
    const items = actions.map(renderActionMenuItem).join('');
    return `<div class="action-menu" data-action-menu>\n      <button type="button" class="action-menu__trigger" data-action-menu-trigger aria-haspopup="true" aria-expanded="false" aria-label="${label}">\n        <span class="action-menu__trigger-icon" aria-hidden="true">⋯</span>\n        <span class="sr-only">${label}</span>\n      </button>\n      <div class="action-menu__list" role="menu" data-action-menu-panel>\n        ${items}\n      </div>\n    </div>`;
  }

  function renderActionMenuItem(action) {
    const label = escapeHtml(action.label || 'Action');
    const icon = action.icon ? `<span class="action-menu__icon" aria-hidden="true">${escapeHtml(action.icon)}</span>` : '';
    if (action.type === 'form') {
      const method = escapeHtml(String(action.method || 'post').toLowerCase());
      const href = escapeHtml(action.href || '#');
      const formAttributes = renderAttributes(action.formAttributes);
      const buttonAttributes = renderAttributes(action.attributes);
      const hiddenFields = renderHiddenFields(action.hiddenFields);
      return `<form method="${method}" action="${href}" class="action-menu__form"${formAttributes}>\n        ${hiddenFields}\n        <button type="submit" class="action-menu__item" role="menuitem"${buttonAttributes}>${icon}<span class="action-menu__label">${label}</span></button>\n      </form>`;
    }
    if (action.type === 'link' || action.href) {
      const href = escapeHtml(action.href || '#');
      const targetAttr = action.target ? ` target="${escapeHtml(action.target)}"` : '';
      const relAttr = action.rel ? ` rel="${escapeHtml(action.rel)}"` : '';
      return `<a href="${href}" class="action-menu__item" role="menuitem"${targetAttr}${relAttr}${renderAttributes(action.attributes)}>${icon}<span class="action-menu__label">${label}</span></a>`;
    }
    return `<button type="button" class="action-menu__item" role="menuitem"${renderAttributes(action.attributes)}>${icon}<span class="action-menu__label">${label}</span></button>`;
  }

  function renderAttributes(attributes) {
    if (!attributes) {
      return '';
    }
    return Object.entries(attributes)
      .filter(([, value]) => value !== undefined && value !== null)
      .map(([key, value]) => ` ${key}="${escapeHtml(String(value))}"`)
      .join('');
  }

  function renderHiddenFields(fields) {
    if (!Array.isArray(fields) || !fields.length) {
      return '';
    }
    return fields
      .map((field) => {
        if (!field || !field.name) {
          return '';
        }
        const name = escapeHtml(String(field.name));
        const value = escapeHtml(String(field.value ?? ''));
        return `<input type="hidden" name="${name}" value="${value}" />`;
      })
      .join('');
  }
})();
