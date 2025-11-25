(function () {
  if (!window.fetch) {
    return;
  }

  const forms = document.querySelectorAll('[data-sync-toggle]');
  forms.forEach((form) => {
    const button = form.querySelector('[data-sync-button]');
    const scopeInput = form.querySelector('input[name="scope"]');
    if (!button || !scopeInput) {
      return;
    }

    const labelEl = form.querySelector('[data-scope-label]');
    const hintEl = form.querySelector('[data-scope-hint]');

    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      button.disabled = true;
      button.dataset.loading = 'true';

      try {
        const response = await fetch(form.action, {
          method: form.method || 'POST',
          headers: { Accept: 'application/json' },
          body: new FormData(form),
        });

        if (!response.ok) {
          throw new Error(`Scope update failed (${response.status})`);
        }

        const payload = await response.json().catch(() => ({}));
        const nextScope = typeof payload.scope === 'string' ? payload.scope.toLowerCase() : '';
        const scope = nextScope || (scopeInput.value || '').toLowerCase();
        const isPublic = scope === 'public';

        button.classList.toggle('meta-chip--success', isPublic);
        button.classList.toggle('meta-chip--muted', !isPublic);
        button.setAttribute('aria-pressed', isPublic ? 'true' : 'false');
        if (labelEl) {
          labelEl.textContent = isPublic ? 'Public' : 'Private';
        }
        if (hintEl) {
          hintEl.textContent = isPublic
            ? 'Tap to keep private'
            : 'Tap to share publicly';
        }
        scopeInput.value = isPublic ? 'private' : 'public';
      } catch (error) {
        console.error('Sync scope toggle failed', error);
        form.submit();
      } finally {
        button.disabled = false;
        delete button.dataset.loading;
      }
    });
  });
})();
