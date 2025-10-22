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
    6: ["R","G","B","Y","O","P"],             # Red, Green, Blue, Yellow, Orange, Purple
    8: ["R","G","B","Y","O","P","C","W"],     # + Cyan, White
}

COLOR_NAMES = {
    "R":"Red","G":"Green","B":"Blue","Y":"Yellow","O":"Orange","P":"Purple","C":"Cyan","W":"White"
}

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

def all_codes(length: int, symbols: List[str]) -> List[Tuple[str,...]]:
    return list(itertools.product(symbols, repeat=length))

def parse_guess(raw: str, length: int, allowed: List[str]) -> List[str]:
    s = (raw or "").strip().upper().replace(" ", "")
    if len(s) != length:
        raise ValueError(f"Girdi uzunluğu {length} olmalı.")
    if any(ch not in allowed for ch in s):
        raise ValueError(f"Sadece şu harfler kullanılabilir: {''.join(allowed)}")
    return list(s)

def pretty(code: Sequence[str]) -> str:
    return " ".join(code)

# -------------------------------
# AI Çözücü
# -------------------------------

class Solver:
    def __init__(self, length: int, symbols: List[str]):
        self.length = length
        self.symbols = symbols
        self.candidates = all_codes(length, symbols)  # Tüm olasılıklar
        self.last_guess: Tuple[str,...] | None = None

    def next_guess(self) -> Tuple[str,...]:
        # Basit strateji: adayların ortasından biri (rastgele daha az tekdüze hissettirir)
        # İstersen Knuth 5-adım algoritmasına yakın iyileştirmeler eklenebilir.
        if not self.candidates:
            # Güvenlik: teoride boşalmamalı
            g = tuple(random.choice(self.symbols) for _ in range(self.length))
        else:
            g = random.choice(self.candidates)
        self.last_guess = g
        return g

    def apply_feedback(self, guess: Sequence[str], fb: Tuple[int,int]) -> None:
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
    secret = tuple(random.choice(symbols) for _ in range(length))
    print(f"\nAI gizli kodu belirledi. Renkler: {''.join(symbols)}  | Uzunluk: {length}")
    # print("(debug) secret:", pretty(secret))  # İstersen aç

    for attempt in range(1, max_attempts+1):
        raw = input(f"[{attempt}/{max_attempts}] Tahminini gir: ").strip()
        try:
            g = parse_guess(raw, length, symbols)
        except Exception as e:
            print("Hata:", e)
            continue
        ex, co = feedback(secret, g)
        print(f"→ Geri Bildirim: {ex} tam, {co} renk")
        if ex == length:
            print(f"✅ Tebrikler! {attempt}. denemede buldun.")
            return
    print(f"❌ Deneme hakkın bitti. Gizli kod: {pretty(secret)}")

def mode_ai_guesses(length: int, symbols: List[str], max_attempts: int) -> None:
    print(f"\nSen gizli kodu belirle (görünmez, sadece sen bileceksin). Renkler: {''.join(symbols)} | Uzunluk: {length}")
    while True:
        raw = input("Gizli kodunu gir (örn. RGBY): ").strip()
        try:
            secret = tuple(parse_guess(raw, length, symbols))
            break
        except Exception as e:
            print("Hata:", e)

    solver = Solver(length, symbols)
    for attempt in range(1, max_attempts+1):
        guess = solver.next_guess()
        print(f"[{attempt}/{max_attempts}] AI tahmini: {pretty(guess)}")
        ex, co = feedback(secret, guess)
        print(f"→ AI için geri bildirim: {ex} tam, {co} renk")
        if ex == length:
            print(f"🤖 AI {attempt}. denemede buldu!")
            return
        solver.apply_feedback(guess, (ex, co))

    print("🤖 AI deneme hakkını bitirdi. Bulamadı!")

def mode_versus(length: int, symbols: List[str], max_attempts: int) -> None:
    # İki taraf da gizli belirler; sırayla tahmin eder. İlk bulan kazanır.
    print(f"\nKARŞILIKLI MOD — Renkler: {''.join(symbols)} | Uzunluk: {length}")
    # Oyuncu gizlisi
    while True:
        raw = input("Kendi gizlini gir (örn. RGBY): ").strip()
        try:
            player_secret = tuple(parse_guess(raw, length, symbols))
            break
        except Exception as e:
            print("Hata:", e)

    # AI gizlisi
    ai_secret = tuple(random.choice(symbols) for _ in range(length))
    # print("(debug) AI secret:", pretty(ai_secret))

    solver = Solver(length, symbols)

    for round_idx in range(1, max_attempts+1):
        print(f"\n--- TUR {round_idx} ---")

        # Oyuncu tahmini
        while True:
            raw = input("Senin tahminin: ").strip()
            try:
                g = tuple(parse_guess(raw, length, symbols))
                break
            except Exception as e:
                print("Hata:", e)
        ex, co = feedback(ai_secret, g)
        print(f"Sana geri bildirim: {ex} tam, {co} renk")
        if ex == length:
            print(f"🏆 Kazandın! AI'nın gizlisi: {pretty(ai_secret)}")
            return

        # AI tahmini
        ai_guess = solver.next_guess()
        print(f"🤖 AI tahmini: {pretty(ai_guess)}")
        ex_ai, co_ai = feedback(player_secret, ai_guess)
        print(f"AI'ya geri bildirim: {ex_ai} tam, {co_ai} renk")
        if ex_ai == length:
            print(f"🤖 AI kazandı! Senin gizlin: {pretty(player_secret)}")
            return
        solver.apply_feedback(ai_guess, (ex_ai, co_ai))

    print(f"Berabere! AI gizlisi: {pretty(ai_secret)} | Senin gizlin: {pretty(player_secret)}")

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
        print("Geçersiz giriş.")

def main() -> None:
    print("=== Renk Kodu: Yapay Zekâya Karşı (Mastermind) ===")
    length = choose_int("Kod uzunluğu", 3, 6, 4)
    color_count = choose_int("Renk sayısı (6 veya 8)", 6, 8, 6)
    if color_count not in (6,8):
        color_count = 6
    symbols = PALETTES[color_count]
    max_attempts = choose_int("Deneme sayısı", 6, 15, 10)

    print("\nMod Seç:")
    print("  1) Sen tahmin et (AI gizli belirler)")
    print("  2) AI tahmin etsin (sen gizli belirle)")
    print("  3) Karşılıklı (sıralı turlar)")
    while True:
        m = input("Seçimin (1/2/3): ").strip()
        if m in ("1","2","3"):
            break
        print("Geçersiz seçim.")

    if m == "1":
        mode_player_guesses(length, symbols, max_attempts)
    elif m == "2":
        mode_ai_guesses(length, symbols, max_attempts)
    else:
        mode_versus(length, symbols, max_attempts)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nÇıkış yapıldı.")
