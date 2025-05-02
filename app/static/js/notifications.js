// notifications.js
// Manejo dinámico del dropdown de notificaciones

document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("notifButton");
  const dropdown = document.getElementById("notifDropdown");
  const url = dropdown?.dataset?.url || "/notifications/dropdown/";

  if (!button || !dropdown) return;

  let visible = false;

  const toggleDropdown = () => {
    visible = !visible;
    button.setAttribute("aria-expanded", visible);
    dropdown.classList.toggle("show", visible);

    if (visible && dropdown.innerHTML.trim() === "") {
      fetch(url)
        .then(res => res.json())
        .then(data => {
          dropdown.innerHTML = data.html;
        })
        .catch(err => console.error("Error al cargar notificaciones:", err));
    }
  };

  button.addEventListener("click", e => {
    e.stopPropagation();
    toggleDropdown();
  });

  document.addEventListener("click", e => {
    if (!dropdown.contains(e.target) && !button.contains(e.target)) {
      dropdown.classList.remove("show");
      button.setAttribute("aria-expanded", false);
      visible = false;
    }
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