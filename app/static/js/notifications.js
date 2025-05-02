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
  
  
/* --- buscador de usuarios en el formulario de notificaciones --- */
document.addEventListener("DOMContentLoaded", () => {
  const select = document.querySelector(".select-user");
  if (!select) return;                  // el select no existe en esta página

  const ORIGINAL = [...select.options]; // snapshot original

  // crea el input siempre
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "Buscar por nombre o email…";
  input.className = "form-control mb-2";
  select.before(input);

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    select.replaceChildren();            // vacía el select

    if (!q) {                            // sin filtro → restaurar
      ORIGINAL.forEach(o => select.append(o));
      return;
    }

    const pri = [], sec = [];
    ORIGINAL.forEach(opt => {
      const txt = opt.textContent.toLowerCase();
      if (txt.startsWith(q)) pri.push(opt);
      else if (txt.includes(q)) sec.push(opt);
    });

    [...pri, ...sec].forEach(o => select.append(o));
  });
});