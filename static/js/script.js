function adjustQuantity(amount) {
    const input = document.getElementById("id_quantity");
    let value = parseInt(input.value) || 1;
    value = value + amount;
    if (value < 1) value = 1;
    input.value = value;
  }
  