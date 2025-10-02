(() => {
  "use strict";

  const newAnswer = () => Math.floor(Math.random() * 101);

  let answer = newAnswer();
  let attempts = 0;
  let ticker = null;                 // setInterval 的 id
  function tick() {                  // 每 50ms 更新一次畫面時間
    if (!startTs) return;
    const secs = (Date.now() - startTs) / 1000;
    timerEl.textContent = `時間：${secs.toFixed(2)} s`;
  }


  const helper = document.querySelector("#helper");
  const $ = (sel) => document.querySelector(sel);
  const input = $("#guessInput");
  const btn = $("#guessBtn");

  let startTs = 0;                         // 第一次作答的時間戳
  const timerEl = document.getElementById("timer");
  const historyEl = document.getElementById("history");

  function tryGuess() {
    const val = input.value.trim();

    if (val === "") {helper.textContent = "請先輸入數字！"; return; }
    if (!/^\d+$/.test(val)) { helper.textContent = "請輸入 0~100 的整數！"; return; }

    const n = Number(val);
    if (n < 0 || n > 100) { helper.textContent = "範圍錯誤：請輸入 0~100 的整數！"; return; }
    // 第一次作答時才啟動計時器，之後自動連續更新
    if (attempts === 0 && startTs === 0) {
      startTs = Date.now();
      tick();                         
      if (!ticker) ticker = setInterval(tick, 50);  
    }

    attempts += 1;

    if (n > answer) {
      helper.textContent = "太大了，請再試一次。";;
    } else if (n < answer) {
      helper.textContent = "太小了，請再試一次。";
    } else {
      clearInterval(ticker);   // 停止背景計時
      ticker = null;
      tick();                  // 把畫面時間停在最後值
      const secs = (Date.now() - startTs) / 1000;
      alert(`猜中了！共猜了 ${attempts} 次，花了 ${secs.toFixed(2)} 秒。`);

      // 寫入歷史紀錄
      const li = document.createElement("li");
      li.textContent = `猜了 ${attempts} 次，耗時 ${secs.toFixed(2)} 秒　${new Date().toLocaleTimeString()}`;
      historyEl.appendChild(li);

      // 重置下一題
      answer = newAnswer();
      attempts = 0;
      startTs = 0;
      timerEl.textContent = "時間：0.00 s";
      helper.textContent = "";   // 你的提示區：把「太大/太小」寫在這裡
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