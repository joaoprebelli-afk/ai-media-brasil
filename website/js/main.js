/* ═══════════════════════════════════════════════════════════════
   JOÃOGPT — Main JS
   Minimal, performant, no dependencies
   ═══════════════════════════════════════════════════════════════ */

'use strict';

/* ── Nav: scroll state ─────────────────────────────────────────── */
(function initNav() {
  const nav = document.getElementById('nav');
  if (!nav) return;

  const onScroll = () => {
    nav.classList.toggle('scrolled', window.scrollY > 24);
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll(); // run once on load
})();


/* ── Smooth anchor scroll ──────────────────────────────────────── */
(function initAnchors() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (!target) return;

      e.preventDefault();

      const navH   = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h')) || 68;
      const top    = target.getBoundingClientRect().top + window.scrollY - navH - 16;

      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
})();


/* ── Intersection Observer: reveal on scroll ───────────────────── */
(function initReveal() {
  const els = document.querySelectorAll('.article-card, .stat-card, .newsletter-card, .about-content, .about-stats, .section-header');

  if (!els.length || !('IntersectionObserver' in window)) return;

  els.forEach(el => el.classList.add('reveal'));

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  );

  els.forEach(el => observer.observe(el));
})();


/* ── Newsletter form — Beehiiv integration ─────────────────────── */
(function initNewsletter() {
  const form    = document.getElementById('newsletter-form');
  const success = document.getElementById('newsletter-success');
  const btn     = form ? form.querySelector('.form-btn') : null;
  const input   = form ? form.querySelector('.form-input') : null;

  if (!form || !success || !btn || !input) return;

  const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  form.addEventListener('submit', function (e) {
    const email = input.value.trim();

    if (!isValidEmail(email)) {
      e.preventDefault(); // só bloqueia se inválido
      input.style.borderColor = 'rgba(239, 68, 68, 0.6)';
      input.focus();
      setTimeout(() => { input.style.borderColor = ''; }, 2000);
      return;
    }

    // Email válido — form submete nativamente ao Beehiiv via iframe oculto
    btn.classList.add('loading');
    btn.disabled = true;

    // Mostra estado de sucesso após a submissão completar
    setTimeout(() => {
      form.hidden = true;
      success.hidden = false;
    }, 1500);
  });

  // Reset border on input
  input.addEventListener('input', () => {
    input.style.borderColor = '';
  });
})();


/* ── Utility: passive event helper ────────────────────────────── */
// Touch devices: improve scroll performance
document.addEventListener('touchstart', function() {}, { passive: true });
