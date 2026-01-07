(() => {
  const API_BASE = '/api/requests';
  const DRAFTS_API = `${API_BASE}/drafts`;
  let draftCache = new Map();

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-request-card]').forEach((card) => setupForm(card));
    document.querySelectorAll('[data-request-list]').forEach((list) => setupList(list));
    const draftsPanel = document.querySelector('[data-request-drafts]');
    if (draftsPanel) {
      setupDrafts(draftsPanel);
    }
  });
  document.addEventListener('click', handleCopyLinkClick);

  function setupForm(card) {
    const form = card.querySelector('[data-request-form]');
    const collapsed = card.querySelector('[data-request-collapsed]');
    const showButton = collapsed?.querySelector('[data-request-action="show-form"]');
    const cancelButton = form?.querySelector('[data-request-action="cancel-form"]');
    const saveDraftButton = form?.querySelector('[data-request-action="save-draft"]');
    const resetDraftButton = form?.querySelector('[data-request-action="reset-draft"]');
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
      const draftId = getDraftId(form);

      if (!description) {
        showStatus(card, 'Description is required.', 'error');
        return;
      }

      const submitButton = form.querySelector('button[type="submit"]');
      submitButton?.setAttribute('disabled', 'true');
      showStatus(card, draftId ? 'Publishing draft…' : 'Posting request…', 'info');

      try {
        if (draftId) {
          await publishDraftRequest({ draftId, description, contact_email, card, reload: true });
        } else {
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
        }

        await refreshVisibleLists();
        await refreshDrafts();
        clearDraftForm(form);
        window.location.reload();
        return;
      } catch (error) {
        console.error(error);
        showStatus(card, 'Unable to post the request. Please try again.', 'error');
      } finally {
        submitButton?.removeAttribute('disabled');
      }
    });

    saveDraftButton?.addEventListener('click', async (event) => {
      event.preventDefault();
      const description = (form.querySelector('textarea[name="description"]')?.value || '').trim();
      const contactValue = (form.querySelector('input[name="contact_email"]')?.value || '').trim();
      if (!description) {
        showStatus(card, 'Add some details before saving the draft.', 'error');
        return;
      }
      const draftId = getDraftId(form);
      toggleDraftButtons(form, true);
      showStatus(card, draftId ? 'Updating draft…' : 'Saving draft…', 'info');
      try {
        const response = await fetch(DRAFTS_API, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          credentials: 'same-origin',
          cache: 'no-store',
          body: JSON.stringify({
            id: draftId ? Number(draftId) : null,
            description,
            contact_email: contactValue || null,
          }),
        });
        if (!response.ok) {
          throw new Error(`Draft save failed with status ${response.status}`);
        }
        const draft = await safeParseJson(response);
        if (draft?.id) {
          setDraftId(form, draft.id);
          showDraftIndicator(form, draft.id);
        }
        showStatus(card, 'Draft saved.', 'success');
        await refreshDrafts();
      } catch (error) {
        console.error(error);
        showStatus(card, 'Unable to save the draft. Please try again.', 'error');
      } finally {
        toggleDraftButtons(form, false);
      }
    });

    resetDraftButton?.addEventListener('click', (event) => {
      event.preventDefault();
      clearDraftForm(form);
      showStatus(card, 'Draft cleared.', 'info');
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

  async function refreshDrafts() {
    const panel = document.querySelector('[data-request-drafts]');
    if (!panel) {
      return;
    }
    try {
      const response = await fetch(DRAFTS_API, {
        headers: { Accept: 'application/json' },
        credentials: 'same-origin',
        cache: 'no-store',
      });
      if (!response.ok) {
        throw new Error('Failed to refresh drafts.');
      }
      const drafts = await safeParseJson(response);
      if (Array.isArray(drafts)) {
        updateDraftCache(drafts);
        renderDrafts(panel, drafts);
      }
    } catch (error) {
      console.error(error);
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
    const statusDisplay = item.status === 'completed'
      ? 'Archived'
      : item.status === 'draft'
        ? 'Draft'
        : 'Active';
    const statusChipClass = item.status === 'completed'
      ? 'meta-chip meta-chip--status meta-chip--muted'
      : item.status === 'draft'
        ? 'meta-chip meta-chip--status meta-chip--muted'
        : 'meta-chip meta-chip--status meta-chip--success';
    const statusChip = `<span class="${statusChipClass}" aria-label="Status"><span class="meta-chip__value">${statusDisplay}</span></span>`;

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

  function showDraftIndicator(form, draftId) {
    const indicator = form.querySelector('[data-request-draft-indicator]');
    const label = form.querySelector('[data-request-draft-label]');
    if (!indicator || !label) {
      return;
    }
    indicator.hidden = false;
    label.textContent = `#${draftId}`;
  }

  function hideDraftIndicator(form) {
    const indicator = form.querySelector('[data-request-draft-indicator]');
    const label = form.querySelector('[data-request-draft-label]');
    if (!indicator || !label) {
      return;
    }
    indicator.hidden = true;
    label.textContent = '';
  }

  function setDraftId(form, draftId) {
    const input = form.querySelector('[data-request-draft-id]');
    if (input) {
      input.value = draftId ? String(draftId) : '';
    }
  }

  function getDraftId(form) {
    const input = form.querySelector('[data-request-draft-id]');
    if (!input || !input.value) {
      return null;
    }
    return input.value;
  }

  function clearDraftForm(form) {
    if (!form) {
      return;
    }
    const descriptionField = form.querySelector('textarea[name="description"]');
    if (descriptionField) {
      descriptionField.value = '';
    }
    const contactField = form.querySelector('input[name="contact_email"]');
    if (contactField) {
      contactField.value = contactField.defaultValue ?? '';
    }
    setDraftId(form, null);
    hideDraftIndicator(form);
  }

  function toggleDraftButtons(form, disabled) {
    const draftButtons = form.querySelectorAll('[data-request-action="save-draft"], [data-request-action="reset-draft"]');
    draftButtons.forEach((button) => {
      if (disabled) {
        button.setAttribute('disabled', 'true');
      } else {
        button.removeAttribute('disabled');
      }
    });
  }

  function setupDrafts(panel) {
    bootstrapDraftCache(panel);
    setDraftPanelVisibility(panel, draftCache.size > 0);
    panel.addEventListener('click', async (event) => {
      const trigger = event.target instanceof Element ? event.target.closest('[data-draft-action]') : null;
      if (!trigger) {
        return;
      }
      event.preventDefault();
      const draftId = Number(trigger.getAttribute('data-draft-id'));
      if (!draftId) {
        return;
      }
      const action = trigger.getAttribute('data-draft-action');
      if (action === 'edit') {
        applyDraftToForm(draftId, trigger);
        return;
      }
      if (action === 'publish') {
        await publishDraftRequest({ draftId, sourceButton: trigger });
        return;
      }
      if (action === 'delete') {
        await deleteDraft(draftId, trigger);
      }
    });
  }

  function bootstrapDraftCache(panel) {
    const nextCache = new Map();
    panel.querySelectorAll('[data-request-draft]').forEach((element) => {
      const draftId = Number(element.getAttribute('data-draft-id'));
      if (!draftId) {
        return;
      }
      nextCache.set(draftId, {
        id: draftId,
        description: element.getAttribute('data-draft-description') || '',
        contact_email: element.getAttribute('data-draft-contact') || '',
        updated_at: element.querySelector('time')?.getAttribute('datetime') || null,
      });
    });
    draftCache = nextCache;
  }

  function updateDraftCache(drafts) {
    draftCache = new Map();
    drafts.forEach((draft) => {
      if (!draft || typeof draft.id !== 'number') {
        return;
      }
      draftCache.set(draft.id, draft);
    });
  }

  function renderDrafts(panel, drafts) {
    const list = panel.querySelector('[data-request-draft-list]');
    const countLabel = panel.querySelector('[data-request-draft-count]');
    if (!list) {
      return;
    }
    const hasDrafts = drafts.length > 0;
    setDraftPanelVisibility(panel, hasDrafts);
    if (countLabel) {
      countLabel.textContent = `${drafts.length} in progress`;
    }
    if (!hasDrafts) {
      list.innerHTML = '';
      return;
    }
    const items = drafts.map(renderDraftCard).join('');
    list.innerHTML = items;
  }

  function setDraftPanelVisibility(panel, hasDrafts) {
    if (!panel) {
      return;
    }
    panel.hidden = !hasDrafts;
    panel.style.display = hasDrafts ? '' : 'none';
    panel.dataset.hasDrafts = hasDrafts ? 'true' : 'false';
    const empty = panel.querySelector('[data-request-draft-empty]');
    if (empty) {
      empty.hidden = hasDrafts;
    }
  }

  function renderDraftCard(draft) {
    const description = draft.description || '';
    const contact = draft.contact_email || '';
    const updatedAt = draft.updated_at ? formatDate(draft.updated_at) : '';
    const safeSummary = description ? escapeHtml(description) : 'No additional details yet.';
    const contactLine = contact ? `<span class="muted">Contact: ${escapeHtml(contact)}</span>` : '';
    const templateChip = draft.recurring_template_title
      ? `<span class="meta-chip"><span class="meta-chip__label">Template</span><span class="meta-chip__value">${escapeHtml(draft.recurring_template_title)}</span></span>`
      : '';
    return `<article class="request-draft" data-request-draft data-draft-id="${escapeHtml(String(draft.id))}" data-draft-description="${escapeHtml(description)}" data-draft-contact="${escapeHtml(contact)}">\n      <header class="request-draft__meta">\n        <span class="meta-chip meta-chip--status meta-chip--muted"><span class="meta-chip__label">Status</span><span class="meta-chip__value">Draft</span></span>\n        ${templateChip}\n        <time class="meta-chip meta-chip--timestamp" datetime="${escapeHtml(draft.updated_at || '')}">\n          <span class="meta-chip__label">Updated</span>\n          <span class="meta-chip__value">${escapeHtml(updatedAt)}</span>\n        </time>\n      </header>\n      <p class="request-draft__summary">${safeSummary}</p>\n      <div class="actions">\n        ${contactLine}\n        <div>\n          <button type="button" class="button button--ghost" data-draft-action="edit" data-draft-id="${escapeHtml(String(draft.id))}">Edit</button>\n          <button type="button" class="button" data-draft-action="publish" data-draft-id="${escapeHtml(String(draft.id))}">Publish</button>\n          <button type="button" class="button button--ghost" data-draft-action="delete" data-draft-id="${escapeHtml(String(draft.id))}">Delete</button>\n        </div>\n      </div>\n    </article>`;
  }

  function applyDraftToForm(draftId, sourceElement) {
    const form = document.querySelector('[data-request-form]');
    const card = document.querySelector('[data-request-card]');
    if (!form || !card) {
      return;
    }
    const draft = resolveDraftData(draftId, sourceElement);
    if (!draft) {
      showStatus(card, 'Unable to load that draft.', 'error');
      return;
    }
    const descriptionField = form.querySelector('textarea[name="description"]');
    const contactField = form.querySelector('input[name="contact_email"]');
    if (descriptionField) {
      descriptionField.value = draft.description || '';
    }
    if (contactField && draft.contact_email !== undefined) {
      contactField.value = draft.contact_email || '';
    }
    setDraftId(form, draftId);
    showDraftIndicator(form, draftId);
    hideStatus(card);
    showForm(card);
  }

  function resolveDraftData(draftId, sourceElement) {
    if (draftCache.has(draftId)) {
      return draftCache.get(draftId);
    }
    const element = sourceElement?.closest('[data-request-draft]');
    if (!element) {
      return null;
    }
    return {
      id: draftId,
      description: element.getAttribute('data-draft-description') || '',
      contact_email: element.getAttribute('data-draft-contact') || '',
      updated_at: element.querySelector('time')?.getAttribute('datetime') || null,
    };
  }

  async function publishDraftRequest({ draftId, description, contact_email, card, sourceButton, reload = false }) {
    const target = sourceButton || card?.querySelector('button[type="submit"]');
    target?.setAttribute('disabled', 'true');
    try {
      const response = await fetch(`${API_BASE}/${draftId}/publish`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        credentials: 'same-origin',
        cache: 'no-store',
        body: JSON.stringify({
          description: description ?? null,
          contact_email: contact_email ?? null,
        }),
      });
      if (!response.ok) {
        throw new Error(`Publish failed with status ${response.status}`);
      }
      await refreshDrafts();
      await refreshVisibleLists();
      const form = document.querySelector('[data-request-form]');
      if (form && getDraftId(form) === String(draftId)) {
        clearDraftForm(form);
      }
      if (reload) {
        window.location.reload();
      } else {
        const cardRef = document.querySelector('[data-request-card]');
        if (cardRef) {
          showStatus(cardRef, 'Draft published.', 'success');
        }
      }
    } catch (error) {
      console.error(error);
      if (card) {
        showStatus(card, 'Unable to publish the draft.', 'error');
      } else {
        showGlobalMessage('Unable to publish the draft.');
      }
    } finally {
      target?.removeAttribute('disabled');
    }
  }

  async function deleteDraft(draftId, trigger) {
    trigger?.setAttribute('disabled', 'true');
    try {
      const response = await fetch(`${API_BASE}/${draftId}`, {
        method: 'DELETE',
        headers: {
          Accept: 'application/json',
        },
        credentials: 'same-origin',
        cache: 'no-store',
      });
      if (!response.ok && response.status !== 204) {
        throw new Error(`Delete failed with status ${response.status}`);
      }
      await refreshDrafts();
      const form = document.querySelector('[data-request-form]');
      if (form && getDraftId(form) === String(draftId)) {
        clearDraftForm(form);
      }
    } catch (error) {
      console.error(error);
      showGlobalMessage('Unable to delete the draft.');
    } finally {
      trigger?.removeAttribute('disabled');
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
    if (typeof window.formatFriendlyTime === 'function') {
      const friendly = window.formatFriendlyTime(value);
      if (friendly) {
        return friendly;
      }
    }
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
