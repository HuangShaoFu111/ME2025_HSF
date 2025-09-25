document.write('<div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin-bottom:8px;">');
for (let i = 0; i <= 9; i++) {
  document.write(`<button style="padding:8px; font-size:18px;" onclick="appAppend('${i}')">${i}</button>`);
}
document.write('</div>');