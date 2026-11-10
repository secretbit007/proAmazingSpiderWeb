(function () {
  'use strict';

  var hud = document.querySelector('.game-hud--live');
  if (!hud) {
    return;
  }

  var movesEl = hud.querySelector('[data-hud="moves"]');
  var timeEl = hud.querySelector('[data-hud="time"]');
  var doneEl = hud.querySelector('[data-hud="done"]');
  if (!movesEl || !timeEl || !doneEl) {
    return;
  }

  var state = { moves: 0, seconds: 0, complete: 0, completeMax: 8 };
  var tick = 0;

  function formatTime(totalSeconds) {
    var minutes = Math.floor(totalSeconds / 60);
    var seconds = totalSeconds % 60;
    return minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
  }

  function render() {
    movesEl.textContent = String(state.moves);
    timeEl.textContent = formatTime(state.seconds);
    doneEl.textContent = state.complete + '/' + state.completeMax;
  }

  function pulse(chip) {
    chip.classList.remove('game-hud__chip--tick');
    void chip.offsetWidth;
    chip.classList.add('game-hud__chip--tick');
  }

  // One tick a second, like the clock in the app.
  function step() {
    tick += 1;
    state.seconds += 1;
    if (tick % 2 === 0) {
      state.moves += 1;
      pulse(movesEl.closest('.game-hud__chip'));
    }
    if (tick % 12 === 0 && state.complete < state.completeMax) {
      state.complete += 1;
      pulse(doneEl.closest('.game-hud__chip'));
    }
    if (tick >= 40) {
      state.moves = 0;
      state.seconds = 0;
      state.complete = 0;
      tick = 0;
    }
    render();
  }

  render();

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  window.setInterval(step, 1000);
})();
