// notifications.js
// Manejo dinámico del dropdown de notificaciones

document.addEventListener("DOMContentLoaded", function () {
  const dropdown = document.getElementById("notifDropdown");
  const url = dropdown?.dataset?.url;
  if (!url) return;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      dropdown.innerHTML = data.html;
    })
    .catch(error => console.error("Error al cargar notificaciones:", error));
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

document.addEventListener("DOMContentLoaded", () => {
  const filterBubbles = document.querySelectorAll(".filter-bubble");
  if (filterBubbles.length === 0) return;

  filterBubbles.forEach(bubble => {
    bubble.addEventListener("click", function (e) {
      e.preventDefault();
      const param = this.dataset.param;
      const url = new URL(window.location.href);
      url.searchParams.delete(param);
      window.location.href = url.toString();
    });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("notifTableScroll");
  let isDown = false;
  let startX, scrollLeft;

  if (!container) return;

  container.addEventListener("mousedown", (e) => {
    isDown = true;
    container.classList.add("active");
    startX = e.pageX - container.offsetLeft;
    scrollLeft = container.scrollLeft;
  });

  container.addEventListener("mouseleave", () => {
    isDown = false;
    container.classList.remove("active");
  });

  container.addEventListener("mouseup", () => {
    isDown = false;
    container.classList.remove("active");
  });

  container.addEventListener("mousemove", (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - container.offsetLeft;
    const walk = (x - startX) * 1.5;
    container.scrollLeft = scrollLeft - walk;
  });
});