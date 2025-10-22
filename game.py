# -*- coding: utf-8 -*-
"""
Renk Kodu: Yapay Zekâya Karşı (Mastermind Tarzı)
Konsol oyunu — Python 3.8+
"""
from __future__ import annotations

import itertools
import random
import sys
from typing import List, Tuple, Sequence

# -------------------------------
# Yardımcı veri ve fonksiyonlar
# -------------------------------

PALETTES = {
    6: ["R", "G", "B", "Y", "O", "P"],
    8: ["R", "G", "B", "Y", "O", "P", "C", "W"],
}

COLOR_NAMES = {
    "R": "Kırmızı",
    "G": "Yeşil",
    "B": "Mavi",
    "Y": "Sarı",
    "O": "Turuncu",
    "P": "Mor",
    "C": "Camgöbeği",
    "W": "Beyaz",
}


def palette_description(symbols: Sequence[str]) -> str:
    return ", ".join(f"{sym} = {COLOR_NAMES[sym]}" for sym in symbols)

def feedback(secret: Sequence[str], guess: Sequence[str]) -> Tuple[int, int]:
    """
    Mastermind geri bildirimi:
    - tam: renk + konum doğru
    - renk: renk doğru, konum yanlış (çifte sayımı önleyerek)
    """
    if len(secret) != len(guess):
        raise ValueError("feedback: Farklı uzunluk!")

    n = len(secret)
    used_s = [False]*n
    used_g = [False]*n

    # Tam eşleşmeler
    exact = 0
    for i in range(n):
        if guess[i] == secret[i]:
            exact += 1
            used_s[i] = True
            used_g[i] = True

    # Sadece renk eşleşmeleri
    color_only = 0
    for i in range(n):
        if used_g[i]: 
            continue
        for j in range(n):
            if used_s[j]: 
                continue
            if guess[i] == secret[j]:
                color_only += 1
                used_s[j] = True
                used_g[i] = True
                break

    return exact, color_only

def all_codes(length: int, symbols: List[str]) -> List[Tuple[str, ...]]:
    return list(itertools.permutations(symbols, length))

def parse_guess(raw: str, length: int, allowed: List[str]) -> List[str]:
    s = (raw or "").strip().upper().replace(" ", "")
    if len(s) != length:
        raise ValueError(f"Girdi uzunluğu {length} olmalı.")
    if any(ch not in allowed for ch in s):
        raise ValueError(
            "Geçersiz harf kullanıldı. İzin verilenler: "
            + ", ".join(f"{c} ({COLOR_NAMES[c]})" for c in allowed)
        )
    if len(set(s)) != len(s):
        raise ValueError("Her rengi en fazla bir kez kullanabilirsin.")
    return list(s)

def pretty(code: Sequence[str]) -> str:
    return " ".join(code)


def generate_secret(length: int, symbols: Sequence[str]) -> Tuple[str, ...]:
    if length > len(symbols):
        raise ValueError("Gizli kod için yeterli renk yok.")
    return tuple(random.sample(list(symbols), length))


def print_history(entries: List[Tuple[str, Sequence[str], int, int]]) -> None:
    if not entries:
        return
    print("\nTahmin tablosu:")
    print("No | Oyuncu        | Tahmin            | Tam | Renk")
    print("-- | ------------- | ----------------- | --- | ----")
    for idx, (player, guess, exact, color_only) in enumerate(entries, 1):
        guess_str = pretty(guess)
        print(
            f"{idx:>2} | {player:<13} | {guess_str:<17} | {exact:^3} | {color_only:^4}"
        )


def ask_player_name(default_label: str) -> str:
    raw = input(f"{default_label} adı ({default_label}): ").strip()
    return raw or default_label


def prompt_secret(owner_name: str, length: int, symbols: List[str]) -> Tuple[str, ...]:
    while True:
        raw = input(f"{owner_name}, gizli kodunu gir: ").strip()
        try:
            return tuple(parse_guess(raw, length, symbols))
        except Exception as e:
            print("Hata:", e)

# -------------------------------
# AI Çözücü
# -------------------------------

