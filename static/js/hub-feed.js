(function () {
  const listEl = document.querySelector('[data-feed-list]');
  const loadBtn = document.querySelector('[data-feed-load]');
  if (!listEl || !loadBtn) {
    return;
  }

  const pageSize = Number(loadBtn.dataset.pageSize || 20);

  loadBtn.addEventListener('click', async () => {
    const nextOffset = Number(loadBtn.dataset.nextOffset);
    if (Number.isNaN(nextOffset)) {
      loadBtn.remove();
      return;
    }
    loadBtn.disabled = true;
    loadBtn.textContent = 'Loading…';
    try {
      const resp = await fetch(`/api/v1/feed/?offset=${nextOffset}&limit=${pageSize}`);
      if (!resp.ok) {
        throw new Error('Failed to load feed');
      }
      const payload = await resp.json();
      payload.items.forEach((item) => {
        listEl.appendChild(renderCard(item));
      });
      if (payload.next_offset !== null && payload.next_offset !== undefined) {
        loadBtn.dataset.nextOffset = payload.next_offset;
        loadBtn.disabled = false;
        loadBtn.textContent = 'Load more';
      } else {
        loadBtn.remove();
      }
    } catch (err) {
      loadBtn.disabled = false;
      loadBtn.textContent = 'Load more';
      console.error(err);
    }
  });

  function renderCard(item) {
    const article = document.createElement('article');
    article.className = 'feed-card';
    article.dataset.requestId = item.id;

    const header = document.createElement('header');
    header.className = 'feed-card__meta';

    const status = document.createElement('span');
    status.className = `status status--${item.status}`;
    status.textContent = capitalize(item.status || 'open');
    header.appendChild(status);

    const source = document.createElement('span');
    source.className = 'meta-pill';
    source.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7"></circle></svg>';
    source.appendChild(document.createTextNode(` ${item.source_instance} · #${item.source_request_id}`));
    header.appendChild(source);

    const updated = document.createElement('span');
    updated.className = 'meta-pill';
    updated.textContent = `Updated ${formatDate(item.updated_at)}`;
    header.appendChild(updated);

    article.appendChild(header);

    const body = document.createElement('div');
    body.className = 'feed-card__body';
    const title = document.createElement('h2');
    title.textContent = item.title || 'Untitled request';
    const desc = document.createElement('p');
    desc.textContent = item.description || '';
    body.appendChild(title);
    body.appendChild(desc);
    article.appendChild(body);

    const details = document.createElement('dl');
    details.className = 'feed-card__details';
    details.appendChild(detailBlock('Creator', item.created_by_username || (item.created_by_id ? `User #${item.created_by_id}` : 'Unknown')));
    details.appendChild(detailBlock('Peer', item.peer_name));
    details.appendChild(detailBlock('Comments', String(item.comment_count || 0)));
    article.appendChild(details);

    if (item.comment_count > 0 && Array.isArray(item.comments) && item.comments.length) {
      const commentsSection = document.createElement('section');
      commentsSection.className = 'feed-card__comments';
      const heading = document.createElement('h3');
      heading.textContent = 'Recent comments';
      commentsSection.appendChild(heading);
      const list = document.createElement('ul');
      item.comments.forEach((comment) => {
        list.appendChild(renderComment(comment));
      });
      commentsSection.appendChild(list);
      article.appendChild(commentsSection);
    }

    return article;
  }

  function detailBlock(label, value) {
    const wrapper = document.createElement('div');
    const dt = document.createElement('dt');
    dt.textContent = label;
    const dd = document.createElement('dd');
    dd.textContent = value || '';
    wrapper.appendChild(dt);
    wrapper.appendChild(dd);
    return wrapper;
  }

  function renderComment(comment) {
    const item = document.createElement('li');
    const meta = document.createElement('div');
    meta.className = 'comment-meta';
    const author = document.createElement('span');
    author.textContent = comment.username || 'Member';
    const timestamp = document.createElement('span');
    timestamp.textContent = formatDate(comment.created_at);
    meta.appendChild(author);
    meta.appendChild(timestamp);
    item.appendChild(meta);
    const body = document.createElement('p');
    body.textContent = comment.body || '';
    item.appendChild(body);
    return item;
  }

  function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  }

  function capitalize(value) {
    if (!value) return '';
    return value.charAt(0).toUpperCase() + value.slice(1);
  }
})();
