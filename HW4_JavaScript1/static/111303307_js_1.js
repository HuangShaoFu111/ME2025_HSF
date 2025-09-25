(() => {
  "use strict";

  const newAnswer = () => Math.floor(Math.random() * 101);

  let answer = newAnswer();
  let attempts = 0;

  const $ = (sel) => document.querySelector(sel);
  const input = $("#guessInput");
  const btn = $("#guessBtn");
  })();