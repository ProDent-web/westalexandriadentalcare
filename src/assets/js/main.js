/* West Alexandria Dental Care — interactions
   Progressive enhancement only: the site works fully without this file. */
(function () {
  'use strict';
  const d = document;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, c) => (c || d).querySelector(s);
  const $$ = (s, c) => Array.from((c || d).querySelectorAll(s));

  /* ---------- live hours (America/New_York) ---------- */
  const HOURS = (window.WADC && window.WADC.hours) || [];
  function nowInNY() {
    try {
      const f = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'short', hour: 'numeric', minute: 'numeric', hour12: false });
      const parts = Object.fromEntries(f.formatToParts(new Date()).map(p => [p.type, p.value]));
      const days = { Sun: 6, Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5 };
      return { day: days[parts.weekday], h: parseInt(parts.hour, 10) % 24, m: parseInt(parts.minute, 10) };
    } catch (e) { const n = new Date(); return { day: (n.getDay() + 6) % 7, h: n.getHours(), m: n.getMinutes() }; }
  }
  function fmt(h) { const ap = h >= 12 ? 'PM' : 'AM'; const hh = h % 12 || 12; return hh + ':00 ' + ap; }
  function status() {
    if (!HOURS.length) return null;
    const t = nowInNY();
    const today = HOURS[t.day];
    const mins = t.h * 60 + t.m;
    if (today && mins >= today.o * 60 && mins < today.c * 60) {
      const left = today.c * 60 - mins;
      return { open: true, text: left <= 60 ? 'Open now · closing soon' : 'Open now · until ' + fmt(today.c) };
    }
    if (today && mins < today.o * 60) return { open: false, text: 'Opens today at ' + fmt(today.o) };
    const tomorrow = HOURS[(t.day + 1) % 7];
    return { open: false, text: 'Opens tomorrow at ' + fmt(tomorrow.o) };
  }
  function paintStatus() {
    const s = status(); if (!s) return;
    $$('[data-status]').forEach(el => {
      el.classList.toggle('status--closed', !s.open);
      const txt = $('[data-status-text]', el); if (txt) txt.textContent = s.text;
    });
    const day = nowInNY().day;
    $$('[data-hours-table] tr').forEach((tr, i) => tr.classList.toggle('is-today', i === day));
  }
  paintStatus(); setInterval(paintStatus, 60000);

  /* ---------- header scroll state ---------- */
  const header = $('.header');
  let lastY = 0;
  function onScroll() {
    const y = window.scrollY || 0;
    if (header) header.classList.toggle('is-scrolled', y > 8);
    const bar = $('.sticky-cta');
    if (bar) bar.classList.toggle('is-visible', y > 420);
    lastY = y;
  }
  onScroll(); window.addEventListener('scroll', onScroll, { passive: true });

  /* ---------- desktop nav panels ---------- */
  const items = $$('.nav__item--has-panel');
  let hoverTimer;
  function closeAll(except) { items.forEach(it => { if (it !== except) { it.classList.remove('is-open'); const b = $('.nav__link', it); if (b) b.setAttribute('aria-expanded', 'false'); } }); }
  items.forEach(it => {
    const btn = $('.nav__link', it);
    const open = () => { closeAll(it); it.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true'); };
    const close = () => { it.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); };
    it.addEventListener('mouseenter', () => { clearTimeout(hoverTimer); hoverTimer = setTimeout(open, 60); });
    it.addEventListener('mouseleave', () => { clearTimeout(hoverTimer); hoverTimer = setTimeout(close, 180); });
    btn.addEventListener('click', e => { e.preventDefault(); it.classList.contains('is-open') ? close() : open(); });
    it.addEventListener('keydown', e => { if (e.key === 'Escape') { close(); btn.focus(); } });
    it.addEventListener('focusout', e => { if (!it.contains(e.relatedTarget)) close(); });
  });
  d.addEventListener('click', e => { if (!e.target.closest('.nav__item--has-panel')) closeAll(); });

  /* ---------- mobile drawer ---------- */
  const drawer = $('.drawer');
  const burger = $('.burger');
  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle('is-open', open);
    drawer.setAttribute('aria-hidden', String(!open));
    if (burger) burger.setAttribute('aria-expanded', String(open));
    d.documentElement.style.overflow = open ? 'hidden' : '';
    if (open) { const c = $('.drawer__close', drawer); c && c.focus(); } else if (burger) burger.focus();
  }
  if (burger && drawer) {
    burger.addEventListener('click', () => setDrawer(true));
    $$('[data-drawer-close]', drawer).forEach(el => el.addEventListener('click', () => setDrawer(false)));
    d.addEventListener('keydown', e => { if (e.key === 'Escape' && drawer.classList.contains('is-open')) setDrawer(false); });
  }

  /* ---------- scroll reveal ---------- */
  const revealEls = $$('.reveal, .reveal-stagger');
  if (!reduce && 'IntersectionObserver' in window && revealEls.length) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(el => io.observe(el));
  } else { revealEls.forEach(el => el.classList.add('in')); }

  /* ---------- accordion height animation ---------- */
  $$('details.faq__item').forEach(det => {
    const sum = $('summary', det); const body = $('.faq__a', det);
    if (!sum || !body || reduce) return;
    sum.addEventListener('click', e => {
      e.preventDefault();
      if (det.open) {
        const h = body.offsetHeight;
        body.style.height = h + 'px'; body.style.overflow = 'hidden';
        requestAnimationFrame(() => { body.style.transition = 'height 260ms cubic-bezier(.22,1,.36,1), opacity 200ms'; body.style.height = '0px'; body.style.opacity = '0'; });
        body.addEventListener('transitionend', function te() { det.open = false; body.style.cssText = ''; body.removeEventListener('transitionend', te); });
      } else {
        det.open = true;
        const h = body.offsetHeight;
        body.style.height = '0px'; body.style.overflow = 'hidden'; body.style.opacity = '0';
        requestAnimationFrame(() => { body.style.transition = 'height 300ms cubic-bezier(.22,1,.36,1), opacity 260ms 60ms'; body.style.height = h + 'px'; body.style.opacity = '1'; });
        body.addEventListener('transitionend', function te() { body.style.cssText = ''; body.removeEventListener('transitionend', te); });
      }
    });
  });

  /* ---------- on-this-page highlighting ---------- */
  const tocLinks = $$('.toc a[href^="#"]');
  if (tocLinks.length && 'IntersectionObserver' in window) {
    const map = new Map();
    tocLinks.forEach(a => { const t = $(a.getAttribute('href')); if (t) map.set(t, a); });
    const io2 = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (en.isIntersecting) { tocLinks.forEach(a => a.classList.remove('is-active')); const a = map.get(en.target); a && a.classList.add('is-active'); }
      });
    }, { rootMargin: '-20% 0px -65% 0px', threshold: 0 });
    map.forEach((a, t) => io2.observe(t));
  }

  /* ---------- contact form → prepared email (no server needed) ---------- */
  const form = $('[data-inquiry-form]');
  if (form) {
    form.addEventListener('submit', e => {
      e.preventDefault();
      const f = new FormData(form);
      const to = form.getAttribute('data-to') || '';
      const subject = 'Website inquiry: ' + (f.get('reason') || 'General question');
      const body = ['Name: ' + (f.get('name') || ''), 'Phone: ' + (f.get('phone') || ''), 'Email: ' + (f.get('email') || ''), 'Reason: ' + (f.get('reason') || ''), '', (f.get('message') || '')].join('\n');
      if (to) {
        window.location.href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      } else {
        const note = $('[data-form-note]', form);
        if (note) note.textContent = 'Thanks. For the fastest reply, call 703-560-7200 or use Book online; this form will be connected to the office inbox before launch.';
      }
    });
  }

  /* ---------- mark current nav ---------- */
  const path = location.pathname.replace(/index\.html$/, '');
  $$('.nav__link[href], .panel__list a[href], .siblings a[href]').forEach(a => {
    const h = a.getAttribute('href');
    if (h && h !== '/' && path.startsWith(h)) a.classList.add('is-current');
  });

  /* ---------- gentle parallax on hero media ---------- */
  const heroMedia = $('.hero__media');
  if (heroMedia && !reduce && window.matchMedia('(min-width: 960px)').matches) {
    window.addEventListener('scroll', () => {
      const y = Math.min(window.scrollY, 600);
      heroMedia.style.transform = 'translateY(' + (y * 0.06) + 'px)';
    }, { passive: true });
  }
})();
