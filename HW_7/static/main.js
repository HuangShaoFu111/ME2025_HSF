
async function apiLogin() {
  const res = await fetch("/api/login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({username: document.querySelector("#u").value, password: document.querySelector("#p").value})
  });
  const data = await res.json();
  const msg = document.querySelector("#loginMsg");
  if (data.ok) {
    msg.textContent = "登入成功！";
    document.querySelector("#welcomeName").textContent = data.username;
    document.querySelector("#loginBox").style.display = "none";
    document.querySelector("#app").style.display = "block";
    loadList();
  } else {
    msg.textContent = data.error || "登入失敗";
  }
}

async function loadList() {
  const res = await fetch("/api/grades");
  const data = await res.json();
  if (!data.ok) { return; }
  document.querySelector("#welcomeName").textContent = data.username || "";
  const tbody = document.querySelector("#tbl tbody");
  tbody.innerHTML = "";
  for (const r of data.items) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.name}</td><td>${r.student_id}</td><td>${r.score}</td>
                    <td><button data-id="${r.student_id}">Delete</button></td>`;
    tr.querySelector("button").addEventListener("click", async (ev) => {
      const id = ev.target.getAttribute("data-id");
      await fetch(`/api/grades/${id}`, {method:"DELETE"});
      loadList();
    });
    tbody.appendChild(tr);
  }
}

async function addItem() {
  const name = document.querySelector("#name").value;
  const sid  = document.querySelector("#sid").value;
  const sc   = document.querySelector("#score").value;
  const res = await fetch("/api/grades", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({name, student_id: sid, score: sc})
  });
  const data = await res.json();
  const msg = document.querySelector("#addMsg");
  if (data.ok) {
    msg.textContent = "新增成功！";
    document.querySelector("#name").value = "";
    document.querySelector("#sid").value = "";
    document.querySelector("#score").value = "";
    loadList();
  } else {
    msg.textContent = data.error || "新增失敗";
  }
}

document.querySelector("#btnLogin").addEventListener("click", apiLogin);
document.querySelector("#btnAdd").addEventListener("click", addItem);
