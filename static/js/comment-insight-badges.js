(function () {
  function init() {
    var badges = document.querySelectorAll('.comment-insight-badge');
    if (!badges.length) {
      return;
    }

    badges.forEach(function (badge) {
      badge.addEventListener('click', function (event) {
        event.preventDefault();
        var commentId = badge.getAttribute('data-comment-insight-id');
        if (!commentId) {
          return;
        }
        var container = document.getElementById('comment-insight-detail-' + commentId);
        if (!container) {
          return;
        }
        container.innerHTML = '<p class="text-muted">Loading insights…</p>';
        fetch('/api/admin/comment-insights/comments/' + commentId, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
          .then(function (response) {
            if (!response.ok) {
              throw new Error('Failed to load insights');
            }
            return response.json();
          })
          .then(function (data) {
            container.innerHTML = renderInsight(data);
          })
          .catch(function () {
            container.innerHTML = '<p class="text-danger">Unable to load insights.</p>';
          });
      });
    });
  }

  function renderInsight(data) {
    var parts = [];
    if (data.summary) {
      parts.push('<p><strong>Summary:</strong> ' + escapeHtml(data.summary) + '</p>');
    }
    var tags = [];
    (data.resource_tags || []).forEach(function (tag) {
      tags.push('<span class="meta-chip meta-chip--small">' + escapeHtml(tag) + '</span>');
    });
    (data.request_tags || []).forEach(function (tag) {
      tags.push('<span class="meta-chip meta-chip--small meta-chip--ghost">' + escapeHtml(tag) + '</span>');
    });
    if (tags.length) {
      parts.push('<div class="comment-insight-tags">' + tags.join(' ') + '</div>');
    }
    parts.push('<p class="small-text text-muted">Audience: ' + escapeHtml(data.audience || 'n/a') + '</p>');
    if (data.run_id) {
      parts.push(
        '<p><a class="small-text" target="_blank" href="/admin/comment-insights?run_id=' +
          encodeURIComponent(data.run_id) +
          '">Open in dashboard</a></p>'
      );
    }
    return '<div class="comment-insight-card">' + parts.join('') + '</div>';
  }

  function escapeHtml(value) {
    return (value || '').replace(/[&<>"']/g, function (ch) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      }[ch];
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
