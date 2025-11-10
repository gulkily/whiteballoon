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
})();
