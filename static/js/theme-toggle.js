(function () {
  var storageKey = 'wb-theme';
  var mediaQuery = '(prefers-color-scheme: dark)';
  var toggle = document.querySelector('[data-theme-toggle]');
  if (!toggle) {
    return;
  }

  var label = toggle.querySelector('[data-theme-toggle-label]');
  var modes = ['auto', 'light', 'dark'];
  var media = null;

  function safeGetStored() {
    try {
      var value = localStorage.getItem(storageKey);
      if (value === 'light' || value === 'dark' || value === 'auto') {
        return value;
      }
      return 'auto';
    } catch (err) {
      return 'auto';
    }
  }

  function safeSetStored(value) {
    try {
      localStorage.setItem(storageKey, value);
    } catch (err) {
      /* no-op */
    }
  }

  function prefersDark() {
    if (!window.matchMedia) {
      return false;
    }
    return window.matchMedia(mediaQuery).matches;
  }

  function resolve(mode) {
    if (mode === 'dark') {
      return 'dark';
    }
    if (mode === 'light') {
      return 'light';
    }
    return prefersDark() ? 'dark' : 'light';
  }

  function labelFor(mode) {
    if (mode === 'dark') {
      return 'Dark';
    }
    if (mode === 'light') {
      return 'Light';
    }
    return 'Auto';
  }

  function apply(mode, persist) {
    var resolved = resolve(mode);
    document.documentElement.setAttribute('data-theme', resolved);
    document.documentElement.setAttribute('data-theme-preference', mode);
    toggle.setAttribute('data-theme-mode', mode);
    toggle.setAttribute('aria-label', 'Theme mode: ' + labelFor(mode));
    if (label) {
      label.textContent = labelFor(mode);
    }
    if (persist) {
      safeSetStored(mode);
    }
  }

  function handleSystemChange() {
    if (currentMode === 'auto') {
      apply('auto', false);
    }
  }

  var currentMode = safeGetStored();
  apply(currentMode, false);

  if (window.matchMedia) {
    media = window.matchMedia(mediaQuery);
    if (media.addEventListener) {
      media.addEventListener('change', handleSystemChange);
    } else if (media.addListener) {
      media.addListener(handleSystemChange);
    }
  }

  toggle.addEventListener('click', function () {
    var index = modes.indexOf(currentMode);
    var next = modes[(index + 1) % modes.length];
    currentMode = next;
    apply(currentMode, true);
  });
})();
