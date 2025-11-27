(function () {
  function $(selector, context) {
    return (context || document).querySelector(selector);
  }

  function fetchHtml(url, options) {
    return fetch(url, options).then(function (response) {
      if (!response.ok) {
        throw new Error('Request failed: ' + response.status);
      }
      return response.text();
    });
  }

  function init() {
    var form = document.getElementById('comment-insights-filters');
    var runList = document.getElementById('comment-insights-run-list');
    var loadingIndicator = document.getElementById('runs-loading');
    if (!form || !runList) {
      return;
    }

    function setLoading(state) {
      if (!loadingIndicator) {
        return;
      }
      loadingIndicator.hidden = !state;
    }

    function loadRuns(url) {
      setLoading(true);
      fetchHtml(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (html) {
          runList.innerHTML = html;
        })
        .catch(function (err) {
          console.error('Failed to load runs', err);
          runList.innerHTML = '<p class="text-danger">Failed to load runs.</p>';
        })
        .finally(function () {
          setLoading(false);
        });
    }

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var formData = new FormData(form);
      var params = new URLSearchParams(formData);
      var url = '/admin/comment-insights/runs?' + params.toString();
      loadRuns(url);
    });

    runList.addEventListener('click', function (event) {
      var button = event.target.closest('[data-run-detail]');
      if (!button) {
        return;
      }
      event.preventDefault();
      var runId = button.getAttribute('data-run-detail');
      var targetId = button.getAttribute('data-target');
      if (!runId || !targetId) {
        return;
      }
      var target = document.getElementById(targetId);
      if (!target) {
        return;
      }
      target.innerHTML = '<p>Loading…</p>';
      var detailUrl = '/admin/comment-insights/runs/' + encodeURIComponent(runId) + '/analyses';
      fetchHtml(detailUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (html) {
          target.innerHTML = html;
        })
        .catch(function () {
          target.innerHTML = '<p class="text-danger">Failed to load analyses.</p>';
        });
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
