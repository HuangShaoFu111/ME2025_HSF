const INPUT_ID = "exprInput";

// 先宣告功能函式，給onclick
window.appAppend = function (ch) {
  const ipt = document.getElementById(INPUT_ID);
  ipt.value += ch;
  ipt.focus();
};

window.appClear = function () {
  const ipt = document.getElementById(INPUT_ID);
  ipt.value = "";
  ipt.focus();
};

window.appEval = function () {
  const ipt = document.getElementById(INPUT_ID);
  const expr = ipt.value;
  try {
      // 使用 eval 計算
      const ans = eval(expr);
      alert(`${expr} = ${ans}`);
      ipt.value = ans; // 輸入框改為答案
    } catch (err) {
      alert("表達式錯誤，請重新輸入。");
    }
    ipt.focus();
  };


document.write('<div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin-bottom:8px;">');
for (let i = 0; i <= 9; i++) {
  document.write(`<button style="padding:8px; font-size:18px;" onclick="appAppend('${i}')">${i}</button>`);
}
document.write('</div>');