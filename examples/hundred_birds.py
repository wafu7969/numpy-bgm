"""示例 8 · 百鸟朝凤 —— 132 BPM，D 宫五声。

情绪：唢呐一响，整条街都亮起来。颤音、滑音、花舌、叠音、双吐、长音循环
以及模仿鸟叫的高频滑音全部用上；锣、鼓、镲压在下面，鸟叫在左右声道之间飞。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (Track, bass, bird, crash, gong, hat, kick, lowpass, pad,
                       reverb, suona, swirl, tom)

BPM = 132
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 32
DUR = BARS * BAR + 4.5

VOICING = {
    "D": [50, 57, 62, 66],
    "G": [43, 50, 55, 59],
    "A": [45, 52, 57, 61],
}
BASS = {"D": 38, "G": 43, "A": 45}

PROGRESSION = ["D", "G", "A", "D"] * 8

INTRO = [
    [(0, 1, 74, 71), (2, 1.5, 78, None)],
    [(0, .5, 81, None), (.5, .5, 78, None), (1, 2, 74, None)],
    [(0, 1, 83, None), (1, 1, 81, None), (2, 2, 78, None)],
    [(0, 1, 74, None), (1, 3, 86, 81)],
]

THEME1 = [
    [(0, .5, 74), (.5, .5, 78), (1, .5, 81), (1.5, 1, 83), (2.5, .5, 81), (3, .5, 78)],
    [(0, .5, 79), (.5, .5, 83), (1, 1, 86), (2, .5, 83), (2.5, .5, 79), (3, .5, 74)],
    [(0, .5, 76), (.5, .5, 81), (1, 1, 83), (2, .5, 81), (2.5, .5, 78), (3, .5, 76)],
    [(0, 1, 74), (1, .5, 78), (1.5, .5, 81), (2, 2, 86)],
]

THEME2 = [
    [(0, .25, 74), (.25, .25, 78), (.5, .25, 81), (.75, .25, 83), (1, .5, 86),
     (1.5, .25, 83), (1.75, .25, 81), (2, .5, 78), (2.5, .25, 74), (2.75, .25, 78),
     (3, .5, 81), (3.5, .5, 78)],
    [(0, .5, 79), (.5, .5, 83), (1, .25, 86), (1.25, .25, 83), (1.5, .5, 79),
     (2, .5, 74), (2.5, .5, 79), (3, 1, 83)],
    [(0, .25, 76), (.25, .25, 78), (.5, .5, 81), (1, .5, 83), (1.5, .25, 81),
     (1.75, .25, 78), (2, .5, 76), (2.5, .5, 74), (3, 1, 76)],
    [(0, .5, 74), (.5, .5, 78), (1, 1, 81), (2, .5, 86), (2.5, .5, 83), (3, 1, 81)],
    [(0, .5, 86), (.5, .25, 83), (.75, .25, 81), (1, .5, 78), (1.5, .5, 81),
     (2, 1, 86), (3, .5, 83), (3.5, .5, 81)],
    [(0, .5, 83), (.5, .5, 86), (1, .5, 88), (1.5, .5, 86), (2, .5, 83),
     (2.5, .5, 79), (3, .5, 83), (3.5, .5, 86)],
    [(0, 1, 81), (1.5, .5, 83), (2, 1, 86), (3, 1, 83)],
    [(0, 2, 86), (2, 1, 83), (3, 1, 78)],
]


def main(out: Path) -> Path:
    lead = Track(DUR)
    birds = Track(DUR)
    low = Track(DUR)
    air = Track(DUR)
    perc = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    def play(bar: int, beat: float, dur: float, m: int, gain: float,
             flutter: float = 0.0, slide_from: int | None = None,
             grace: bool = False) -> None:
        """把一个唢呐音放到时间线上，可带叠音、滑音、花舌。"""
        d = max(dur * BEAT, 0.09)
        if slide_from is None:
            audio = suona(hz(m), d, flutter=flutter)
        else:
            audio = suona(hz(slide_from), d, slide_to=hz(m),
                          slide_time=min(0.16, d * 0.4), flutter=flutter)
        if grace:
            g = suona(hz(m), 0.07, vib=0.0, vib_depth=0.0, attack=0.004)
            lead.add(g, at(bar, beat) - 0.075, gain=gain * 0.4, pan_=0.0)
        lead.add(audio, at(bar, beat), gain=gain, pan_=0.0)

    # ---------- 前奏：锣一响，唢呐独奏，带滑音与叠音
    perc.add(gong(tune=78, dur=6.0), 0.0, gain=0.30, pan_=0.0)
    for bar in range(0, 4):
        perc.add(kick(tune=42, dur=0.9), at(bar, 0.0), gain=0.34)
        perc.add(kick(tune=42, dur=0.9), at(bar, 2.0), gain=0.26)
    for bar, phrase in enumerate(INTRO):
        for beat, dur, m, slide in phrase:
            if slide is None:
                play(bar, beat, dur, m, 0.24, grace=True)
            else:
                play(bar, beat, dur, m, 0.26, slide_from=slide)

    # ---------- 主题一：中音区，鼓点进入
    for i, phrase in enumerate(THEME1):
        bar = 4 + i
        for beat, dur, m in phrase:
            play(bar, beat, dur, m, 0.25, grace=dur >= 0.5,
                 flutter=0.45 if dur >= 1.5 else 0.0)

    # ---------- 主题二：加花、双吐、锣鼓全上
    for i, phrase in enumerate(THEME2):
        bar = 8 + i
        for beat, dur, m in phrase:
            play(bar, beat, dur, m, 0.27, grace=dur >= 0.4,
                 flutter=0.5 if dur >= 1.0 else 0.0)

    # ---------- 百鸟段：鸟叫在左右声道之间来回飞，唢呐在后面双吐
    rng = np.random.default_rng(7)
    for bar in range(16, 18):
        for i in range(8):
            base = [1250, 1650, 950, 1400, 1100, 1850, 1000, 1500][(i + bar) % 8]
            birds.add(bird(base, 0.16, rise=1.8, seed=bar * 8 + i),
                      at(bar, i * 0.5), gain=0.13,
                      pan_=0.85 if i % 2 == 0 else -0.85)
    for bar in (18, 19):
        for i in range(16):
            m = 86 if i % 2 == 0 else 83
            play(bar, i * 0.25, 0.2, m, 0.13 + 0.004 * i, flutter=0.3)
            if rng.random() < 0.35:
                birds.add(bird(float(rng.integers(900, 2100)), 0.12,
                               rise=float(rng.uniform(1.4, 2.2)), seed=i + bar * 16),
                          at(bar, i * 0.25 + 0.06), gain=0.07,
                          pan_=0.8 if i % 2 else -0.8)

    # ---------- 高潮：主题二再来一遍，叠低八度、花舌、锣鼓镲
    for i, phrase in enumerate(THEME2):
        bar = 20 + i
        for beat, dur, m in phrase:
            play(bar, beat, dur, m, 0.29, grace=dur >= 0.4,
                 flutter=0.55 if dur >= 1.0 else 0.0)
            # 低八度加厚，像两支唢呐齐吹
            low.add(suona(hz(m - 12), max(dur * BEAT, 0.1), vib=5.2), at(bar, beat),
                    gain=0.10, pan_=0.0)

    # ---------- 打击：铺满整首
    for bar in range(4, 16):
        perc.add(kick(tune=44, dur=0.8), at(bar, 0.0), gain=0.32)
        perc.add(kick(tune=44, dur=0.8), at(bar, 2.0), gain=0.24)
        for i in range(8):
            perc.add(hat(), at(bar, i * 0.5),
                     gain=0.026 if i % 2 == 0 else 0.015, pan_=0.3)
    for bar in (8, 12):
        perc.add(crash(dur=1.4), at(bar, 0.0), gain=0.10)
    for bar in range(20, 28):
        for beat in (0.0, 1.0, 2.0, 3.0):
            perc.add(kick(tune=44, dur=0.75), at(bar, beat), gain=0.30)
        for i in range(8):
            perc.add(hat(), at(bar, i * 0.5),
                     gain=0.020 if i % 2 == 0 else 0.010, pan_=0.35)
        if bar % 4 == 0:
            perc.add(crash(dur=1.2), at(bar, 0.0), gain=0.10)
        if bar in (20, 24):
            perc.add(gong(tune=86, dur=5.5), at(bar, 0.0), gain=0.22)

    # 段落缝隙的排鼓过门
    for bar in (7, 15, 19, 27):
        for k in range(6):
            perc.add(tom(tune=150 + 18 * k, dur=0.35), at(bar, 2.5 + k * 0.25),
                     gain=0.16 + 0.02 * k)
    perc.add(suona(hz(74), 0.22, vib=0, vib_depth=0), at(19, 3.5), gain=0.16)

    # ---------- 结尾：长音花舌 + 锣
    perc.add(gong(tune=80, dur=6.0), at(28), gain=0.30)
    play(28, 0.0, 4.0, 86, 0.30, flutter=0.6)
    play(29, 0.0, 2.0, 83, 0.28, flutter=0.5)
    play(29, 2.0, 2.0, 81, 0.28)
    for i, m in enumerate((78, 81, 83, 86)):
        play(30, i * 0.25, 0.3, m, 0.24 + 0.01 * i)
    play(30, 1.0, 1.5, 88, 0.30, flutter=0.55)
    play(30, 2.5, 1.5, 86, 0.30, flutter=0.6)
    perc.add(crash(dur=2.2), at(31, 0.0), gain=0.18)
    perc.add(gong(tune=76, dur=6.0), at(31, 0.0), gain=0.32)
    perc.add(kick(tune=40, dur=1.2), at(31, 0.0), gain=0.36)
    play(31, 0.0, 3.2, 86, 0.32, flutter=0.65)

    # ---------- 铺底与低音
    for bar, name in enumerate(PROGRESSION):
        for j, m in enumerate(VOICING[name][:3]):
            air.add(pad(hz(m), BAR * 1.25, voices=3, detune=0.005,
                        cutoff=1900 if bar >= 20 else 1500, attack=0.7),
                    at(bar), gain=0.048, pan_=0.0)
        if bar >= 4:
            low.add(bass(hz(BASS[name]), BAR * 0.95, cutoff=340), at(bar),
                    gain=0.18, pan_=0.0)

    # ---------- 总线：唢呐居中，铺底缓慢环绕
    lead_bus = reverb(lead.buf, dur=2.4, mix=0.22, damp=5600)
    bird_bus = reverb(birds.buf, dur=2.8, mix=0.30, damp=6000)
    pad_st = swirl(air.buf.mean(axis=1), rate=0.07, depth=0.75, phase=np.pi)

    mix = (lead_bus + bird_bus
           + reverb(pad_st, dur=4.0, mix=0.38, damp=3000)
           + low.buf
           + reverb(perc.buf, dur=3.2, mix=0.16, damp=4200))
    mix = lowpass(mix, 14000)
    return render(out / "08_hundred_birds.wav", mix, fade=(0.01, 2.2), drive=0.12)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
