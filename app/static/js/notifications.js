// notifications.js
// Manejo dinámico del dropdown de notificaciones

document.addEventListener("DOMContentLoaded", () => {
    const dropdown = document.getElementById("notifMenu");
    dropdown?.addEventListener("show.bs.dropdown", () => {
      fetch("/notifications/dropdown/")
        .then(response => response.json())
        .then(data => {
          const container = document.getElementById("notifDropdown");
          container.innerHTML = data.html || "<li class='dropdown-item text-muted'>Sin notificaciones</li>";
        })
        .catch(err => console.error("Error al cargar notificaciones:", err));
    });
  });
  