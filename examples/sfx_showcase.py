"""示例 11 · 音效与配音展示 —— 28 种声音，每 1.7 秒一个。

包含鼓组、金属、自然声、电子声，以及用共振峰合成的五个元音（a/e/i/o/u）。
不是采样，全部由 numpy 现场算出来。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (SR, Track, adsr, bandpass, bell, bird, clap, gong, hat,
                       highpass, kick, lowpass, osc, reverb, samples, snare,
                       timeline, tom)

SLOT = 1.7
COUNT = 28
DUR = COUNT * SLOT + 3.0


def norm(x: np.ndarray) -> np.ndarray:
    return x / (np.max(np.abs(x)) + 1e-9)


def level(x: np.ndarray, target_rms: float = 0.18) -> np.ndarray:
    """按能量而不是峰值对齐响度，短促的音效才不会被长音压过去。"""
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    g = target_rms / rms
    peak = np.max(np.abs(x)) * g
    if peak > 0.98:
        g *= 0.98 / peak
    return x * g


def place(out: np.ndarray, audio: np.ndarray, at: float, gain: float = 1.0) -> np.ndarray:
    """把一段声音放到缓冲区指定秒数处（自动裁掉越界部分）。"""
    i = samples(at)
    chunk = audio[:len(out) - i] * gain
    out[i:i + len(chunk)] += chunk
    return out


def noise_burst(dur: float, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal(samples(dur))


def woodblock(dur: float = 0.16) -> np.ndarray:
    t = timeline(dur)
    x = np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.02)
    x += 0.5 * np.sin(2 * np.pi * 1500 * t) * np.exp(-t / 0.012)
    x += noise_burst(dur) * np.exp(-t / 0.004) * 0.4
    return norm(x)


def phone_ring(dur: float = 1.4) -> np.ndarray:
    t = timeline(dur)
    out = np.zeros_like(t)
    for start in (0.0, 0.62):
        i = samples(start)
        tt = t[:len(t) - i]
        gate = (np.sin(2 * np.pi * 9 * tt) > 0).astype(float)
        tone = np.sin(2 * np.pi * 950 * tt) + 0.7 * np.sin(2 * np.pi * 1400 * tt)
        out[i:] += (tone * gate * np.exp(-tt / 0.5))[:len(out) - i]
    return norm(out)


def doorbell() -> np.ndarray:
    dur = 1.8
    out = np.zeros(samples(dur))
    for m, start in ((84, 0.0), (79, 0.42)):
        place(out, bell(hz(m), 1.3), start, 0.8)
    return norm(out)


def heartbeat() -> np.ndarray:
    dur = 0.9
    out = np.zeros(samples(dur))
    for start in (0.0, 0.30):
        place(out, lowpass(kick(tune=36, dur=0.5), 140), start, 0.8)
    return norm(out)


def typewriter(dur: float = 1.4) -> np.ndarray:
    rng = np.random.default_rng(5)
    out = np.zeros(samples(dur))
    pos = 0.02
    while pos < dur - 0.12:
        click = highpass(noise_burst(0.03, int(pos * 1000)), 2400)
        click *= np.exp(-timeline(0.03) / 0.004)
        place(out, click, pos, 0.7)
        pos += rng.uniform(0.05, 0.15)
    place(out, bell(hz(96), 0.5), dur - 0.5, 0.35)
    return norm(out)


def coin() -> np.ndarray:
    dur = 0.9
    out = np.zeros(samples(dur))
    for m, start, gain in ((96, 0.0, 1.0), (103, 0.06, 0.7)):
        place(out, bell(hz(m), 0.8), start, gain)
    return norm(out)


def water_drop(dur: float = 0.5) -> np.ndarray:
    t = timeline(dur)
    f = 1500 * np.exp(-t / 0.05) + 380
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)
    x += noise_burst(dur) * np.exp(-t / 0.004) * 0.3
    return norm(x)


def bubble(dur: float = 0.4) -> np.ndarray:
    t = timeline(dur)
    f = 320 * np.exp(t / 0.18)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    return norm(x)


def laser(dur: float = 0.45) -> np.ndarray:
    t = timeline(dur)
    f = 2600 * np.exp(-t / 0.09) + 120
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * np.exp(-t / 0.13)
    return norm(x)


def riser(dur: float = 1.5) -> np.ndarray:
    t = timeline(dur)
    noise = highpass(noise_burst(dur, 11), 900) * 0.5
    f = 350 * np.exp(t / 0.55)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    return norm((noise + tone) * (t / dur) ** 2.2)


def siren(dur: float = 1.3) -> np.ndarray:
    t = timeline(dur)
    f = 780 + 320 * np.sin(2 * np.pi * 1.8 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = adsr(dur, a=0.05, d=0.1, s=0.9, r=0.2)
    return norm(x * env)


def wind(dur: float = 1.6) -> np.ndarray:
    t = timeline(dur)
    x = lowpass(highpass(noise_burst(dur, 13), 200), 900)
    return norm(x * np.sin(np.pi * t / dur) ** 2)


def rain(dur: float = 1.6) -> np.ndarray:
    t = timeline(dur)
    base = bandpass(noise_burst(dur, 17), 1200, 8000)
    drops = np.zeros_like(base)
    rng = np.random.default_rng(19)
    for _ in range(40):
        i = int(rng.integers(0, len(base) - 3000))
        drops[i:i + 3000] += noise_burst(3000 / SR, int(i)) * np.exp(-np.arange(3000) / 400) * 0.5
    x = base * 0.35 + drops
    return norm(x * np.sin(np.pi * t / dur) ** 2)


def wave(dur: float = 1.7) -> np.ndarray:
    t = timeline(dur)
    x = lowpass(noise_burst(dur, 23), 700)
    env = np.sin(np.pi * t / dur) ** 2
    return norm(x * env)


def explosion(dur: float = 1.6) -> np.ndarray:
    t = timeline(dur)
    boom = np.sin(2 * np.pi * np.cumsum(48 + 60 * np.exp(-t / 0.05)) / SR)
    boom *= np.exp(-t / 0.45)
    rumble = lowpass(noise_burst(dur, 29), 500) * np.exp(-t / 0.35)
    click = noise_burst(dur, 31) * np.exp(-t / 0.01) * 0.6
    return norm(boom + rumble + click)


def engine(dur: float = 1.6) -> np.ndarray:
    t = timeline(dur)
    f = 52 + 4 * np.sin(2 * np.pi * 0.8 * t)
    x = lowpass(osc("saw", f, dur, harmonics=12), 320)
    x += 0.6 * np.sin(2 * np.pi * 104 * t)
    x *= 1.0 + 0.15 * np.sin(2 * np.pi * 22 * t)
    env = adsr(dur, a=0.15, d=0.1, s=0.9, r=0.3)
    return norm(x * env)


FORMANTS = {
    "a": ((800, 1.0), (1200, 0.55), (2500, 0.25)),
    "e": ((500, 1.0), (1800, 0.50), (2500, 0.25)),
    "i": ((300, 1.0), (2300, 0.45), (3000, 0.20)),
    "o": ((500, 1.0), (900, 0.60), (2400, 0.20)),
    "u": ((320, 1.0), (800, 0.50), (2300, 0.15)),
}


def vowel(name: str, f0: float = 132.0, dur: float = 1.2) -> np.ndarray:
    """共振峰合成的元音：锯齿波 + 三组带通，听起来像 a/e/i/o/u。"""
    t = timeline(dur)
    f = f0 * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t))
    src = osc("saw", f, dur, harmonics=40)
    out = np.zeros_like(src)
    for fc, amp in FORMANTS[name]:
        bw = max(90.0, fc * 0.12)
        out += amp * bandpass(src, fc - bw, fc + bw)
    env = adsr(dur, a=0.06, d=0.12, s=0.85, r=0.35)
    return norm(out * env)


def main(out: Path) -> Path:
    track = Track(DUR)

    items = [
        ("大鼓", kick(tune=42)),
        ("军鼓", snare()),
        ("踩镲", hat(open_=True, dur=0.35)),
        ("拍手", clap()),
        ("木鱼", woodblock()),
        ("锣", gong(tune=76, dur=2.2)),
        ("铃声", bell(hz(84), 1.4)),
        ("电话铃", phone_ring()),
        ("门铃", doorbell()),
        ("心跳", heartbeat()),
        ("打字机", typewriter()),
        ("硬币", coin()),
        ("水滴", water_drop()),
        ("泡泡", bubble()),
        ("激光", laser()),
        ("上升音", riser()),
        ("警笛", siren()),
        ("风声", wind()),
        ("雨声", rain()),
        ("海浪", wave()),
        ("爆炸", explosion()),
        ("引擎", engine()),
        ("鸟叫", bird(1400, 0.22, rise=1.9, seed=3)),
        ("配音 a", vowel("a")),
        ("配音 e", vowel("e")),
        ("配音 i", vowel("i")),
        ("配音 o", vowel("o")),
        ("配音 u", vowel("u")),
    ]

    for i, (name, audio) in enumerate(items):
        pan = (-0.35, 0.35, 0.0)[i % 3]
        track.add(level(audio), at=i * SLOT, pan_=pan)

    mix = reverb(track.buf, dur=1.6, mix=0.10, damp=6000)
    return render(out / "11_sfx_showcase.wav", mix, fade=(0.01, 1.5))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
