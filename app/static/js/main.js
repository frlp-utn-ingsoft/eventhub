// main.js
// Funciones generales para la app (toast, scroll, etc.)

document.addEventListener("DOMContentLoaded", () => {
    // Mensajes de éxito o error automáticos
    const alerts = document.querySelectorAll(".alert-auto-dismiss");
    alerts.forEach(alert => {
      setTimeout(() => {
        alert.classList.add("fade");
        setTimeout(() => alert.remove(), 300); // remove after animation
      }, 4000);
    });
  });
  

  document.addEventListener("DOMContentLoaded", () => {
    const nav = document.getElementById("navbar-content");
    const burger = document.querySelector(".navbar-toggler");
  
    burger?.addEventListener("click", () => {
      nav.classList.toggle("animate-slide-down");
      // al cerrar (hidden.bs.collapse) quitamos la clase
      nav.addEventListener("hidden.bs.collapse", () =>
        nav.classList.remove("animate-slide-down"), { once: true });
    });
  });