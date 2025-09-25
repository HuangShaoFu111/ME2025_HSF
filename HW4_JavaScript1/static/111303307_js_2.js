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

// 指定畫面排版 
document.write('<div style="max-width: 320px; font-family: system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Arial; line-height:1.4;">');

// 輸入框
document.write(`<input id="${INPUT_ID}" type="text" style="width:100%; padding:8px; font-size:18px; box-sizing:border-box; margin-bottom:12px;" placeholder="請輸入算式，例如：6*(8+8)"/>`);

//繪出數字鍵盤
document.write('<div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; margin-bottom:8px;">');
for (let i = 0; i <= 9; i++) {
  document.write(`<button style="padding:8px; font-size:18px;" onclick="appAppend('${i}')">${i}</button>`);
}
document.write('</div>');

// clear
document.write('<div style="margin-bottom:8px;">');
document.write('<button style="padding:8px; font-size:18px; width:100%;" onclick="appClear()">clear</button>');
document.write('</div>');

// 符號列：「+ - * / ( ) =」
const ops = ["+", "-", "*", "/", "(", ")", "="];
document.write('<div style="display:grid; grid-template-columns: repeat(7, 1fr); gap:6px;">');
ops.forEach(op => {
  if (op === "=") {
    document.write(`<button style="padding:8px; font-size:18px;" onclick="appEval()">${op}</button>`);
  } else {
    document.write(`<button style="padding:8px; font-size:18px;" onclick="appAppend('${op}')">${op}</button>`);
  }
});
document.write('</div>');
document.write('</div>');