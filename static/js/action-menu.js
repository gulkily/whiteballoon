(function () {
  const MENU_SELECTOR = '[data-action-menu]';
  const PANEL_SELECTOR = '[data-action-menu-panel]';
  const TRIGGER_SELECTOR = '[data-action-menu-trigger]';
  const ITEM_SELECTOR = '[role="menuitem"]';
  const registry = new WeakMap();
  let openMenu = null;
  let documentPointerHandler = null;
  let documentKeyHandler = null;

  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn, { once: true });
    } else {
      fn();
    }
  }

  function collectItems(menu) {
    const info = registry.get(menu);
    if (!info) {
      return [];
    }
    return Array.from(info.panel.querySelectorAll(ITEM_SELECTOR)).filter((node) => !node.hasAttribute('disabled'));
  }

  function focusItem(menu, index) {
    const items = collectItems(menu);
    if (!items.length) {
      return;
    }
    const target = items[(index + items.length) % items.length];
    window.requestAnimationFrame(() => target.focus());
  }

  function closeMenu(menu, { restoreFocus } = { restoreFocus: false }) {
    const info = menu ? registry.get(menu) : null;
    if (!info) {
      return;
    }
    menu.classList.remove('action-menu--open');
    info.trigger.setAttribute('aria-expanded', 'false');
    if (restoreFocus) {
      info.trigger.focus();
    }
    if (openMenu === menu) {
      openMenu = null;
    }
    if (!openMenu) {
      teardownDocumentListeners();
    }
  }

  function openMenuFor(menu) {
    if (openMenu && openMenu !== menu) {
      closeMenu(openMenu);
    }
    const info = registry.get(menu);
    if (!info) {
      return;
    }
    menu.classList.add('action-menu--open');
    info.trigger.setAttribute('aria-expanded', 'true');
    openMenu = menu;
    setupDocumentListeners();
    focusItem(menu, 0);
  }

  function toggleMenu(menu) {
    if (openMenu === menu) {
      closeMenu(menu, { restoreFocus: true });
    } else {
      openMenuFor(menu);
    }
  }

  function handleTriggerKeydown(menu, event) {
    if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openMenuFor(menu);
    }
  }

  function handleMenuKeydown(menu, event) {
    const items = collectItems(menu);
    if (!items.length) {
      return;
    }
    const currentIndex = items.indexOf(document.activeElement);
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % items.length;
      focusItem(menu, nextIndex);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      const prevIndex = currentIndex === -1 ? items.length - 1 : (currentIndex - 1 + items.length) % items.length;
      focusItem(menu, prevIndex);
    } else if (event.key === 'Home') {
      event.preventDefault();
      focusItem(menu, 0);
    } else if (event.key === 'End') {
      event.preventDefault();
      focusItem(menu, items.length - 1);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      closeMenu(menu, { restoreFocus: true });
    }
  }

  function handleDocumentPointer(event) {
    if (!openMenu) {
      return;
    }
    if (openMenu.contains(event.target)) {
      return;
    }
    closeMenu(openMenu);
  }

  function handleDocumentKeydown(event) {
    if (event.key === 'Escape' && openMenu) {
      event.preventDefault();
      closeMenu(openMenu, { restoreFocus: true });
    }
  }

  function setupDocumentListeners() {
    if (!documentPointerHandler) {
      documentPointerHandler = handleDocumentPointer;
      document.addEventListener('pointerdown', documentPointerHandler, { capture: true });
    }
    if (!documentKeyHandler) {
      documentKeyHandler = handleDocumentKeydown;
      document.addEventListener('keydown', documentKeyHandler);
    }
  }

  function teardownDocumentListeners() {
    if (documentPointerHandler) {
      document.removeEventListener('pointerdown', documentPointerHandler, { capture: true });
      documentPointerHandler = null;
    }
    if (documentKeyHandler) {
      document.removeEventListener('keydown', documentKeyHandler);
      documentKeyHandler = null;
    }
  }

  function attachMenu(menu) {
    const trigger = menu.querySelector(TRIGGER_SELECTOR);
    const panel = menu.querySelector(PANEL_SELECTOR);
    if (!trigger || !panel) {
      return;
    }
    registry.set(menu, { trigger, panel });
    trigger.setAttribute('aria-expanded', 'false');
    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleMenu(menu);
    });
    trigger.addEventListener('keydown', (event) => handleTriggerKeydown(menu, event));
    panel.addEventListener('keydown', (event) => handleMenuKeydown(menu, event));
  }

  ready(function init() {
    const menus = Array.from(document.querySelectorAll(MENU_SELECTOR));
    if (!menus.length) {
      return;
    }
    menus.forEach(attachMenu);
  });
})();