class Solver:
    def __init__(self, length: int, symbols: List[str]):
        self.length = length
        self.symbols = symbols
        self.candidates = all_codes(length, symbols)  # Tüm olasılıklar
        self.last_guess: Tuple[str, ...] | None = None

    def next_guess(self) -> Tuple[str, ...]:
        # Basit strateji: adayların ortasından biri (rastgele daha az tekdüze hissettirir)
        # İstersen Knuth 5-adım algoritmasına yakın iyileştirmeler eklenebilir.
        if not self.candidates:
            # Güvenlik: teoride boşalmamalı
            g = generate_secret(self.length, self.symbols)
        else:
            g = random.choice(self.candidates)
        self.last_guess = g
        return g

    def apply_feedback(self, guess: Sequence[str], fb: Tuple[int, int]) -> None:
        ex, co = fb
        new_cands = []
        for c in self.candidates:
            if feedback(c, guess) == (ex, co):
                new_cands.append(c)
        self.candidates = new_cands

# -------------------------------
# Oyun Modları
# -------------------------------

def mode_player_guesses(length: int, symbols: List[str], max_attempts: int) -> None:
    secret = generate_secret(length, symbols)
    print("\n=== Oyuncu vs Yapay Zekâ ===")
    print("Yapay zekâ gizli kodu belirledi. Aşağıdaki harfleri kullanabilirsin:")
    print("  " + palette_description(symbols))
    print("Her renk yalnızca bir kez kullanılabilir.")

    history: List[Tuple[str, Sequence[str], int, int]] = []

    for attempt in range(1, max_attempts + 1):
        print(f"\nDeneme {attempt}/{max_attempts}")
        raw = input("Tahminini gir: ").strip()
        try:
            g_list = parse_guess(raw, length, symbols)
        except Exception as e:
            print("Hata:", e)
            continue
        guess = tuple(g_list)
        ex, co = feedback(secret, guess)
        history.append(("Sen", guess, ex, co))
        print_history(history)
        if ex == length:
            print(f"\n✅ Tebrikler! {attempt}. denemede kodu çözdün.")
            return
        print("İpuçları: Tam = doğru renk + konum, Renk = doğru renk yanlış konum")

    print(f"\n❌ Deneme hakkın bitti. Gizli kod: {pretty(secret)}")

def mode_ai_guesses(length: int, symbols: List[str], max_attempts: int) -> None:
    print("\n=== Yapay Zekâ Senin Kodunu Bulmaya Çalışıyor ===")
    print("Renk harfleri:")
    print("  " + palette_description(symbols))
    print("Her rengi en fazla bir kez kullan.")
    while True:
        raw = input("Gizli kodunu gir (örn. RGBY): ").strip()
        try:
            secret = tuple(parse_guess(raw, length, symbols))
            break
        except Exception as e:
            print("Hata:", e)

    solver = Solver(length, symbols)
    history: List[Tuple[str, Sequence[str], int, int]] = []
    for attempt in range(1, max_attempts+1):
        guess = solver.next_guess()
        print(f"\n[{attempt}/{max_attempts}] Yapay zekâ tahmini: {pretty(guess)}")
        ex, co = feedback(secret, guess)
        history.append(("Yapay zekâ", guess, ex, co))
        print_history(history)
        print(f"Son ipucu → Tam: {ex}, Renk: {co}")
        if ex == length:
            print(f"\n🤖 Yapay zekâ {attempt}. denemede gizli kodu buldu!")
            return
        solver.apply_feedback(guess, (ex, co))

    print("\n🤖 Yapay zekâ deneme hakkını bitirdi. Gizli kodu bulamadı!")

