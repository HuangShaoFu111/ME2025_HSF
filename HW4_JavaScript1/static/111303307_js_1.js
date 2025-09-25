(() => {
  "use strict";

  const newAnswer = () => Math.floor(Math.random() * 101);

  let answer = newAnswer();
  let attempts = 0;

  const $ = (sel) => document.querySelector(sel);
  const input = $("#guessInput");
  const btn = $("#guessBtn");

  function tryGuess() {
    const val = input.value.trim();

    // 基本檢查
    if (val === "") { alert("請先輸入數字！"); return; }
    if (!/^\d+$/.test(val)) { alert("請輸入 0~100 的整數！"); return; }

    const n = Number(val);
    if (n < 0 || n > 100) { alert("範圍錯誤：請輸入 0~100 的整數！"); return; }

    attempts += 1;

    if (n > answer) {
      alert("太大了，請再試一次。");
    } else if (n < answer) {
      alert("太小了，請再試一次。");
    } else {
      alert(`恭喜你，猜對了！你總共猜了 ${attempts} 次。`);
      // 重新開始新的一題
      answer = newAnswer();
      attempts = 0;
      input.value = "";
    }
    input.focus();
    input.select();
  }

  btn.addEventListener("click", tryGuess);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") tryGuess();
  });

  })();