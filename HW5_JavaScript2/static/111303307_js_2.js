// 更新總價
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
// checkbox 全選
document.getElementById("checkAll").addEventListener("change", function() {
  const checked = this.checked;
  document.querySelectorAll(".item-check").forEach(cb => {
    cb.checked = checked;
  });
  updateTotal();
});
// 單獨的 checkbox
document.querySelectorAll(".item-check").forEach(cb => {
  cb.addEventListener("change", function() {
    const all = document.querySelectorAll(".item-check");
    const allChecked = Array.from(all).every(c => c.checked);
    document.getElementById("checkAll").checked = allChecked;
    updateTotal();
  });
});
// 數量輸入變化
document.querySelectorAll(".qty").forEach(input => {
  input.addEventListener("input", updateTotal);
});
// 初始計算
updateTotal();