(function () {
  var toggle = document.querySelector('[data-nav-mobile-toggle]');
  var panel = document.querySelector('[data-nav-mobile-panel]');
  var navLinks = document.querySelector('[data-nav-links]');
  var navInlineActions = document.querySelector('[data-nav-inline-actions]');
  var accountSlot = document.querySelector('[data-nav-mobile-account]');
  var themeSlot = document.querySelector('[data-nav-mobile-theme]');
  var navRoot = toggle ? toggle.closest('.top-nav') : null;
  var navContainer = navRoot ? navRoot.querySelector('.container') : null;
  var navActions = navRoot ? navRoot.querySelector('.nav-actions') : null;
  var media = window.matchMedia('(max-width: 768px)');

  if (!toggle || !panel || !navLinks || !accountSlot || !navContainer || !navActions) {
    return;
  }

  var originalLinksParent = navLinks.parentNode;
  var originalLinksNext = navLinks.nextSibling;
  var originalActionsParent = navInlineActions ? navInlineActions.parentNode : null;
  var originalActionsNext = navInlineActions ? navInlineActions.nextSibling : null;

  var isMobile = false;

  var closePanel = function () {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.classList.remove('is-active');
  };

  var openPanel = function () {
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    toggle.classList.add('is-active');
  };

  var handleOutsideClick = function (event) {
    if (!panel.hidden && !panel.contains(event.target) && !toggle.contains(event.target)) {
      closePanel();
    }
  };

  var handleEscape = function (event) {
    if (event.key === 'Escape' && !panel.hidden) {
      closePanel();
      toggle.focus();
    }
  };

  document.addEventListener('click', handleOutsideClick);
  document.addEventListener('keydown', handleEscape);

  toggle.addEventListener('click', function () {
    if (panel.hidden) {
      openPanel();
    } else {
      closePanel();
    }
  });

  var activateMobile = function () {
    if (isMobile) {
      return;
    }
    isMobile = true;
    toggle.hidden = false;
    toggle.setAttribute('aria-expanded', 'false');
    closePanel();

    accountSlot.appendChild(navLinks);
    if (themeSlot) {
      if (navInlineActions) {
        themeSlot.appendChild(navInlineActions);
      } else {
        themeSlot.textContent = '';
      }
    }
  };

  var activateDesktop = function () {
    if (!isMobile) {
      return;
    }
    isMobile = false;
    closePanel();
    toggle.hidden = true;

    if (originalLinksParent) {
      if (originalLinksNext) {
        originalLinksParent.insertBefore(navLinks, originalLinksNext);
      } else {
        originalLinksParent.appendChild(navLinks);
      }
    } else {
      navContainer.insertBefore(navLinks, navActions);
    }

    if (navInlineActions && originalActionsParent) {
      if (originalActionsNext) {
        originalActionsParent.insertBefore(navInlineActions, originalActionsNext);
      } else {
        originalActionsParent.appendChild(navInlineActions);
      }
    } else if (navInlineActions) {
      navActions.appendChild(navInlineActions);
    }
  };

  var evaluate = function (event) {
    if (event.matches) {
      activateMobile();
    } else {
      activateDesktop();
    }
  };

  evaluate(media);

  if (media.addEventListener) {
    media.addEventListener('change', evaluate);
  } else if (media.addListener) {
    media.addListener(evaluate);
  }
})();
