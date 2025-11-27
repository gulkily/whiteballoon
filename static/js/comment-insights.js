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
    var params = new URLSearchParams(window.location.search);
    var runToOpen = params.get('run_id');
    if (!form || !runList) {
      return;
    }

    function setLoading(state) {
      if (!loadingIndicator) {
        return;
      }
      loadingIndicator.hidden = !state;
    }

    function loadRuns(url, opts) {
      setLoading(true);
      fetchHtml(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (html) {
          runList.innerHTML = html;
          if (opts && opts.runToOpen) {
            openRunDetail(opts.runToOpen);
          }
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
      loadRuns(url, { runToOpen: runToOpen });
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
      loadRunDetail(runId, target);
    });

    function loadRunDetail(runId, target) {
      target.innerHTML = '<p>Loading…</p>';
      var detailUrl = '/admin/comment-insights/runs/' + encodeURIComponent(runId) + '/analyses';
      fetchHtml(detailUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (html) {
          target.innerHTML = html;
        })
        .catch(function () {
          target.innerHTML = '<p class="text-danger">Failed to load analyses.</p>';
        });
    }

    function openRunDetail(runId) {
      if (!runId) {
        return;
      }
      var button = runList.querySelector('[data-run-detail="' + runId + '"]');
      var targetId = button && button.getAttribute('data-target');
      var target = targetId && document.getElementById(targetId);
      if (button && target) {
        loadRunDetail(runId, target);
      }
    }

    if (runToOpen) {
      openRunDetail(runToOpen);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
