/* 🔹 Sin reinicios manuales: se confía en Bootstrap */
document.addEventListener("DOMContentLoaded", () => {
    const el = document.getElementById("heroCarousel");
    if (!el) return;
  
    new bootstrap.Carousel(el, {
      interval: 3000,          // 3 s
      ride:     "carousel",
      touch:    true,
      pause:    false          // nunca se detiene por hover
    });
  });
  
  /* ---------- Fade-up on scroll ---------- */
document.addEventListener("DOMContentLoaded", () => {
  const items = document.querySelectorAll(".fade-up");
  if (!items.length) return;

  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add("is-visible");
        obs.unobserve(e.target);          // anima solo una vez
      }
    });
  }, { threshold:0.25 });

  items.forEach(el => obs.observe(el));
});
