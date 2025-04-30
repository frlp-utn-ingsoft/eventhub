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
  