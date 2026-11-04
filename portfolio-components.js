(() => {
  'use strict';
  document.querySelectorAll('.portfolio-reviews').forEach(section => {
    const track = section.querySelector('.portfolio-reviews__track');
    const prev = section.querySelector('[data-reviews-prev]');
    const next = section.querySelector('[data-reviews-next]');
    if (!track || !prev || !next) return;
    section.setAttribute('data-ready', '');
    const update = () => {
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
    };
    const move = direction => track.scrollBy({left: direction * Math.min(track.clientWidth, 388), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    prev.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    track.addEventListener('scroll', update, {passive: true});
    window.addEventListener('resize', update, {passive: true});
    update();
  });
})();