def mode_versus(length: int, symbols: List[str], max_attempts: int) -> None:
    print("\n=== Oyuncu vs Yapay Zekâ: Düello ===")
    print("Her iki taraf da kendi gizli kodunu belirler.")
    print("Renk harfleri: " + palette_description(symbols))

    while True:
        raw = input("Gizli kodunu gir (örn. RGBY): ").strip()
        try:
            player_secret = tuple(parse_guess(raw, length, symbols))
            break
        except Exception as e:
            print("Hata:", e)

    ai_secret = generate_secret(length, symbols)

    solver = Solver(length, symbols)
    history: List[Tuple[str, Sequence[str], int, int]] = []

    for round_idx in range(1, max_attempts + 1):
        print(f"\n--- {round_idx}. Tur ---")

        while True:
            raw = input("Tahminin (Yapay zekânın kodu): ").strip()
            try:
                g_list = parse_guess(raw, length, symbols)
                break
            except Exception as e:
                print("Hata:", e)
        player_guess = tuple(g_list)
        ex, co = feedback(ai_secret, player_guess)
        history.append(("Sen", player_guess, ex, co))
        print_history(history)
        if ex == length:
            print(f"\n🏆 Tebrikler! Yapay zekânın kodunu {round_idx}. turda çözdün.")
            print(f"Yapay zekâ kodu: {pretty(ai_secret)}")
            return

        ai_guess = solver.next_guess()
        ex_ai, co_ai = feedback(player_secret, ai_guess)
        history.append(("Yapay zekâ", ai_guess, ex_ai, co_ai))
        print_history(history)
        if ex_ai == length:
            print(f"\n🤖 Yapay zekâ kazandı! Senin gizli kodun: {pretty(player_secret)}")
            return
        solver.apply_feedback(ai_guess, (ex_ai, co_ai))

    print("\nBerabere! Kimse gizli kodu çözemedi.")
    print(f"Yapay zekâ kodu: {pretty(ai_secret)} | Senin kodun: {pretty(player_secret)}")


def mode_pvp_duel(length: int, symbols: List[str], max_attempts: int) -> None:
    print("\n=== Oyuncu vs Oyuncu: Düello ===")
    print("Her oyuncu kendi gizli kodunu belirler ve rakibinin kodunu çözmeye çalışır.")
    print("Kullanılabilecek harfler: " + palette_description(symbols))
    print("Her renk yalnızca bir kez kullanılmalıdır.")

    player1 = ask_player_name("1. Oyuncu")
    player2 = ask_player_name("2. Oyuncu")

    print(f"\n{player1}, gizli kodunu girerken {player2} lütfen bakma!")
    secret1 = prompt_secret(player1, length, symbols)
    print(f"\n{player2}, şimdi sıra sende. {player1} lütfen bakma!")
    secret2 = prompt_secret(player2, length, symbols)

    players = [
        (player1, player2, secret2),
        (player2, player1, secret1),
    ]
    history: List[Tuple[str, Sequence[str], int, int]] = []

    for round_idx in range(1, max_attempts + 1):
        print(f"\n--- {round_idx}. Tur ---")
        for active, opponent, opponent_secret in players:
            while True:
                raw = input(f"{active} tahmini ({opponent}'nin kodu): ").strip()
                try:
                    guess_list = parse_guess(raw, length, symbols)
                    break
                except Exception as e:
                    print("Hata:", e)
            guess = tuple(guess_list)
            ex, co = feedback(opponent_secret, guess)
            history.append((active, guess, ex, co))
            print_history(history)
            if ex == length:
                print(f"\n🎉 {active} {round_idx}. turda kazandı!")
                print(
                    f"{player1} kodu: {pretty(secret1)} | {player2} kodu: {pretty(secret2)}"
                )
                return

    print("\nBerabere! Kimse rakibinin kodunu çözmedi.")
    print(f"{player1} kodu: {pretty(secret1)} | {player2} kodu: {pretty(secret2)}")


