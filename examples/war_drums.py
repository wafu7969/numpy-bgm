"""示例 10 · 战鼓 —— 116 BPM，D 小调。

情绪：鼓声从远处逼近，最后铺满整个场地。大鼓、排鼓、军鼓、镲与锣层层叠加，
低音铜管只负责压住底盘；所有鼓点都落在十六分网格上，靠加花而不是提速推向高潮。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (Track, clap, crash, gong, hat, kick, lowpass, pad,
                       reverb, snare, supersaw, tom)

BPM = 116
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 28
DUR = BARS * BAR + 4.5

HORN = {
    "Dm": [50, 57, 62],
    "Bb": [46, 53, 58],
    "F": [41, 48, 53],
    "C": [48, 55, 60],
}
PROGRESSION = ["Dm", "Bb", "F", "C"] * 7

# (小节内第几拍, 鼓件, 力度)
GROOVE = [
    (0.00, "big", 0.55), (0.50, "low", 0.34), (1.00, "clap", 0.24),
    (1.00, "high", 0.28), (1.50, "mid", 0.30), (2.00, "big", 0.50),
    (2.50, "low", 0.30), (3.00, "clap", 0.24), (3.00, "high", 0.28),
    (3.50, "mid", 0.30), (3.75, "high", 0.20),
]
GHOSTS = [
    (0.25, "high", 0.12), (0.75, "mid", 0.14), (1.25, "low", 0.13),
    (1.75, "high", 0.16), (2.25, "mid", 0.13), (2.75, "high", 0.15),
    (3.25, "low", 0.14),
]


def main(out: Path) -> Path:
    perc = Track(DUR)
    horn = Track(DUR)
    air = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    def hit(kind: str, bar: int, beat: float, gain: float, pan_: float = 0.0) -> None:
        table = {
            "big": lambda: kick(tune=40, dur=0.9),
            "low": lambda: tom(tune=73, dur=0.7),
            "mid": lambda: tom(tune=98, dur=0.55),
            "high": lambda: tom(tune=146, dur=0.40),
            "clap": clap,
            "snare": snare,
            "hat": hat,
        }
        perc.add(table[kind](), at(bar, beat), gain=gain, pan_=pan_)

    # ---------- 前奏：锣 + 大鼓，排鼓由远及近
    perc.add(gong(tune=72, dur=7.0), 0.0, gain=0.34, pan_=0.0)
    for bar in range(0, 4):
        hit("big", bar, 0.0, 0.60)
        hit("big", bar, 2.0, 0.48)
        if bar >= 2:
            hit("low", bar, 3.5, 0.30, pan_=-0.2)
            hit("high", bar, 3.75, 0.22, pan_=0.25)

    # ---------- 主段：第 5 小节进入完整节奏
    for bar in range(4, 12):
        for beat, kind, gain in GROOVE:
            hit(kind, bar, beat, gain, pan_=-0.15 if kind in ("low", "mid") else 0.15)
        for i in range(8):
            hit("hat", bar, i * 0.5, 0.030 if i % 2 == 0 else 0.020, pan_=0.3)

    # ---------- 高潮：加十六分加花、齐奏与镲
    for bar in range(12, 24):
        for beat, kind, gain in GROOVE:
            hit(kind, bar, beat, gain * 1.1,
                pan_=-0.18 if kind in ("low", "mid") else 0.18)
        for beat, kind, gain in GHOSTS:
            hit(kind, bar, beat, gain, pan_=0.3 if kind == "high" else -0.3)
        for i in range(16):
            hit("hat", bar, i * 0.25, 0.018 if i % 4 == 0 else 0.009, pan_=0.35)
        if bar % 2 == 0:
            perc.add(crash(dur=1.5), at(bar), gain=0.13, pan_=0.0)
        if bar in (12, 20):
            perc.add(gong(tune=80, dur=6.0), at(bar), gain=0.24, pan_=0.0)

    # ---------- 军鼓滚奏：把每一段推向下一段
    for bar in (7, 11, 19, 23):
        for k in range(8):
            hit("snare", bar, 2 + k * 0.25, 0.05 + 0.012 * k, pan_=0.1)

    # ---------- 低音铜管：整小节长音，压住底盘
    for bar, name in enumerate(PROGRESSION):
        if bar < 8:
            continue
        for j, m in enumerate(HORN[name]):
            horn.add(supersaw(hz(m), BAR * 0.92, voices=3, detune=0.004,
                              cutoff=760 if bar < 12 else 900),
                     at(bar), gain=0.075, pan_=(-0.2 + 0.2 * j))

    # ---------- 持续低音与铺底
    n = int(DUR * 44100)
    t = np.arange(n) / 44100
    breath = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t - 1.1)
    for m, level in ((38, 0.14), (45, 0.07)):
        air.add(np.sin(2 * np.pi * hz(m) * t) * breath, 0.0, gain=level, pan_=0.0)
    for bar, name in enumerate(PROGRESSION):
        for m in HORN[name]:
            air.add(pad(hz(m - 12), BAR * 1.2, voices=2, cutoff=520,
                        attack=0.6, detune=0.004),
                    at(bar), gain=0.030, pan_=0.0)

    # ---------- 收尾：三下重击 + 滚奏 + 锣
    for bar in (24, 25):
        hit("big", bar, 0.0, 0.60)
        hit("big", bar, 2.0, 0.46)
        hit("low", bar, 3.0, 0.32)
    for k in range(16):
        hit("snare", 26, k * 0.25, 0.06 + 0.010 * k, pan_=0.15)
    for k in range(8):
        hit("big", 26, 2 + k * 0.25, 0.18 + 0.03 * k)
    perc.add(crash(dur=2.4), at(27), gain=0.20, pan_=0.0)
    perc.add(gong(tune=70, dur=8.0), at(27), gain=0.34, pan_=0.0)
    hit("big", 27, 0.0, 0.66)
    for m in HORN["Dm"]:
        horn.add(supersaw(hz(m - 12), 4.5, voices=3, cutoff=800), at(27),
                 gain=0.09, pan_=0.0)

    # ---------- 总线：鼓组给一点厅堂感，铜管留在中间
    mix = (reverb(perc.buf, dur=2.0, mix=0.16, damp=5200)
           + reverb(horn.buf, dur=2.8, mix=0.30, damp=3000)
           + air.buf)
    mix = lowpass(mix, 15000)
    return render(out / "10_war_drums.wav", mix, fade=(0.01, 2.4), drive=0.18)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
