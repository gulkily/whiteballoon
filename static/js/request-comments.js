
(function () {
  const form = document.querySelector('[data-comment-form]');
  if (!form) return;

  const list = document.querySelector('[data-comment-list]');
  const errorsBox = form.querySelector('[data-comment-errors]');
  const bodyField = form.querySelector('[data-comment-body]');
  const submitButton = form.querySelector('[data-comment-submit]');

  const showErrors = (messages) => {
    if (!errorsBox) return;
    if (!messages || !messages.length) {
      errorsBox.setAttribute('hidden', 'hidden');
      errorsBox.innerHTML = '';
      return;
    }
    const items = messages.map((msg) => `<li>${msg}</li>`).join('');
    errorsBox.innerHTML = `<ul class="stack">${items}</ul>`;
    errorsBox.removeAttribute('hidden');
  };

  const appendComment = (html) => {
    if (!list) return;
    list.removeAttribute('hidden');
    list.insertAdjacentHTML('beforeend', html);
    const last = list.lastElementChild;
    if (last) {
      last.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!window.fetch || !list) {
      form.submit();
      return;
    }

    showErrors([]);
    submitButton?.setAttribute('disabled', 'disabled');

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'Fetch', Accept: 'application/json' },
        body: new FormData(form),
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        showErrors(payload.errors || ['Something went wrong.']);
        return;
      }

      appendComment(payload.html);
      if (bodyField) bodyField.value = '';
    } catch (error) {
      form.submit();
    } finally {
      submitButton?.removeAttribute('disabled');
    }
  });

  const commentSection = document.querySelector('[data-comment-section]');
  if (!commentSection) return;

  commentSection.addEventListener('submit', async (event) => {
    const target = event.target;
    if (!window.fetch) {
      return;
    }

    if (target.matches('[data-comment-delete-form]')) {
      event.preventDefault();
      const commentEl = target.closest('[data-comment-id]');
      const deleteButton = target.querySelector('[data-comment-delete]');
      deleteButton?.setAttribute('disabled', 'disabled');

      try {
        const response = await fetch(target.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'Fetch', Accept: 'application/json' },
        });

        if (!response.ok) {
          target.submit();
          return;
        }

        commentEl?.remove();
        if (list && !list.children.length) {
          list.setAttribute('hidden', 'hidden');
        }
      } catch (error) {
        target.submit();
      } finally {
        deleteButton?.removeAttribute('disabled');
      }
      return;
    }

    if (target.matches('[data-comment-scope-form]')) {
      event.preventDefault();
      const commentEl = target.closest('[data-comment-id]');
      const scopeChip = commentEl?.querySelector('.request-comment__scope');
      const scopeInput = target.querySelector('input[name="scope"]');
      const button = target.querySelector('button');
      button?.setAttribute('disabled', 'disabled');

      try {
        const response = await fetch(target.action, {
          method: 'POST',
          headers: { 'X-Requested-With': 'Fetch', Accept: 'application/json' },
          body: new FormData(target),
        });

        if (!response.ok) {
          target.submit();
          return;
        }

        const payload = await response.json().catch(() => ({}));
        const nextScope = (payload.scope || '').toLowerCase();
        const fallbackScope = (scopeInput?.value || '').toLowerCase() === 'public' ? 'private' : 'public';
        const scope = nextScope || fallbackScope;
        const isPublic = scope === 'public';
        if (scopeChip) {
          scopeChip.textContent = isPublic ? 'Public' : 'Private';
        }
        if (button) {
          button.textContent = isPublic ? 'Make private' : 'Share';
        }
        if (scopeInput) {
          scopeInput.value = isPublic ? 'private' : 'public';
        }
      } catch (error) {
        target.submit();
      } finally {
        button?.removeAttribute('disabled');
      }
    }
  });
})();
