// events.js
// Lógica específica de eventos (validaciones, interacción)

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("eventForm");
    if (form) {
      form.addEventListener("submit", (e) => {
        const title = form.querySelector("[name='title']").value.trim();
        const date = form.querySelector("[name='date']").value;
        if (!title || !date) {
          e.preventDefault();
          alert("Por favor completá todos los campos obligatorios.");
        }
      });
    }
  });
  