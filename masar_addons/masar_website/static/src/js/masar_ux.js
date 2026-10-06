/* Progressive enhancements: core forms and service links work without JS. */
(() => {
  'use strict';
  function init() {
    document.querySelectorAll('.masar-service-list').forEach(list => {
      const items = [...list.querySelectorAll('details')];
      const key = 'masar-service-open';
      try {
        const selected = sessionStorage.getItem(key);
        if (selected !== null && items[Number(selected)]) items.forEach((item, i) => { item.open = i === Number(selected); });
      } catch (_) { /* Storage is optional. */ }
      items.forEach((item, index) => item.addEventListener('toggle', () => {
        if (!item.open) return;
        items.forEach(other => { if (other !== item) other.open = false; });
        try { sessionStorage.setItem(key, String(index)); } catch (_) { /* Optional. */ }
      }));
    });
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      const lang = document.activeElement?.closest('.masar-lang');
      if (lang) {
        lang.classList.remove('is-open');
        const toggle = lang.querySelector('button');
        toggle?.setAttribute('aria-expanded', 'false'); toggle?.focus();
      }
      const header = document.querySelector('.masar-header.is-open');
      if (header) {
        header.classList.remove('is-open');
        const toggle = header.querySelector('.masar-nav__toggle');
        toggle?.setAttribute('aria-expanded', 'false'); toggle?.focus();
      }
    });
    document.querySelectorAll('.masar-lang').forEach(lang => {
      const button = lang.querySelector('button');
      if (!button) return;
      const sync = () => button.setAttribute('aria-expanded', String(lang.classList.contains('is-open')));
      new MutationObserver(sync).observe(lang, {attributes:true, attributeFilter:['class']}); sync();
    });
    document.querySelectorAll('[data-masar-request]').forEach(form => {
      const button = form.querySelector('button[type=submit]');
      const label = button.textContent;
      form.addEventListener('submit', () => {
        button.disabled = true; button.textContent = form.dataset.sending;
        form.setAttribute('aria-busy', 'true');
      });
      window.addEventListener('pageshow', () => {button.disabled=false;button.textContent=label;form.removeAttribute('aria-busy');});
      form.querySelector('[data-masar-errors]')?.focus();
    });
    const header = document.querySelector('#wrapwrap > header.masar-header');
    if (header) {
      const root = document.documentElement;
      let frame = 0;
      const syncOffset = () => root.style.setProperty('--masar-header-offset', header.offsetHeight + 'px');
      const syncScroll = () => header.classList.toggle('is-scrolled', (window.scrollY || root.scrollTop || 0) > 12);
      const onScroll = () => {
        if (frame) return;
        frame = window.requestAnimationFrame(() => { frame = 0; syncScroll(); });
      };
      syncOffset();
      syncScroll();
      window.addEventListener('scroll', onScroll, {passive: true});
      window.addEventListener('resize', () => { syncOffset(); syncScroll(); }, {passive: true});
    }
    document.querySelectorAll('[data-masar-search]').forEach(input => {
      const container = input.closest('.masar-block');
      const items = [...container.querySelectorAll('.masar-faq__item')];
      const status = container.querySelector('.masar-filter-status');
      const normalize = text => text.toLocaleLowerCase().normalize('NFKD').replace(/[\u064B-\u065F\u0670\u0640]/g, '').replace(/[أإآ]/g, 'ا').trim();
      input.addEventListener('input', () => {
        const query = normalize(input.value); let matches = 0;
        items.forEach(item => { item.hidden = !normalize(item.textContent).includes(query); if (!item.hidden) matches++; });
        status.textContent = !query ? '' : matches ? input.dataset.matches+' '+matches : input.dataset.empty;
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
})();
