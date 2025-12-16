(() => {
  async function dismissCaption(captionId, button) {
    const container = button.closest('[data-caption-id]');
    button.disabled = true;
    try {
      const response = await fetch(`/api/captions/${encodeURIComponent(captionId)}/dismiss`, {
        method: 'POST',
        headers: { 'X-Requested-With': 'Fetch' },
        credentials: 'same-origin',
      });
      if (!response.ok) {
        throw new Error('Dismiss failed');
      }
      if (container) {
        container.remove();
      }
    } catch (error) {
      console.error('Failed to dismiss caption', error);
      button.disabled = false;
    }
  }

  document.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target.closest('[data-caption-dismiss]') : null;
    if (!target) {
      return;
    }
    event.preventDefault();
    const captionId = target.getAttribute('data-caption-dismiss');
    if (!captionId) {
      return;
    }
    dismissCaption(captionId, target);
  });
})();
