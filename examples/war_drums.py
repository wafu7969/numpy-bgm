"""示例 10 · 战鼓 —— 116 BPM，D 小调。

写法刻意避开架子鼓的语法：没有四拍底鼓、没有军鼓反拍、没有连续踩镲。
大鼓、中鼓、小鼓按 D–G–D 调音，用轮流呼应、齐奏、鼓边与滚奏推进，
像一支鼓队从远处走近，而不是一个人在打鼓。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (Track, bandpass, crash, gong, lowpass, pad, reverb, swirl,
                       taiko, timeline)

BPM = 116
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 28
DUR = BARS * BAR + 4.5

# 三面鼓按 D–G–D 调音，形成低、中、高三个声部
TUNE = {"big": 73.0, "mid": 98.0, "high": 147.0}
DECAY = {"big": 0.95, "mid": 0.6, "high": 0.35}

CHORDS = {
    "Dm": [50, 57, 62],
    "Bb": [46, 53, 58],
    "F": [41, 48, 53],
    "C": [48, 55, 60],
}
PROGRESSION = ["Dm", "Bb", "F", "C"] * 7

# 主节奏：三面鼓轮流说话，重音在 1、2.75、3.5
MAIN = [
    (0.00, "big", 0.72), (0.75, "mid", 0.34), (1.25, "high", 0.24),
    (1.50, "big", 0.52), (2.00, "big", 0.62), (2.75, "mid", 0.36),
    (3.00, "high", 0.26), (3.50, "big", 0.48),
]
RIM = [(1.00, 0.12), (3.00, 0.10)]


def main(out: Path) -> Path:
    drums = Track(DUR)
    air = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    def hit(kind: str, bar: int, beat: float, gain: float, pan_: float = 0.0) -> None:
        drums.add(taiko(TUNE[kind], dur=DECAY[kind] * 3.2, decay=DECAY[kind],
                        skin=0.5 if kind == "big" else 0.4,
                        seed=int(bar * 20 + beat * 7)),
                  at(bar, beat), gain=gain, pan_=pan_)

    def rim(bar: int, beat: float, gain: float) -> None:
        t = timeline(0.10)
        noise = bandpass(np.random.default_rng(int(bar * 17 + beat * 11)).standard_normal(len(t)),
                         700, 3500)
        click = np.sin(2 * np.pi * 1250 * t) * np.exp(-t / 0.012)
        wood = (click + 0.7 * noise * np.exp(-t / 0.006))
        drums.add(wood / (np.max(np.abs(wood)) + 1e-9), at(bar, beat),
                  gain=gain, pan_=0.35)

    def roll(bar: int, start: float, step: float, count: int, gain0: float,
             gain1: float, kind: str = "big") -> None:
        for k in range(count):
            g = gain0 + (gain1 - gain0) * k / max(count - 1, 1)
            hit(kind, bar, start + k * step, g, pan_=-0.15 + 0.3 * (k % 2))

    # ---------- 前奏：一只大鼓、一面锣，鼓边偶尔回应
    drums.add(gong(tune=68, dur=7.0), 0.0, gain=0.34, pan_=0.0)
    for bar in range(0, 4):
        hit("big", bar, 0.0, 0.75)
        hit("big", bar, 2.0, 0.55)
        rim(bar, 3.5, 0.16)
        if bar >= 2:
            hit("mid", bar, 1.5, 0.26, pan_=-0.2)
            hit("high", bar, 3.25, 0.18, pan_=0.25)

    # ---------- 主段：鼓队进入
    for bar in range(4, 12):
        for beat, kind, gain in MAIN:
            hit(kind, bar, beat, gain, pan_=-0.2 if kind == "mid" else 0.2)
        for beat, gain in RIM:
            rim(bar, beat, gain)
        if bar in (7, 11):
            roll(bar, 2.0, 0.25, 8, 0.20, 0.55)

    # ---------- 高潮：齐奏、鼓边加密、滚奏
    for bar in range(12, 20):
        hit("big", bar, 0.0, 0.80)
        hit("mid", bar, 0.0, 0.40)
        hit("high", bar, 0.0, 0.26)
        for beat, kind, gain in MAIN[1:]:
            hit(kind, bar, beat, gain * 1.05,
                pan_=-0.22 if kind == "mid" else 0.22)
        for beat, gain in RIM:
            rim(bar, beat, gain + 0.04)
        for k in range(8):
            rim(bar, 1.75 + k * 0.25, 0.05 + 0.006 * k)
        if bar in (13, 15, 17, 19):
            roll(bar, 3.0, 0.25, 4, 0.28, 0.52, "mid")
        if bar % 4 == 0:
            drums.add(crash(dur=1.4), at(bar), gain=0.10)
            drums.add(gong(tune=78, dur=6.0), at(bar), gain=0.24)

    # ---------- 间奏：只留大鼓与鼓边，重新蓄力
    for bar in range(20, 24):
        hit("big", bar, 0.0, 0.62)
        hit("big", bar, 2.0, 0.48)
        rim(bar, 1.0, 0.14)
        rim(bar, 3.0, 0.12)
        if bar >= 22:
            roll(bar, 2.0, 0.25, 8, 0.18, 0.45, "mid")
    roll(23, 2.0, 0.125, 16, 0.16, 0.60)

    # ---------- 收尾：三下齐奏，一整小节滚奏，最后一声大鼓
    for bar in (24, 25):
        for kind, gain in (("big", 0.85), ("mid", 0.42), ("high", 0.26)):
            hit(kind, bar, 0.0, gain)
            hit(kind, bar, 2.0, gain * 0.75)
        rim(bar, 1.0, 0.16)
        rim(bar, 3.5, 0.14)
    roll(26, 0.0, 0.125, 16, 0.20, 0.65)
    roll(26, 2.0, 0.125, 16, 0.30, 0.85)
    drums.add(crash(dur=2.6), at(27), gain=0.20)
    drums.add(gong(tune=66, dur=8.0), at(27), gain=0.36)
    hit("big", 27, 0.0, 0.9)
    hit("mid", 27, 0.0, 0.45)
    hit("high", 27, 0.0, 0.30)

    # ---------- 低音与铺底：只做底盘，不抢鼓
    n = int(DUR * 44100)
    t = np.arange(n) / 44100
    breath = 0.6 + 0.4 * np.sin(2 * np.pi * 0.06 * t - 1.1)
    for m, level in ((38, 0.12), (45, 0.06)):
        air.add(np.sin(2 * np.pi * hz(m) * t) * breath, 0.0, gain=level)
    for bar, name in enumerate(PROGRESSION):
        if bar < 4:
            continue
        for m in CHORDS[name]:
            air.add(pad(hz(m - 12), BAR * 1.15, voices=2, detune=0.004,
                        cutoff=480, attack=0.5),
                    at(bar), gain=0.028)

    # ---------- 总线
    pads = swirl(air.buf.mean(axis=1), rate=0.05, depth=0.4)
    mix = (reverb(drums.buf, dur=2.4, mix=0.20, damp=4200)
           + reverb(pads, dur=4.0, mix=0.35, damp=2600))
    mix = lowpass(mix, 14000)
    return render(out / "10_war_drums.wav", mix, fade=(0.01, 2.2), drive=0.20)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
