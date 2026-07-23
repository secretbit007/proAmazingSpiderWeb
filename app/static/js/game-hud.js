(function () {
  'use strict';

  var hud = document.querySelector('.game-hud--live');
  if (!hud) {
    return;
  }

  var movesEl = hud.querySelector('[data-hud="moves"]');
  var stackEl = hud.querySelector('[data-hud="stack"]');
  var doneEl = hud.querySelector('[data-hud="done"]');
  if (!movesEl || !stackEl || !doneEl) {
    return;
  }

  var state = { moves: 0, stockLeft: 5, stockMax: 5, complete: 0, completeMax: 8 };
  var tick = 0;

  function render() {
    movesEl.textContent = String(state.moves);
    stackEl.textContent = state.stockLeft + '/' + state.stockMax;
    doneEl.textContent = state.complete + '/' + state.completeMax;
  }

  function pulse(chip) {
    chip.classList.remove('game-hud__chip--tick');
    void chip.offsetWidth;
    chip.classList.add('game-hud__chip--tick');
  }

  function step() {
    tick += 1;
    if (tick % 3 === 0 && state.stockLeft > 0) {
      state.stockLeft -= 1;
      state.moves += 1;
      pulse(stackEl.closest('.game-hud__chip'));
    } else if (tick % 5 === 0) {
      state.moves += 1;
      pulse(movesEl.closest('.game-hud__chip'));
    }
    if (tick === 14 && state.complete < 1) {
      state.complete = 1;
      pulse(doneEl.closest('.game-hud__chip'));
    }
    if (tick >= 22) {
      state.moves = 0;
      state.stockLeft = state.stockMax;
      state.complete = 0;
      tick = 0;
    }
    render();
  }

  render();

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  window.setInterval(step, 1400);
})();
