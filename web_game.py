"""Web arayüzü için Mastermind oyun motoru."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from game import COLOR_NAMES, PALETTES, feedback, generate_secret, pretty


class GameError(Exception):
    """Web oyununda kullanıcı hatalarını temsil eder."""


@dataclass
class HistoryEntry:
    player: str
    guess: Tuple[str, ...]
    exact: int
    color_only: int

    def to_dict(self, index: int) -> Dict[str, object]:
        return {
            "index": index,
            "player": self.player,
            "guess": [
                {
                    "code": code,
                    "name": COLOR_NAMES.get(code, code),
                }
                for code in self.guess
            ],
            "exact": self.exact,
            "color_only": self.color_only,
        }


def _color_list(symbols: Sequence[str]) -> List[Dict[str, str]]:
    return [
        {
            "code": code,
            "name": COLOR_NAMES.get(code, code),
        }
        for code in symbols
    ]


def _colors_text(code: Sequence[str]) -> str:
    return ", ".join(COLOR_NAMES.get(c, c) for c in code)


class BaseGame:
    mode_key: str = "base"
    mode_label: str = "Mastermind"

    def __init__(self, length: int, symbols: Sequence[str], max_attempts: int) -> None:
        if length < 1:
            raise GameError("Kod uzunluğu en az 1 olmalı.")
        if len(set(symbols)) < length:
            raise GameError("Bu uzunluk için yeterli benzersiz renk yok.")
        self.length = length
        self.symbols = list(symbols)
        self.max_attempts = max_attempts
        self.history: List[HistoryEntry] = []
        self.status: str = "ongoing"
        self.message: str = ""
        self.winner: Optional[str] = None

    # -----------------------
    # Genel yardımcılar
    # -----------------------
    def _validate_guess(self, guess: Iterable[str]) -> Tuple[str, ...]:
        guess_list = [str(item).upper() for item in guess]
        if len(guess_list) != self.length:
            raise GameError(f"Tahmin {self.length} renk içermeli.")
        if any(code not in self.symbols for code in guess_list):
            allowed = ", ".join(self.symbols)
            raise GameError(f"Sadece şu harfleri kullanabilirsin: {allowed}.")
        if len(set(guess_list)) != len(guess_list):
            raise GameError("Her renk yalnızca bir kez seçilebilir.")
        return tuple(guess_list)

    def _history_dict(self) -> List[Dict[str, object]]:
        return [entry.to_dict(i + 1) for i, entry in enumerate(self.history)]

    def _palette_dict(self) -> List[Dict[str, str]]:
        return _color_list(self.symbols)

    def get_active_player(self) -> Optional[str]:
        return None

    def get_attempts_left(self) -> Optional[int]:
        return None

    def players_summary(self) -> List[Dict[str, object]]:
        return []

    def secret_payload(self) -> Optional[Dict[str, object]]:
        return None

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "mode": self.mode_key,
            "mode_label": self.mode_label,
            "length": self.length,
            "max_attempts": self.max_attempts,
            "palette": self._palette_dict(),
            "history": self._history_dict(),
            "status": self.status,
            "message": self.message,
            "active_player": self.get_active_player(),
            "attempts_left": self.get_attempts_left(),
            "players": self.players_summary(),
        }
        secret = self.secret_payload()
        if secret is not None:
            payload["secret"] = secret
        return payload

    # -----------------------
    # Oyun akışı
    # -----------------------
    def make_guess(self, guess: Iterable[str], player: Optional[str] = None) -> None:
        raise NotImplementedError


class PlayerVsAIGame(BaseGame):
    mode_key = "player_vs_ai"
    mode_label = "Oyuncu vs Yapay Zekâ"

    def __init__(
        self,
        length: int,
        symbols: Sequence[str],
        max_attempts: int,
        player_name: Optional[str] = None,
    ) -> None:
        super().__init__(length, symbols, max_attempts)
        self.player_name = (player_name or "Oyuncu").strip() or "Oyuncu"
        self.secret: Tuple[str, ...] = generate_secret(length, symbols)
        self.remaining_attempts = max_attempts
        self.message = (
            f"{self.player_name}, gizli kodu çözmek için {self.remaining_attempts} hakkın var."
        )

    def get_active_player(self) -> Optional[str]:
        return self.player_name if self.status == "ongoing" else None

    def get_attempts_left(self) -> Optional[int]:
        return self.remaining_attempts

    def players_summary(self) -> List[Dict[str, object]]:
        return [
            {
                "name": self.player_name,
                "remaining": self.remaining_attempts,
                "total": self.max_attempts,
                "is_active": self.status == "ongoing",
            }
        ]

    def secret_payload(self) -> Optional[Dict[str, object]]:
        if self.status == "ongoing":
            return None
        return {
            "code": list(self.secret),
            "text": _colors_text(self.secret),
        }

    def make_guess(self, guess: Iterable[str], player: Optional[str] = None) -> None:
        if self.status != "ongoing":
            raise GameError("Oyun tamamlandı, yeni oyun başlatmalısın.")
        if player and player != self.player_name:
            raise GameError("Sıradaki oyuncu sen değilsin.")
        guess_tuple = self._validate_guess(guess)
        exact, color_only = feedback(self.secret, guess_tuple)
        self.history.append(HistoryEntry(self.player_name, guess_tuple, exact, color_only))
        self.remaining_attempts -= 1
        if exact == self.length:
            self.status = "won"
            self.winner = self.player_name
            self.message = f"Harika! {self.player_name} gizli kodu çözdü."
        elif self.remaining_attempts <= 0:
            self.status = "lost"
            self.message = (
                "Tahmin hakları bitti. Gizli kod: "
                + pretty(self.secret)
                + f" ({_colors_text(self.secret)})"
            )
        else:
            self.message = (
                f"Tam isabet: {exact}, doğru renk: {color_only}. "
                f"{self.remaining_attempts} deneme kaldı."
            )


class PvPOneByOneGame(BaseGame):
    mode_key = "pvp_one_by_one"
    mode_label = "Oyuncu vs Oyuncu (Sırayla)"

    def __init__(
        self,
        length: int,
        symbols: Sequence[str],
        max_attempts: int,
        players: Sequence[str],
    ) -> None:
        if len(players) < 2:
            raise GameError("İki oyuncu adı girmelisin.")
        super().__init__(length, symbols, max_attempts)
        self.players = [
            (name.strip() or f"{idx + 1}. Oyuncu") for idx, name in enumerate(players[:2])
        ]
        self.secret: Tuple[str, ...] = generate_secret(length, symbols)
        self.turn_index = 0
        self.guess_counts: Dict[str, int] = {name: 0 for name in self.players}
        self.message = f"Oyun başladı! İlk tahmin {self.players[0]} tarafından yapılacak."

    def get_active_player(self) -> Optional[str]:
        return self.players[self.turn_index] if self.status == "ongoing" else None

    def get_attempts_left(self) -> Optional[int]:
        if self.status != "ongoing":
            return None
        active = self.get_active_player()
        if active is None:
            return None
        return self.max_attempts - self.guess_counts.get(active, 0)

    def players_summary(self) -> List[Dict[str, object]]:
        active = self.get_active_player()
        return [
            {
                "name": name,
                "remaining": self.max_attempts - self.guess_counts.get(name, 0),
                "total": self.max_attempts,
                "is_active": self.status == "ongoing" and name == active,
            }
            for name in self.players
        ]

    def secret_payload(self) -> Optional[Dict[str, object]]:
        if self.status == "ongoing":
            return None
        return {
            "code": list(self.secret),
            "text": _colors_text(self.secret),
        }

    def _advance_turn(self) -> None:
        self.turn_index = (self.turn_index + 1) % len(self.players)

    def _attempts_exhausted(self) -> bool:
        return all(count >= self.max_attempts for count in self.guess_counts.values())

    def make_guess(self, guess: Iterable[str], player: Optional[str] = None) -> None:
        if self.status != "ongoing":
            raise GameError("Oyun tamamlandı, yeni oyun başlatmalısın.")
        active = self.get_active_player()
        if not active:
            raise GameError("Aktif oyuncu bulunamadı.")
        if player and player != active:
            raise GameError(f"Sıradaki oyuncu {active}.")
        guess_tuple = self._validate_guess(guess)
        exact, color_only = feedback(self.secret, guess_tuple)
        self.history.append(HistoryEntry(active, guess_tuple, exact, color_only))
        self.guess_counts[active] += 1
        if exact == self.length:
            self.status = "won"
            self.winner = active
            self.message = f"{active} gizli kodu buldu!"
            return
        if self._attempts_exhausted():
            self.status = "lost"
            self.message = (
                "Hiç kimse gizli kodu bulamadı. Kod: "
                + pretty(self.secret)
                + f" ({_colors_text(self.secret)})"
            )
            return
        self._advance_turn()
        next_player = self.get_active_player()
        remaining = self.get_attempts_left()
        self.message = (
            f"Tam isabet: {exact}, doğru renk: {color_only}. "
            f"Sıradaki oyuncu: {next_player} — kalan hak: {remaining}."
        )


MODE_LABELS = {
    "player_vs_ai": PlayerVsAIGame.mode_label,
    "pvp_one_by_one": PvPOneByOneGame.mode_label,
}


def available_palettes() -> Dict[int, List[str]]:
    """UI tarafında seçim için paletleri döndür."""
    return {size: list(symbols) for size, symbols in PALETTES.items()}


def create_game(
    *,
    mode: str,
    length: int,
    symbols: Sequence[str],
    max_attempts: int,
    players: Optional[Sequence[str]] = None,
) -> BaseGame:
    players = list(players or [])
    if mode == "player_vs_ai":
        player_name = players[0] if players else None
        return PlayerVsAIGame(length, symbols, max_attempts, player_name)
    if mode == "pvp_one_by_one":
        return PvPOneByOneGame(length, symbols, max_attempts, players)
    raise GameError("Desteklenmeyen oyun modu seçildi.")
