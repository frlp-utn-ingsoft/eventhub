// accounts.js
// Validaciones para login/registro

document.addEventListener("DOMContentLoaded", () => {
    const password = document.getElementById("password");
    const confirm = document.getElementById("password-confirm");
  
    if (password && confirm) {
      confirm.addEventListener("input", () => {
        if (password.value !== confirm.value) {
          confirm.setCustomValidity("Las contraseñas no coinciden");
        } else {
          confirm.setCustomValidity("");
        }
      });
    }
  });
  