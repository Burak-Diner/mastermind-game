from __future__ import annotations

import uuid
from typing import Dict, Optional

from flask import Flask, jsonify, render_template, request, session

from game import COLOR_NAMES, PALETTES
from web_game import BaseGame, GameError, available_palettes, create_game

app = Flask(__name__)
app.secret_key = "mastermind-secret-key"

_games: Dict[str, BaseGame] = {}


def _ensure_game_id() -> str:
    gid = session.get("game_id")
    if not gid:
        gid = uuid.uuid4().hex
        session["game_id"] = gid
    return gid


def _get_game() -> Optional[BaseGame]:
    gid = session.get("game_id")
    if not gid:
        return None
    return _games.get(gid)


def _set_game(game: BaseGame) -> None:
    gid = _ensure_game_id()
    _games[gid] = game


def _clear_game() -> None:
    gid = session.pop("game_id", None)
    if gid and gid in _games:
        _games.pop(gid, None)


@app.route("/")
def index():
    return render_template(
        "index.html",
        color_names=COLOR_NAMES,
        palettes=available_palettes(),
    )


@app.get("/state")
def get_state():
    game = _get_game()
    if not game:
        return jsonify({"state": None})
    return jsonify({"state": game.to_dict()})


@app.post("/start")
def start_game():
    data = request.get_json(silent=True) or {}
    try:
        mode = str(data["mode"])
        length = int(data["length"])
        color_count = int(data["color_count"])
        max_attempts = int(data["max_attempts"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Eksik veya hatalı ayarlar gönderildi."}), 400

    if color_count not in PALETTES:
        return jsonify({"error": "Geçersiz renk sayısı."}), 400
    symbols = PALETTES[color_count]
    if length < 1 or length > len(symbols):
        return jsonify({"error": "Kod uzunluğu seçilen paletten büyük olamaz."}), 400
    if max_attempts < 1:
        return jsonify({"error": "Deneme sayısı en az 1 olmalı."}), 400

    players = data.get("players") or []
    try:
        game = create_game(
            mode=mode,
            length=length,
            symbols=symbols,
            max_attempts=max_attempts,
            players=players,
        )
    except GameError as exc:
        return jsonify({"error": str(exc)}), 400

    _set_game(game)
    return jsonify({"state": game.to_dict()})


@app.post("/guess")
def submit_guess():
    game = _get_game()
    if not game:
        return jsonify({"error": "Aktif oyun bulunamadı."}), 400
    data = request.get_json(silent=True) or {}
    guess = data.get("guess")
    if not isinstance(guess, list):
        return jsonify({"error": "Tahmin verisi gönderilmedi."}), 400
    player = data.get("player")
    try:
        game.make_guess(guess, player=player)
    except GameError as exc:
        return jsonify({"error": str(exc), "state": game.to_dict()}), 400
    return jsonify({"state": game.to_dict()})


@app.post("/reset")
def reset_game():
    _clear_game()
    return jsonify({"state": None})


if __name__ == "__main__":
    app.run(debug=True)
