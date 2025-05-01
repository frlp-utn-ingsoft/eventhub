function adjustQuantity(amount) {
  const input = document.getElementById("id_quantity");
  let value = parseInt(input.value || 0);
  if (isNaN(value)) value = 0;
  value = Math.max(1, value + amount);
  input.value = value;
  actualizarResumen(); // actualiza el resumen al cambiar la cantidad
}

function actualizarResumen() {
  const cantidad = parseInt(document.getElementById("id_quantity").value) || 1;
  const tipo = document.getElementById("id_type").value;
  const precioUnitario = tipo === "VIP" ? 100 : 50;
  const subtotal = precioUnitario * cantidad;
  const impuestos = subtotal * 0.10;
  const total = subtotal + impuestos;

  document.getElementById("precio_unitario").innerText = precioUnitario;
  document.getElementById("resumen_cantidad").innerText = cantidad;
  document.getElementById("subtotal").innerText = subtotal.toFixed(2);
  document.getElementById("impuestos").innerText = impuestos.toFixed(2);
  document.getElementById("total").innerText = total.toFixed(2);
}

// Actualizar resumen cuando cambia cantidad o tipo
window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("id_quantity").addEventListener("input", actualizarResumen);
  document.getElementById("id_type").addEventListener("change", actualizarResumen);
  actualizarResumen();
});
