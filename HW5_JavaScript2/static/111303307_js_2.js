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

// 個別 checkbox
document.querySelectorAll(".item-check").forEach(cb => {
  cb.addEventListener("change", function() {
    const all = document.querySelectorAll(".item-check");
    const allChecked = Array.from(all).every(c => c.checked);
    document.getElementById("checkAll").checked = allChecked;
    updateTotal();
  });
});

// 數量輸入框 → 直接輸入
document.querySelectorAll(".qty").forEach(input => {
  input.addEventListener("input", function() {
    const stock = parseInt(this.closest("tr").querySelector(".stock").textContent);
    if (this.value < 1) this.value = 1;
    if (this.value > stock) this.value = stock;
    updateTotal();
  });
});

// ➕ 按鈕
document.querySelectorAll(".plus").forEach(btn => {
  btn.addEventListener("click", function() {
    const row = this.closest("tr");
    const qtyInput = row.querySelector(".qty");
    const stock = parseInt(row.querySelector(".stock").textContent);
    let qty = parseInt(qtyInput.value);
    if (qty < stock) {
      qtyInput.value = qty + 1;
      updateTotal();
    }
  });
});

// ➖ 按鈕
document.querySelectorAll(".minus").forEach(btn => {
  btn.addEventListener("click", function() {
    const row = this.closest("tr");
    const qtyInput = row.querySelector(".qty");
    let qty = parseInt(qtyInput.value);
    if (qty > 1) {
      qtyInput.value = qty - 1;
      updateTotal();
    }
  });
});

// 初始計算
updateTotal();

// 結帳按鈕
document.getElementById("checkout").addEventListener("click", function() {
  let total = parseInt(document.getElementById("total").textContent);
  if (total <= 0) {
    alert("尚未選擇商品");
    return;
  }

  let summary = "購買明細：\n";
  document.querySelectorAll("tbody tr").forEach(row => {
    const check = row.querySelector(".item-check");
    if (check.checked) {
      const name = row.cells[1].textContent;
      const qtyInput = row.querySelector(".qty");
      const qty = parseInt(qtyInput.value);
      const price = parseInt(row.querySelector(".price").textContent);
      const subtotal = qty * price;

      // 扣庫存
      let stockCell = row.querySelector(".stock");
      let stock = parseInt(stockCell.textContent);
      stockCell.textContent = stock - qty;

      // 更新 max 屬性
      qtyInput.max = stock - qty;

      // 更新摘要
      summary += `${name} x ${qty} = ${subtotal}\n`;

      // 重設狀態
      check.checked = false;
      if (stock - qty > 0) {
        qtyInput.value = 1;
      } else {
        qtyInput.value = 0;
      }
    }
  });

  alert(summary + `\n總金額：${total}`);

  // 全選框取消
  document.getElementById("checkAll").checked = false;

  // 更新金額
  updateTotal();
});

