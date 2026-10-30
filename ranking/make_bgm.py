# 랭킹 릴스 배경음(자체 제작, 저작권 문제 없음)을 만든다: python3 ranking/make_bgm.py → ranking/bgm/*.m4a (각 8초)
# 01_경쾌(120 BPM 화음 뜯기) · 02_웅장(84 BPM 큰북 · 금관 느낌 화음) · 03_긴장(110 BPM 반복 저음 · 올라가는 소리) · 04_통통(128 BPM 마림바 느낌)
import numpy as np, subprocess, wave, pathlib, sys
SR = 44100; L = SR * 8
OUT = pathlib.Path(__file__).resolve().parent / 'bgm'
def note(m): return 440 * 2 ** ((m - 69) / 12)
def env(n, a=0.005, d=0.25): x = np.arange(n) / SR; return np.minimum(1, x / a) * np.exp(-x / d)
def mk(): return np.zeros(L)
def add(out, sig, st):
    s = int(st * SR); e = min(L, s + len(sig))
    if s < L: out[s:e] += sig[:e - s]
def noise(n, seed): return np.random.default_rng(seed).standard_normal(n)
def kick(out, st, amp=0.9):
    k = np.arange(int(0.35 * SR)) / SR; add(out, amp * np.sin(2 * np.pi * (50 + 90 * np.exp(-k * 30)) * k) * np.exp(-k * 8), st)
def snare(out, st, seed, amp=0.35): n = int(0.2 * SR); add(out, amp * noise(n, seed) * env(n, 0.001, 0.06), st)
def hat(out, st, seed, amp=0.08): n = int(0.05 * SR); add(out, amp * noise(n, seed) * env(n, 0.001, 0.015), st)
def tom(out, st, f=70, amp=1.0, d=0.5):
    n = int(1.0 * SR); x = np.arange(n) / SR
    add(out, amp * (np.sin(2 * np.pi * f * (1 + 0.6 * np.exp(-x * 12)) * x) * np.exp(-x / d) + 0.25 * noise(n, int(f * 7 + st * 10)) * np.exp(-x * 25)), st)
def saw(f, n, harm=12):
    x = np.arange(n) / SR; return sum(np.sin(2 * np.pi * f * k * x) / k for k in range(1, harm + 1)) * (2 / np.pi)
def finish(out, name):
    out = out / np.max(np.abs(out)) * 0.8; fade = int(0.6 * SR); out[-fade:] *= np.linspace(1, 0, fade)
    w = OUT / ('_' + name + '.wav')
    with wave.open(str(w), 'wb') as f: f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((out * 32767).astype(np.int16).tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(w), '-ac', '2', '-c:a', 'aac', '-b:a', '160k', str(OUT / (name + '.m4a'))], check=True); w.unlink()
    print(name + '.m4a')

def t01():  # 경쾌: 120 BPM, C G Am F
    out = mk(); beat = 0.5
    for b in range(16):
        st = b * beat; kick(out, st)
        if b % 2: snare(out, st, b)
        for h in (0, .5): hat(out, st + h * beat, 100 + b * 2 + int(h * 2))
    for bar, (bass, ch) in enumerate([(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]):
        for b in range(4):
            st = (bar * 4 + b) * beat; n = int(beat * SR); x = np.arange(n) / SR
            add(out, 0.175 * np.sign(np.sin(2 * np.pi * note(bass) * x)) * env(n, .005, .18), st)
            for j, m in enumerate(ch):
                for h in (0, .5):
                    nn = int(.3 * SR); xx = np.arange(nn) / SR
                    add(out, .12 * 2 / np.pi * np.arcsin(np.sin(2 * np.pi * note(m + 12) * xx)) * env(nn, .002, .12), st + h * beat + j * .012)
    finish(out, '01_경쾌')

def t02():  # 웅장: 84 BPM, Dm Bb F C, 큰북 + 금관 느낌 톱니파 화음 + 낮은 현 느낌 지속음
    out = mk(); beat = 60 / 84
    chords = [(38, [62, 65, 69]), (34, [62, 65, 70]), (41, [60, 65, 69]), (36, [60, 64, 67])]
    for i, (bass, ch) in enumerate(chords):
        st = i * 2 * beat; n = int(2 * beat * SR) + int(.3 * SR); x = np.arange(n) / SR
        swell = np.minimum(1, x / 0.35) * np.exp(-x / 2.5)
        pad = sum(saw(note(m), n, 10) for m in ch) / 3
        add(out, 0.35 * pad * swell, st)                                   # 금관 느낌 화음
        add(out, 0.30 * saw(note(bass), n, 6) * swell, st)                 # 저음
        add(out, 0.25 * saw(note(bass - 12), n, 4) * swell, st)
    for b in range(12):                                                  # 큰북: 박마다, 마디 첫 박은 더 크게
        st = b * beat; tom(out, st, 60 if b % 4 == 0 else 85, 1.2 if b % 4 == 0 else 0.6, 0.6 if b % 4 == 0 else 0.3)
        if b % 2 == 1: tom(out, st + beat / 2, 100, 0.35, 0.2)
    n = int(2.5 * SR); add(out, 0.18 * noise(n, 9) * env(n, 0.002, 0.45), 0)  # 첫 박 심벌
    finish(out, '02_웅장')

def t03():  # 긴장: 110 BPM, 16분음표 반복 저음 + 위로 올라가는 소리 + 심장 박동 킥
    out = mk(); beat = 60 / 110; s16 = beat / 4
    seq = [45, 45, 57, 45, 45, 55, 45, 53]
    for i in range(int(8 / s16)):
        n = int(s16 * SR); x = np.arange(n) / SR; m = seq[i % 8] + (2 if i >= 64 else 0)
        add(out, 0.25 * saw(note(m), n, 8) * env(n, .003, .07), i * s16)
    for b in range(int(8 / beat)):
        kick(out, b * beat, 0.8); kick(out, b * beat + 0.18, 0.4)
    x = np.arange(L) / SR; f = 300 * 2 ** (x / 8 * 2)
    add(out, 0.12 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (x / 8), 0)  # 올라가는 소리
    finish(out, '03_긴장')

def t04():  # 통통: 128 BPM, 마림바 느낌 선율, F C Dm Bb
    out = mk(); beat = 60 / 128
    def mar(m, st, amp=.3):
        n = int(.5 * SR); x = np.arange(n) / SR
        add(out, amp * (np.sin(2 * np.pi * note(m) * x) + .3 * np.sin(2 * np.pi * note(m) * 4 * x) * np.exp(-x * 30)) * env(n, .001, .14), st)
    mel = [77, 81, 84, 81, 79, 76, 72, 76, 74, 77, 81, 77, 70, 74, 77, 82]
    bass = [41, 36, 38, 34]
    for b in range(int(8 / beat)):
        st = b * beat; kick(out, st, .7)
        if b % 2: snare(out, st, 300 + b, .25)
        hat(out, st + beat / 2, 500 + b)
        mar(mel[b % 16], st); mar(mel[(b + 2) % 16] - 12, st + beat / 2, .18)
        n = int(beat * SR); xx = np.arange(n) / SR
        add(out, .3 * np.sin(2 * np.pi * note(bass[(b // 4) % 4]) * xx) * env(n, .005, .2), st)
    finish(out, '04_통통')

for f in (t01, t02, t03, t04): f()
