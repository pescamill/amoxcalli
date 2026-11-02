'use strict';
// Una diapositiva a la vez: ← → (o espacio, Re Pág/Av Pág, clic). «?todas» en la URL muestra todas seguidas.
// Imprimir (Cmd/Ctrl+P → Guardar como PDF) siempre saca una diapositiva por página.
(function () {
  const slides = [...document.querySelectorAll('.slide')];
  if (!slides.length || /[?&]todas\b/.test(location.search)) return;
  document.body.classList.add('present');
  let i = Math.min(Math.max(parseInt(location.hash.slice(1), 10) || 1, 1), slides.length) - 1;
  const show = (k) => {
    i = Math.min(Math.max(k, 0), slides.length - 1);
    slides.forEach((s, j) => s.classList.toggle('on', j === i));
    history.replaceState(null, '', '#' + (i + 1));
  };
  document.addEventListener('keydown', (e) => {
    if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); show(i + 1); }
    else if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); show(i - 1); }
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(slides.length - 1);
  });
  document.addEventListener('click', (e) => { if (!e.target.closest('a')) show(i + (e.clientX < innerWidth / 3 ? -1 : 1)); });
  const hint = document.createElement('div');
  hint.className = 'hint';
  hint.textContent = document.documentElement.lang === 'en' ? '← → to move · ?todas to see all' : '← → para avanzar · ?todas para ver todas';
  document.body.appendChild(hint);
  show(i);
})();
