function updateTotal() {
  let total = 0;
  document.querySelectorAll("tbody tr").forEach(row => {
    const check = row.querySelector(".item-check");
    const qty = parseInt(row.querySelector(".qty").value);
    const price = parseInt(row.querySelector(".price").textContent);
    const subtotalCell = row.querySelector(".subtotal");

    const subtotal = qty * price;
    subtotalCell.textContent = subtotal;

    if (check.checked) {
      total += subtotal;
    }
  });
  document.getElementById("total").textContent = total;
}
