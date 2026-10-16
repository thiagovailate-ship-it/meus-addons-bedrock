#!/usr/bin/env python3
"""Synthesises every .ogg sound used by PALEOFRONTIER.

Pure procedural DSP (numpy + libsndfile via soundfile).  No external audio
files are referenced anywhere in the pack.

Usage:  python3 tools/gen_sounds.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content_model as cm  # noqa: E402
import soundfile as sf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "resource_pack", "sounds")
SR = 22050


def seed_rng(name):
    np.random.seed(abs(hash(name)) % (2 ** 31))


def t(duration):
    return np.arange(int(duration * SR)) / SR


def env_decay(n, attack=0.004, decay=0.3):
    x = np.arange(n) / SR
    a = np.clip(x / max(attack, 1e-4), 0, 1)
    d = np.exp(-x / max(decay, 1e-4))
    return a * d


def env_adsr(n, attack=0.01, decay=0.05, sustain=0.6, release=0.1, dur=None):
    x = np.arange(n) / SR
    total = dur or n / SR
    out = np.zeros(n)
    a_end = attack
    d_end = attack + decay
    r_start = max(total - release, d_end)
    out = np.where(x < a_end, x / max(a_end, 1e-4), out)
    out = np.where((x >= a_end) & (x < d_end),
                   1 - (1 - sustain) * (x - a_end) / max(decay, 1e-4), out)
    out = np.where((x >= d_end) & (x < r_start), sustain, out)
    out = np.where(x >= r_start, sustain * np.clip(1 - (x - r_start) / max(release, 1e-4), 0, 1), out)
    return out


def sine(freq, duration, vibrato=0.0, vib_rate=6.0, slide_to=None):
    n = int(duration * SR)
    x = t(duration)
    if slide_to is not None:
        f = np.linspace(freq, slide_to, n)
        phase = 2 * np.pi * np.cumsum(f) / SR
    else:
        phase = 2 * np.pi * freq * x
    if vibrato:
        phase += vibrato * np.sin(2 * np.pi * vib_rate * x)
    return np.sin(phase)


def saw(freq, duration, slide_to=None, vibrato=0.0, vib_rate=6.0):
    n = int(duration * SR)
    if slide_to is not None:
        f = np.linspace(freq, slide_to, n)
    else:
        f = np.full(n, freq)
    x = t(duration)
    phase = np.cumsum(f) / SR
    if vibrato:
        phase += vibrato * np.sin(2 * np.pi * vib_rate * x)
    return 2 * (phase - np.floor(phase + 0.5))


def noise(duration, colour=0.0):
    """colour 0 = white; >0 biases towards brown/pink via cumulative sum."""
    n = int(duration * SR)
    w = np.random.randn(n)
    if colour > 0:
        w = np.cumsum(w)
        w = w / (np.max(np.abs(w)) + 1e-9)
    return w


def _fft_apply(sig, mask_fn):
    n = len(sig)
    spec = np.fft.rfft(sig)
    freqs = np.fft.rfftfreq(n, 1.0 / SR)
    spec = spec * mask_fn(freqs)
    return np.fft.irfft(spec, n)


def lowpass(sig, cutoff):
    """4th-order Butterworth magnitude lowpass, vectorised via FFT."""
    return _fft_apply(sig, lambda f: 1.0 / (1.0 + (f / max(cutoff, 1.0)) ** 4))


def highpass(sig, cutoff):
    return _fft_apply(
        sig, lambda f: 1.0 / (1.0 + (cutoff / np.maximum(f, 1.0)) ** 4))


def bandpass(sig, centre, q=4.0):
    def mask(f):
        ff = np.maximum(f, 1.0)
        return 1.0 / (1.0 + (q * (ff / centre - centre / ff)) ** 2)
    return _fft_apply(sig, mask)


def mix(*tracks):
    n = max(len(x) for x in tracks)
    out = np.zeros(n)
    for x in tracks:
        out[: len(x)] += x
    return out


def pad(sig, total):
    out = np.zeros(int(total * SR))
    out[: len(sig)] = sig
    return out


def normalise(sig, peak=0.85):
    m = np.max(np.abs(sig))
    if m < 1e-9:
        return sig
    return sig * (peak / m)


def write_ogg(sig, name, duration=None):
    sig = normalise(sig)
    path = os.path.join(OUT, name + ".ogg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, sig.astype(np.float32), SR, format="OGG", subtype="VORBIS")
    return path


# ---------------------------------------------------------------------------
# recipes
# ---------------------------------------------------------------------------
def sediment(i):
    seed_rng(f"sediment{i}")
    d = 0.22 + 0.05 * i
    n = int(d * SR)
    body = lowpass(noise(d, colour=0.4), 900 + 200 * i) * env_decay(n, 0.002, 0.06)
    grit = highpass(noise(d), 2400) * env_decay(n, 0.001, 0.03) * 0.35
    thud = sine(90 + 12 * i, d, slide_to=52) * env_decay(n, 0.002, 0.09) * 0.5
    return mix(body, grit, thud)


def brush(i):
    seed_rng(f"brush{i}")
    d = 0.34
    n = int(d * SR)
    sw = bandpass(noise(d), 2600 + 700 * i, q=2.2) * env_adsr(n, 0.05, 0.08, 0.5, 0.14, d)
    tip = bandpass(noise(d), 5200, q=3.0) * env_decay(n, 0.004, 0.05) * 0.3
    return mix(sw, tip)


def discover():
    seed_rng("discover")
    notes = [523.25, 659.25, 783.99, 1046.5]
    tracks = []
    for k, f in enumerate(notes):
        d = 0.5
        n = int(d * SR)
        sig = sine(f, d) * env_decay(n, 0.004, 0.16) * 0.5
        sig = np.roll(sig, int(k * 0.07 * SR))
        tracks.append(pad(sig, 1.2))
    shimmer = highpass(noise(1.0), 6000) * env_decay(int(1.0 * SR), 0.01, 0.3) * 0.12
    return mix(*tracks, shimmer)


def discover_rare():
    seed_rng("discover_rare")
    tracks = []
    chord = [392.0, 523.25, 659.25, 783.99, 987.77]
    for k, f in enumerate(chord):
        d = 0.9
        n = int(d * SR)
        sig = (sine(f, d, vibrato=0.02) + 0.3 * sine(f * 2, d)) * env_decay(n, 0.006, 0.34) * 0.32
        sig = np.roll(sig, int(k * 0.05 * SR))
        tracks.append(pad(sig, 1.7))
    sub = sine(60, 1.5, slide_to=38) * env_decay(int(1.5 * SR), 0.01, 0.6) * 0.4
    shimmer = highpass(noise(1.4), 5200) * env_decay(int(1.4 * SR), 0.02, 0.5) * 0.14
    return mix(*tracks, sub, shimmer)


def scan_ping():
    seed_rng("scan_ping")
    d = 0.34
    n = int(d * SR)
    blip = sine(620, d, slide_to=1480) * env_adsr(n, 0.006, 0.03, 0.5, 0.14, d) * 0.7
    echo = blip * 0.35
    echo = np.roll(echo, int(0.09 * SR))
    return mix(blip, pad(echo, 0.5))


def scan_strong():
    seed_rng("scan_strong")
    d = 0.22
    a = sine(700, d, slide_to=1650) * env_adsr(int(d * SR), 0.005, 0.02, 0.6, 0.08, d) * 0.7
    b = np.roll(a * 0.9, int(0.16 * SR))
    sub = sine(120, 0.5, slide_to=70) * env_decay(int(0.5 * SR), 0.004, 0.18) * 0.35
    return mix(pad(a, 0.6), pad(b, 0.6), sub)


def scan_empty():
    seed_rng("scan_empty")
    d = 0.3
    return sine(520, d, slide_to=240) * env_adsr(int(d * SR), 0.006, 0.04, 0.4, 0.14, d) * 0.6


def lab_process():
    seed_rng("lab_process")
    d = 1.15
    n = int(d * SR)
    whir = lowpass(saw(74, d), 700) * env_adsr(n, 0.08, 0.1, 0.55, 0.35, d) * 0.45
    hum = sine(148, d, vibrato=0.05, vib_rate=9) * env_adsr(n, 0.05, 0.1, 0.4, 0.3, d) * 0.2
    ticks = []
    for k in range(7):
        td = 0.05
        tk = bandpass(noise(td), 3200, q=6) * env_decay(int(td * SR), 0.001, 0.012) * 0.5
        ticks.append(pad(np.roll(tk, int((0.12 + k * 0.14) * SR)), d))
    hiss = bandpass(noise(d), 4200, q=1.6) * env_adsr(n, 0.3, 0.2, 0.25, 0.4, d) * 0.16
    return mix(whir, hum, hiss, *ticks)


def lab_identify():
    seed_rng("lab_identify")
    d1 = 0.22
    a = sine(880, d1) * env_decay(int(d1 * SR), 0.004, 0.09) * 0.55
    b = np.roll(sine(1318.5, 0.3) * env_decay(int(0.3 * SR), 0.004, 0.12) * 0.5, int(0.14 * SR))
    click = bandpass(noise(0.05), 2600, q=5) * env_decay(int(0.05 * SR), 0.001, 0.01) * 0.4
    return mix(pad(a, 0.6), pad(b, 0.6), click)


def lab_deny():
    seed_rng("lab_deny")
    d = 0.34
    n = int(d * SR)
    buzz = lowpass(saw(150, d, slide_to=96), 900) * env_adsr(n, 0.004, 0.03, 0.6, 0.12, d) * 0.6
    return buzz


def bench_open():
    seed_rng("bench_open")
    d = 0.5
    n = int(d * SR)
    creak = bandpass(saw(180, d, slide_to=260), 620, q=3) * env_adsr(n, 0.06, 0.1, 0.4, 0.2, d) * 0.35
    latch = bandpass(noise(0.06), 1800, q=4) * env_decay(int(0.06 * SR), 0.001, 0.014) * 0.6
    wood = sine(140, 0.25, slide_to=90) * env_decay(int(0.25 * SR), 0.002, 0.07) * 0.3
    return mix(creak, latch, pad(wood, 0.5))


def incu_start():
    seed_rng("incu_start")
    d = 0.9
    n = int(d * SR)
    hum = sine(96, d, vibrato=0.06, vib_rate=4) * env_adsr(n, 0.25, 0.1, 0.7, 0.4, d) * 0.45
    bubble = []
    for k, f in enumerate((420, 560, 700)):
        bd = 0.12
        b = sine(f, bd, slide_to=f * 1.8) * env_decay(int(bd * SR), 0.003, 0.04) * 0.3
        bubble.append(pad(np.roll(b, int((0.3 + k * 0.12) * SR)), d))
    return mix(hum, *bubble)


def incu_progress():
    seed_rng("incu_progress")
    d = 0.42
    tracks = []
    for k, f in enumerate((300, 430)):
        bd = 0.1
        b = sine(f, bd, slide_to=f * 1.5) * env_decay(int(bd * SR), 0.003, 0.035) * 0.35
        tracks.append(pad(np.roll(b, int(k * 0.13 * SR)), d))
    hum = sine(96, d) * env_adsr(int(d * SR), 0.05, 0.05, 0.35, 0.2, d) * 0.18
    return mix(*tracks, hum)


def incu_hatch():
    seed_rng("incu_hatch")
    d = 1.4
    n = int(d * SR)
    cracks = []
    for k in range(4):
        cd = 0.07
        c = highpass(noise(cd), 1500) * env_decay(int(cd * SR), 0.001, 0.02) * 0.55
        cracks.append(pad(np.roll(c, int((0.05 + k * 0.1) * SR)), d))
    pop = bandpass(noise(0.12), 900, q=2) * env_decay(int(0.12 * SR), 0.002, 0.05) * 0.5
    pop = np.roll(pop, int(0.5 * SR))
    chirp = []
    for k, f in enumerate((1180, 1420, 1660)):
        cd = 0.16
        c = sine(f, cd, vibrato=0.08) * env_decay(int(cd * SR), 0.006, 0.06) * 0.3
        chirp.append(pad(np.roll(c, int((0.68 + k * 0.14) * SR)), d))
    shimmer = highpass(noise(1.2), 5000) * env_decay(int(1.2 * SR), 0.02, 0.4) * 0.1
    return mix(*cracks, pad(pop, d), *chirp, shimmer)


def compy_idle(i):
    seed_rng(f"compy_idle{i}")
    d = 0.26
    n = int(d * SR)
    base = 1450 + 260 * i
    sig = sine(base, d, slide_to=base * 1.35, vibrato=0.05, vib_rate=22) * env_adsr(n, 0.01, 0.03, 0.5, 0.1, d)
    sig += 0.4 * sine(base * 2, d, slide_to=base * 2.6) * env_adsr(n, 0.01, 0.03, 0.35, 0.1, d)
    return sig * 0.7


def compy_hurt():
    seed_rng("compy_hurt")
    d = 0.22
    n = int(d * SR)
    return (sine(1900, d, slide_to=1200, vibrato=0.09, vib_rate=30) * env_adsr(n, 0.004, 0.02, 0.6, 0.08, d)) * 0.8


def compy_death():
    seed_rng("compy_death")
    d = 0.5
    n = int(d * SR)
    a = sine(1700, d, slide_to=520, vibrato=0.07, vib_rate=26) * env_adsr(n, 0.006, 0.06, 0.5, 0.2, d)
    b = 0.3 * sine(2550, d, slide_to=780) * env_adsr(n, 0.006, 0.06, 0.3, 0.2, d)
    return (a + b) * 0.8


def compy_step(i):
    seed_rng(f"compy_step{i}")
    d = 0.07
    n = int(d * SR)
    return lowpass(noise(d), 700 + 150 * i) * env_decay(n, 0.001, 0.02) * 0.5


def trike_idle(i):
    seed_rng(f"trike_idle{i}")
    d = 0.85
    n = int(d * SR)
    f = 96 + 14 * i
    body = lowpass(saw(f, d, vibrato=0.06, vib_rate=5), 520) * env_adsr(n, 0.12, 0.1, 0.6, 0.35, d)
    form = bandpass(saw(f * 1.01, d), 340, q=6) * env_adsr(n, 0.12, 0.1, 0.4, 0.35, d) * 0.7
    breath = bandpass(noise(d), 700, q=1.4) * env_adsr(n, 0.2, 0.15, 0.2, 0.4, d) * 0.2
    return (body + form + breath) * 0.7


def trike_hurt():
    seed_rng("trike_hurt")
    d = 0.5
    n = int(d * SR)
    body = lowpass(saw(150, d, slide_to=110), 800) * env_adsr(n, 0.02, 0.05, 0.7, 0.2, d)
    form = bandpass(saw(152, d), 460, q=5) * env_adsr(n, 0.02, 0.05, 0.5, 0.2, d) * 0.8
    return (body + form) * 0.8


def trike_death():
    seed_rng("trike_death")
    d = 1.2
    n = int(d * SR)
    body = lowpass(saw(130, d, slide_to=54), 700) * env_adsr(n, 0.04, 0.1, 0.6, 0.5, d)
    form = bandpass(saw(132, d, slide_to=56), 380, q=5) * env_adsr(n, 0.04, 0.1, 0.4, 0.5, d) * 0.7
    breath = bandpass(noise(d), 600, q=1.3) * env_adsr(n, 0.3, 0.2, 0.2, 0.6, d) * 0.25
    return (body + form + breath) * 0.8


def trike_step(i):
    seed_rng(f"trike_step{i}")
    d = 0.16
    n = int(d * SR)
    thud = sine(72 + 8 * i, d, slide_to=40) * env_decay(n, 0.002, 0.05)
    dirt = lowpass(noise(d), 500) * env_decay(n, 0.001, 0.03) * 0.4
    return (thud + dirt) * 0.9


def trike_angry():
    seed_rng("trike_angry")
    d = 0.7
    n = int(d * SR)
    huff = bandpass(noise(d), 500, q=1.6) * env_adsr(n, 0.03, 0.06, 0.5, 0.25, d) * 0.5
    snort = lowpass(saw(88, d, slide_to=70), 420) * env_adsr(n, 0.02, 0.06, 0.6, 0.3, d) * 0.7
    stomp = sine(58, 0.2, slide_to=34) * env_decay(int(0.2 * SR), 0.002, 0.06) * 0.6
    return mix(huff + snort, pad(stomp, d))


def raptor_idle(i):
    seed_rng(f"raptor_idle{i}")
    d = 0.6
    n = int(d * SR)
    f = 240 + 60 * i
    growl = lowpass(saw(f, d, vibrato=0.05, vib_rate=14), 900) * env_adsr(n, 0.05, 0.08, 0.5, 0.25, d)
    hiss = bandpass(noise(d), 3400, q=1.8) * env_adsr(n, 0.1, 0.1, 0.2, 0.3, d) * 0.25
    click = bandpass(noise(0.05), 1600, q=6) * env_decay(int(0.05 * SR), 0.001, 0.012) * 0.5
    return mix(growl + hiss, pad(click, d)) * 0.8


def raptor_hurt():
    seed_rng("raptor_hurt")
    d = 0.34
    n = int(d * SR)
    return (lowpass(saw(520, d, slide_to=330), 1800) * env_adsr(n, 0.006, 0.04, 0.7, 0.12, d)
            + 0.3 * bandpass(noise(d), 2600, q=2) * env_decay(n, 0.002, 0.06)) * 0.85


def raptor_death():
    seed_rng("raptor_death")
    d = 0.8
    n = int(d * SR)
    shriek = lowpass(saw(700, d, slide_to=180), 2400) * env_adsr(n, 0.01, 0.08, 0.55, 0.3, d)
    breath = bandpass(noise(d), 1800, q=1.5) * env_adsr(n, 0.2, 0.15, 0.2, 0.4, d) * 0.3
    return (shriek + breath) * 0.85


def raptor_step(i):
    seed_rng(f"raptor_step{i}")
    d = 0.1
    n = int(d * SR)
    tap = bandpass(noise(d), 1400 + 300 * i, q=3) * env_decay(n, 0.001, 0.022)
    low = sine(120, d, slide_to=80) * env_decay(n, 0.001, 0.03) * 0.5
    return (tap + low) * 0.7


def raptor_screech():
    seed_rng("raptor_screech")
    d = 0.7
    n = int(d * SR)
    scream = lowpass(saw(1500, d, slide_to=620, vibrato=0.06, vib_rate=18), 4200) * env_adsr(n, 0.02, 0.06, 0.7, 0.25, d)
    layer = lowpass(saw(1510, d, slide_to=630), 3000) * env_adsr(n, 0.02, 0.06, 0.4, 0.25, d) * 0.6
    hiss = bandpass(noise(d), 4200, q=1.6) * env_adsr(n, 0.05, 0.08, 0.25, 0.3, d) * 0.3
    return (scream + layer + hiss) * 0.85


def rex_idle(i):
    seed_rng(f"rex_idle{i}")
    d = 1.2
    n = int(d * SR)
    f = 58 + 8 * i
    sub = sine(f * 0.5, d, vibrato=0.04, vib_rate=3.2) * env_adsr(n, 0.2, 0.15, 0.5, 0.5, d) * 0.7
    body = lowpass(saw(f, d, vibrato=0.05, vib_rate=4.4), 340) * env_adsr(n, 0.18, 0.15, 0.6, 0.5, d)
    rumble = lowpass(noise(d, colour=1.0), 180) * env_adsr(n, 0.25, 0.2, 0.4, 0.5, d) * 0.5
    return (sub + body + rumble) * 0.85


def rex_hurt():
    seed_rng("rex_hurt")
    d = 0.7
    n = int(d * SR)
    body = lowpass(saw(120, d, slide_to=84), 700) * env_adsr(n, 0.02, 0.06, 0.7, 0.28, d)
    bark = bandpass(saw(124, d), 420, q=4) * env_adsr(n, 0.02, 0.06, 0.45, 0.28, d) * 0.7
    return (body + bark) * 0.9


def rex_death():
    seed_rng("rex_death")
    d = 1.8
    n = int(d * SR)
    body = lowpass(saw(110, d, slide_to=36), 620) * env_adsr(n, 0.05, 0.15, 0.6, 0.8, d)
    form = bandpass(saw(112, d, slide_to=38), 320, q=4) * env_adsr(n, 0.05, 0.15, 0.4, 0.8, d) * 0.7
    breath = bandpass(noise(d, colour=0.6), 500, q=1.3) * env_adsr(n, 0.4, 0.3, 0.2, 0.8, d) * 0.3
    return (body + form + breath) * 0.85


def rex_step(i):
    seed_rng(f"rex_step{i}")
    d = 0.26
    n = int(d * SR)
    thud = sine(46 + 6 * i, d, slide_to=26) * env_decay(n, 0.003, 0.09)
    impact = lowpass(noise(d), 300) * env_decay(n, 0.001, 0.04) * 0.5
    return (thud + impact) * 1.0


def rex_roar():
    seed_rng("rex_roar")
    d = 1.8
    n = int(d * SR)
    sub = sine(34, d, slide_to=26, vibrato=0.05, vib_rate=5) * env_adsr(n, 0.12, 0.2, 0.8, 0.7, d) * 0.9
    body = lowpass(saw(72, d, slide_to=50, vibrato=0.06, vib_rate=6.5), 420) * env_adsr(n, 0.1, 0.18, 0.8, 0.7, d)
    form1 = bandpass(saw(74, d, slide_to=52), 300, q=5) * env_adsr(n, 0.1, 0.18, 0.5, 0.7, d) * 0.8
    form2 = bandpass(saw(76, d, slide_to=54), 760, q=6) * env_adsr(n, 0.14, 0.2, 0.3, 0.7, d) * 0.5
    breath = bandpass(noise(d, colour=0.7), 900, q=1.5) * env_adsr(n, 0.2, 0.25, 0.35, 0.8, d) * 0.35
    onset = bandpass(noise(0.16), 1400, q=1.2) * env_decay(int(0.16 * SR), 0.004, 0.06) * 0.5
    return mix(sub + body + form1 + form2 + breath, pad(onset, d)) * 0.9


def rex_bite():
    seed_rng("rex_bite")
    d = 0.3
    n = int(d * SR)
    chomp = bandpass(noise(0.09), 900, q=2.5) * env_decay(int(0.09 * SR), 0.001, 0.026)
    snap = highpass(noise(0.05), 2200) * env_decay(int(0.05 * SR), 0.001, 0.012) * 0.7
    thud = sine(90, 0.22, slide_to=48) * env_decay(int(0.22 * SR), 0.002, 0.07) * 0.7
    return mix(pad(chomp, d) + pad(snap, d), pad(thud, d))


BUILDERS = {
    "sediment1": lambda: sediment(0),
    "sediment2": lambda: sediment(1),
    "sediment3": lambda: sediment(2),
    "brush1": lambda: brush(0),
    "brush2": lambda: brush(1),
    "discover": discover,
    "discover_rare": discover_rare,
    "scan_ping": scan_ping,
    "scan_strong": scan_strong,
    "scan_empty": scan_empty,
    "lab_process": lab_process,
    "lab_identify": lab_identify,
    "lab_deny": lab_deny,
    "bench_open": bench_open,
    "incu_start": incu_start,
    "incu_progress": incu_progress,
    "incu_hatch": incu_hatch,
    "compy_idle1": lambda: compy_idle(0),
    "compy_idle2": lambda: compy_idle(1),
    "compy_hurt": compy_hurt,
    "compy_death": compy_death,
    "compy_step1": lambda: compy_step(0),
    "compy_step2": lambda: compy_step(1),
    "trike_idle1": lambda: trike_idle(0),
    "trike_idle2": lambda: trike_idle(1),
    "trike_hurt": trike_hurt,
    "trike_death": trike_death,
    "trike_step1": lambda: trike_step(0),
    "trike_step2": lambda: trike_step(1),
    "trike_angry": trike_angry,
    "raptor_idle1": lambda: raptor_idle(0),
    "raptor_idle2": lambda: raptor_idle(1),
    "raptor_hurt": raptor_hurt,
    "raptor_death": raptor_death,
    "raptor_step1": lambda: raptor_step(0),
    "raptor_step2": lambda: raptor_step(1),
    "raptor_screech": raptor_screech,
    "rex_idle1": lambda: rex_idle(0),
    "rex_idle2": lambda: rex_idle(1),
    "rex_hurt": rex_hurt,
    "rex_death": rex_death,
    "rex_step1": lambda: rex_step(0),
    "rex_step2": lambda: rex_step(1),
    "rex_roar": rex_roar,
    "rex_bite": rex_bite,
}


def main():
    wanted = set()
    for s in cm.SOUND_DEFS:
        for f in s["files"]:
            wanted.add(f)
    missing = wanted - set(BUILDERS)
    extra = set(BUILDERS) - wanted
    if missing or extra:
        raise SystemExit(f"sound table mismatch: missing={sorted(missing)} extra={sorted(extra)}")
    written = []
    for name, builder in sorted(BUILDERS.items()):
        sig = builder()
        folder = None
        for s in cm.SOUND_DEFS:
            if name in s["files"]:
                folder = s["id"].replace(".", "/")
                break
        path = write_ogg(sig, os.path.join(folder, name))
        written.append(path)
    total = sum(os.path.getsize(p) for p in written)
    print(f"[gen_sounds] wrote {len(written)} ogg files ({total/1024:.0f} KiB)")


if __name__ == "__main__":
    main()
