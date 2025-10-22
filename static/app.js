(() => {
  const COLOR_MAP = window.COLOR_NAMES || {};

  const paletteEl = document.getElementById('palette');
  const currentGuessEl = document.getElementById('current-guess');
  const guessCountEl = document.getElementById('guess-count');
  const historyBodyEl = document.getElementById('history-body');
  const historyEmptyEl = document.getElementById('history-empty');
  const modeTitleEl = document.getElementById('mode-title');
  const statusMessageEl = document.getElementById('status-message');
  const badgeEl = document.getElementById('game-status');
  const turnInfoEl = document.getElementById('turn-info');
  const attemptInfoEl = document.getElementById('attempt-info');
  const secretPanelEl = document.getElementById('secret-panel');
  const secretCodeEl = document.getElementById('secret-code');
  const secretTextEl = document.getElementById('secret-text');
  const submitBtn = document.getElementById('submit-btn');
  const undoBtn = document.getElementById('undo-btn');
  const resetBtn = document.getElementById('reset-btn');
  const configForm = document.getElementById('config-form');
  const modeSelect = document.getElementById('mode');
  const playerTwoGroup = document.getElementById('player-two-group');

  let currentGuess = [];
  let currentState = null;

  function handleModeChange() {
    if (modeSelect.value === 'player_vs_ai') {
      playerTwoGroup.style.display = 'none';
    } else {
      playerTwoGroup.style.display = 'flex';
    }
  }

  function fetchState() {
    fetch('/state')
      .then((res) => res.json())
      .then((data) => updateState(data.state || null))
      .catch(() => updateState(null));
  }

  function updateState(state, errorText = '') {
    currentState = state;
    renderState(errorText);
  }

  function renderState(errorText = '') {
    if (!currentState) {
      modeTitleEl.textContent = 'Yeni oyun başlatın';
      badgeEl.textContent = 'Hazır';
      statusMessageEl.textContent = errorText || 'Yan menüden oyun modunu seçerek başlayabilirsin.';
      statusMessageEl.classList.toggle('error', Boolean(errorText));
      turnInfoEl.textContent = '';
      attemptInfoEl.innerHTML = '';
      paletteEl.innerHTML = '';
      historyBodyEl.innerHTML = '';
      historyEmptyEl.hidden = false;
      secretPanelEl.hidden = true;
      submitBtn.disabled = true;
      undoBtn.disabled = true;
      guessCountEl.textContent = '';
      renderCurrentGuess();
      return;
    }

    const state = currentState;
    modeTitleEl.textContent = state.mode_label;

    const statusMap = {
      ongoing: { text: 'Devam ediyor', class: 'badge' },
      won: { text: 'Kazandın', class: 'badge' },
      lost: { text: 'Oyun bitti', class: 'badge' },
    };
    const statusInfo = statusMap[state.status] || statusMap.ongoing;
    badgeEl.textContent = statusInfo.text;

    const message = errorText || state.message || '';
    statusMessageEl.textContent = message;
    statusMessageEl.classList.toggle('error', Boolean(errorText));

    renderPlayers(state);
    renderPalette(state);
    renderHistory(state);
    renderSecret(state);
    renderCurrentGuess();
    updateControls();
  }

  function renderPlayers(state) {
    const players = Array.isArray(state.players) ? state.players : [];
    if (!players.length) {
      turnInfoEl.textContent = state.active_player
        ? `Sıradaki oyuncu: ${state.active_player}`
        : '';
      attemptInfoEl.innerHTML = '';
      return;
    }

    turnInfoEl.textContent = state.active_player
      ? `Sıradaki oyuncu: ${state.active_player}`
      : '';

    const wrapper = document.createElement('div');
    wrapper.className = 'players-list';
    players.forEach((player) => {
      const pill = document.createElement('span');
      pill.className = 'player-pill';
      if (player.is_active) {
        pill.classList.add('active');
      }
      const nameEl = document.createElement('span');
      nameEl.textContent = player.name;
      const attemptsEl = document.createElement('span');
      attemptsEl.className = 'attempts';
      attemptsEl.textContent = `${player.remaining}/${player.total}`;
      pill.appendChild(nameEl);
      pill.appendChild(attemptsEl);
      wrapper.appendChild(pill);
    });
    attemptInfoEl.innerHTML = '';
    attemptInfoEl.appendChild(wrapper);
  }

  function renderPalette(state) {
    paletteEl.innerHTML = '';
    if (!Array.isArray(state.palette)) {
      return;
    }
    const disabled = state.status !== 'ongoing';
    state.palette.forEach((color) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.disabled = disabled;
      button.title = `${color.code} – ${color.name}`;
      const chip = document.createElement('div');
      chip.className = `color-chip color-${color.code}`;
      const label = document.createElement('span');
      label.textContent = color.code;
      chip.appendChild(label);
      button.appendChild(chip);
      button.addEventListener('click', () => {
        addColor(color.code);
      });
      paletteEl.appendChild(button);
    });
  }

  function renderHistory(state) {
    historyBodyEl.innerHTML = '';
    const history = Array.isArray(state.history) ? state.history : [];
    if (!history.length) {
      historyEmptyEl.hidden = false;
      return;
    }
    historyEmptyEl.hidden = true;
    history.forEach((entry) => {
      const row = document.createElement('tr');

      const indexCell = document.createElement('td');
      indexCell.textContent = entry.index;
      row.appendChild(indexCell);

      const playerCell = document.createElement('td');
      playerCell.textContent = entry.player;
      row.appendChild(playerCell);

      const guessCell = document.createElement('td');
      const guessWrapper = document.createElement('div');
      guessWrapper.className = 'guess-cells';
      entry.guess.forEach((item) => {
        guessWrapper.appendChild(createMiniChip(item.code, item.name));
      });
      guessCell.appendChild(guessWrapper);
      row.appendChild(guessCell);

      const exactCell = document.createElement('td');
      exactCell.textContent = entry.exact;
      row.appendChild(exactCell);

      const colorCell = document.createElement('td');
      colorCell.textContent = entry.color_only;
      row.appendChild(colorCell);

      historyBodyEl.appendChild(row);
    });
  }

  function renderSecret(state) {
    if (!state.secret) {
      secretPanelEl.hidden = true;
      secretCodeEl.innerHTML = '';
      secretTextEl.textContent = '';
      return;
    }
    secretPanelEl.hidden = false;
    secretCodeEl.innerHTML = '';
    state.secret.code.forEach((code) => {
      secretCodeEl.appendChild(createMiniChip(code, COLOR_MAP[code]));
    });
    secretTextEl.textContent = state.secret.text;
  }

  function renderCurrentGuess() {
    currentGuessEl.innerHTML = '';
    const state = currentState;
    if (!state) {
      return;
    }
    const limit = state.length;
    currentGuess.forEach((code) => {
      currentGuessEl.appendChild(createMiniChip(code, COLOR_MAP[code]));
    });
    for (let i = currentGuess.length; i < limit; i += 1) {
      const placeholder = document.createElement('div');
      placeholder.className = 'placeholder-slot';
      placeholder.textContent = '?';
      currentGuessEl.appendChild(placeholder);
    }
    guessCountEl.textContent = `${currentGuess.length} / ${limit}`;
  }

  function createMiniChip(code, name) {
    const chip = document.createElement('div');
    chip.className = `mini-chip color-${code}`;
    chip.title = `${code} – ${name || ''}`;
    chip.textContent = code;
    return chip;
  }

  function addColor(code) {
    if (!currentState || currentState.status !== 'ongoing') {
      return;
    }
    if (currentGuess.includes(code)) {
      flashMessage('Aynı rengi tekrar seçemezsin.');
      return;
    }
    if (currentGuess.length >= currentState.length) {
      flashMessage('Tahmin zaten tamamlandı. Gönderebilirsin.');
      return;
    }
    currentGuess.push(code);
    renderCurrentGuess();
    updateControls();
  }

  function undoColor() {
    if (!currentGuess.length) {
      return;
    }
    currentGuess.pop();
    renderCurrentGuess();
    updateControls();
  }

  function updateControls() {
    const ready = Boolean(currentState && currentState.status === 'ongoing');
    undoBtn.disabled = !ready || currentGuess.length === 0;
    submitBtn.disabled = !ready || currentGuess.length !== (currentState ? currentState.length : 0);
  }

  function flashMessage(text) {
    if (!text) {
      return;
    }
    statusMessageEl.textContent = text;
    statusMessageEl.classList.add('error');
    setTimeout(() => {
      if (!currentState) {
        return;
      }
      statusMessageEl.textContent = currentState.message || '';
      statusMessageEl.classList.remove('error');
    }, 1800);
  }

  function submitGuess() {
    if (!currentState || currentState.status !== 'ongoing') {
      return;
    }
    if (currentGuess.length !== currentState.length) {
      flashMessage('Tahmin eksik. Tüm renkleri seçmelisin.');
      return;
    }
    fetch('/guess', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        guess: currentGuess,
        player: currentState.active_player || null,
      }),
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          updateState(data.state || currentState, data.error || 'Geçersiz tahmin.');
          throw new Error(data.error || 'Tahmin gönderilemedi');
        }
        currentGuess = [];
        updateState(data.state || null);
      })
      .catch(() => {
        renderCurrentGuess();
        updateControls();
      });
  }

  function startGame(event) {
    event.preventDefault();
    const formData = new FormData(configForm);
    const mode = formData.get('mode');
    const payload = {
      mode,
      length: Number(formData.get('length')),
      color_count: Number(formData.get('color_count')),
      max_attempts: Number(formData.get('max_attempts')),
      players: [],
    };
    if (mode === 'player_vs_ai') {
      payload.players.push(formData.get('player1') || '');
    } else {
      payload.players.push(formData.get('player1') || '');
      payload.players.push(formData.get('player2') || '');
    }

    fetch('/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          renderState(data.error || 'Oyun başlatılamadı.');
          throw new Error(data.error || 'Başlatma hatası');
        }
        currentGuess = [];
        updateState(data.state || null);
      })
      .catch(() => {
        renderState('Oyun başlatılamadı. Daha sonra tekrar dene.');
      });
  }

  function resetGame() {
    fetch('/reset', { method: 'POST' })
      .then(() => {
        currentGuess = [];
        updateState(null);
      })
      .catch(() => updateState(null));
  }

  submitBtn.addEventListener('click', submitGuess);
  undoBtn.addEventListener('click', undoColor);
  resetBtn.addEventListener('click', resetGame);
  configForm.addEventListener('submit', startGame);
  modeSelect.addEventListener('change', handleModeChange);

  handleModeChange();
  fetchState();
})();