def mode_pvp_one_by_one(length: int, symbols: List[str], max_attempts: int) -> None:
    print("\n=== Oyuncu vs Oyuncu: Tek Tek Tahmin ===")
    print("Yapay zekâ rastgele bir gizli kod belirler, oyuncular sırayla tahmin eder.")
    print("Harfler: " + palette_description(symbols))
    print(f"Her oyuncunun {max_attempts} tahmin hakkı vardır.")

    player1 = ask_player_name("1. Oyuncu")
    player2 = ask_player_name("2. Oyuncu")
    players = [player1, player2]

    secret = generate_secret(length, symbols)
    history: List[Tuple[str, Sequence[str], int, int]] = []
    total_turns = max_attempts * len(players)
    current_index = 0

    for turn in range(1, total_turns + 1):
        active = players[current_index]
        print(f"\n{turn}. hamle — {active}")
        while True:
            raw = input("Tahminin: ").strip()
            try:
                guess_list = parse_guess(raw, length, symbols)
                break
            except Exception as e:
                print("Hata:", e)
        guess = tuple(guess_list)
        ex, co = feedback(secret, guess)
        history.append((active, guess, ex, co))
        print_history(history)
        if ex == length:
            print(f"\n🎉 {active} gizli kodu buldu!")
            print(f"Gizli kod: {pretty(secret)}")
            return
        current_index = 1 - current_index

    print("\nTahmin hakları tükendi. Kimse gizli kodu bulamadı.")
    print(f"Gizli kod: {pretty(secret)}")

# -------------------------------
# Menü ve Başlat
# -------------------------------

def choose_int(prompt: str, lo: int, hi: int, default: int) -> int:
    while True:
        raw = input(f"{prompt} [{lo}-{hi}] (enter={default}): ").strip()
        if not raw:
            return default
        if raw.isdigit():
            v = int(raw)
            if lo <= v <= hi:
                return v
        print(f"Lütfen {lo} ile {hi} arasında bir sayı gir.")

def main() -> None:
    print("=== Renk Kodu: Mastermind Tarzı ===")
    print("Hoş geldin! Kod uzunluğunu ve renk sayısını seç, ardından oyun modunu belirle.")

    color_count = choose_int("Renk sayısı (6 veya 8)", 6, 8, 6)
    if color_count not in (6, 8):
        print("Sadece 6 veya 8 renk kullanılabilir. 6 seçildi.")
        color_count = 6
    symbols = PALETTES[color_count]

    max_length = min(6, color_count)
    default_length = 4 if max_length >= 4 else max_length
    length = choose_int("Kod uzunluğu", 3, max_length, default_length)
    if length > len(symbols):
        print(f"Kod uzunluğu renk sayısından büyük olamaz. Uzunluk {len(symbols)} olarak ayarlandı.")
        length = len(symbols)

    max_attempts = choose_int("Deneme sayısı", 6, 15, 10)

    print("\n--- Ayarlar ---")
    print(f"Kod uzunluğu : {length}")
    print(f"Renk sayısı  : {color_count}")
    print("Renk harfleri: " + palette_description(symbols))
    print(f"Deneme hakkı : {max_attempts}")
    print("Her renk yalnızca bir kez kullanılabilir.")

    print("\nOyun modları:")
    print("  1) Oyuncu vs Yapay Zekâ — gizli kodu yapay zekâ belirler, sen tahmin edersin")
    print("  2) Yapay Zekâ tahmin etsin — gizli kodu sen belirlersin")
    print("  3) Oyuncu vs Yapay Zekâ — iki taraf da gizli kod belirler")
    print("  4) Oyuncu vs Oyuncu")

    while True:
        m = input("Seçimin (1/2/3/4): ").strip()
        if m in ("1", "2", "3", "4"):
            break
        print("Geçersiz seçim.")

    if m == "1":
        mode_player_guesses(length, symbols, max_attempts)
        return
    if m == "2":
        mode_ai_guesses(length, symbols, max_attempts)
        return
    if m == "3":
        mode_versus(length, symbols, max_attempts)
        return

    print("\nOyuncu vs Oyuncu modunu seçtin.")
    print("  1) Düello — her oyuncu kendi gizli kodunu belirler")
    print("  2) Tek tek tahmin — ortak gizli kod, sırayla tahmin")
    while True:
        sub = input("Seçimin (1/2): ").strip()
        if sub in ("1", "2"):
            break
        print("Geçersiz seçim.")

    if sub == "1":
        mode_pvp_duel(length, symbols, max_attempts)
    else:
        mode_pvp_one_by_one(length, symbols, max_attempts)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nÇıkış yapıldı.")
