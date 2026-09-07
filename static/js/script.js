document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-count]').forEach((el) => {
    const target = Number(el.dataset.count); const suffix = el.dataset.suffix || ''; const duration = 900; const start = performance.now();
    const tick = (now) => { const progress = Math.min((now - start) / duration, 1); el.textContent = Math.floor(progress * target).toLocaleString() + suffix; if (progress < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  });
  const observer = new IntersectionObserver((entries) => entries.forEach((entry) => { if (entry.isIntersecting) entry.target.classList.add('visible'); }), {threshold: .12});
  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
});
