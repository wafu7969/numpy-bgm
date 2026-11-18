"""示例 9 · 天宫迅音（致敬版）—— 128 BPM，A 小调。

情绪：云海、天门、腾云驾雾。16 分音符合成器琶音铺底，铜管式主旋律压在上面，
电子鼓与民乐打击交替推进。旋律与音色为原创，只沿用那个年代的电子 + 民乐语汇。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (Track, bass, bell, crash, echo, gong, hat, kick, lead,
                       pad, reverb, snare, supersaw, swell)

BPM = 128
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 28
DUR = BARS * BAR + 4.0

VOICING = {
    "Am": [57, 60, 64, 69],
    "F": [53, 57, 60, 65],
    "G": [55, 59, 62, 67],
}
BASS = {"Am": 45, "F": 41, "G": 43}

PROGRESSION = (["Am", "Am", "F", "G"] * 3
               + ["F", "G", "Am", "Am"]
               + ["Am", "Am", "F", "G"] * 2
               + ["F", "G", "Am", "Am"])

ARP_STEPS = [0, 1, 2, 3, 2, 1, 2, 3] * 2

THEME = [
    [(0, .5, 69), (.5, .5, 72), (1, .5, 76), (1.5, 1.5, 81), (3, .5, 79), (3.5, .5, 76)],
    [(0, .5, 74), (.5, .5, 76), (1, 1.5, 79), (2.5, .5, 76), (3, .5, 74), (3.5, .5, 72)],
    [(0, .5, 69), (.5, .5, 72), (1, .5, 77), (1.5, 1.5, 81), (3, .5, 79), (3.5, .5, 77)],
    [(0, 1, 74), (1, .5, 71), (1.5, 1.5, 67), (3, .5, 71), (3.5, .5, 74)],
    [(0, .5, 76), (.5, .5, 79), (1, .5, 81), (1.5, 1.5, 84), (3, .5, 81), (3.5, .5, 79)],
    [(0, .5, 74), (.5, .5, 76), (1, 1.5, 79), (2.5, .5, 81), (3, .5, 79), (3.5, .5, 76)],
    [(0, .5, 77), (.5, .5, 81), (1, 1, 84), (2, .5, 81), (2.5, .5, 79), (3, 1, 77)],
    [(0, 1, 74), (1, 1, 71), (2, 2, 67)],
]

BRIDGE_BELLS = [
    [65, 69, 72, 77],
    [67, 71, 74, 79],
    [69, 72, 76, 81],
    [69, 72, 76, 81],
]


def main(out: Path) -> Path:
    arp = Track(DUR)
    lead_bus = Track(DUR)
    bells = Track(DUR)
    low = Track(DUR)
    air = Track(DUR)
    drums = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # ---------- 16 分音符琶音：前奏偏暗，进入主题后打开
    for bar in range(BARS):
        notes = VOICING[PROGRESSION[bar]]
        tones = [n + 12 for n in notes[:3]]
        if bar < 4:
            cutoff, gain = 700, 0.060
        elif bar < 12:
            cutoff, gain = 2600, 0.070
        elif bar < 16:
            cutoff, gain = 3400, 0.075
        elif bar < 24:
            cutoff, gain = 3200, 0.078
        else:
            cutoff, gain = 1800, 0.060
        for step in range(16):
            idx = ARP_STEPS[step]
            m = tones[idx % len(tones)] + (12 if idx >= len(tones) else 0)
            arp.add(supersaw(hz(m), BEAT * 0.4, voices=2, detune=0.005,
                             cutoff=cutoff),
                    at(bar, step * 0.25), gain=gain,
                    pan_=0.4 if step % 2 == 0 else -0.4)

    # ---------- 主旋律：第 5 小节进入，第二段加钟琴与高八度
    for section_start in (4, 16):
        for i, phrase in enumerate(THEME):
            bar = section_start + i
            for beat, dur, m in phrase:
                note = lead(hz(m), max(dur * BEAT * 0.96, 0.1))
                lead_bus.add(echo(note, delay=BEAT * 0.75, feedback=0.25, mix=0.18),
                             at(bar, beat), gain=0.20, pan_=0.0)
                if section_start == 16:
                    lead_bus.add(bell(hz(m + 12), dur * BEAT), at(bar, beat),
                                 gain=0.05, pan_=0.25)

    # ---------- 间奏：钟琴琶音，把音量让出来
    for i, notes in enumerate(BRIDGE_BELLS):
        bar = 12 + i
        for k in range(8):
            m = notes[k % len(notes)] + (12 if k >= len(notes) else 0)
            bells.add(bell(hz(m), BEAT * 1.1), at(bar, k * 0.5),
                      gain=0.075, pan_=0.45 if k % 2 else -0.45)

    # ---------- 低音
    for bar, name in enumerate(PROGRESSION):
        if bar < 4:
            continue
        root = BASS[name]
        if bar < 12 or bar >= 16:
            for i in range(8):
                offset = 12 if i in (3, 7) else 0
                low.add(bass(hz(root + offset), BEAT * 0.44, cutoff=380),
                        at(bar, i * 0.5), gain=0.18)
        else:
            low.add(bass(hz(root), BAR * 0.95, cutoff=300), at(bar), gain=0.16)

    # ---------- 铺底
    for bar, name in enumerate(PROGRESSION):
        for j, m in enumerate(VOICING[name][:3]):
            air.add(pad(hz(m), BAR * 1.2, voices=3, detune=0.006,
                        cutoff=2200, attack=0.5),
                    at(bar), gain=0.045, pan_=(-0.35 + 0.35 * j))

    # ---------- 鼓组：前奏只有锣，主题进入后全编制
    for bar in range(4, 12):
        drums.add(kick(tune=50), at(bar, 0.0), gain=0.34)
        drums.add(kick(tune=50), at(bar, 2.0), gain=0.28)
        for beat in (1.0, 3.0):
            drums.add(snare(), at(bar, beat), gain=0.16)
        for i in range(8):
            drums.add(hat(), at(bar, i * 0.5),
                      gain=0.032 if i % 2 == 0 else 0.022, pan_=0.25)
    for bar in range(16, 24):
        for beat in (0.0, 1.0, 2.0, 3.0):
            drums.add(kick(tune=50), at(bar, beat), gain=0.33)
        for beat in (1.0, 3.0):
            drums.add(snare(), at(bar, beat), gain=0.17)
        for i in range(16):
            drums.add(hat(), at(bar, i * 0.25),
                      gain=0.024 if i % 4 == 0 else 0.012, pan_=0.3)
    for bar in (13, 14, 15):
        for i in range(8):
            drums.add(hat(), at(bar, i * 0.5), gain=0.028, pan_=0.35)

    # ---------- 段落标记
    drums.add(gong(tune=80, dur=6.0), at(0), gain=0.26)
    for bar in (8, 12, 16, 20, 24):
        drums.add(crash(dur=1.6), at(bar), gain=0.12)
    for bar, beat in ((3, 2.0), (11, 2.0), (15, 2.0), (23, 2.0)):
        air.add(swell(BEAT * 2), at(bar, beat), gain=0.16)
    for bar in (7, 15, 23):
        for k in range(6):
            drums.add(snare(), at(bar, 2.5 + k * 0.25), gain=0.07 + 0.012 * k)

    # ---------- 收尾
    for m in VOICING["Am"]:
        bells.add(bell(hz(m + 12), 5.0), at(26) + 0.02 * m, gain=0.10, pan_=0.0)
    drums.add(gong(tune=78, dur=6.5), at(26), gain=0.30)
    drums.add(crash(dur=2.4), at(26), gain=0.16)
    drums.add(kick(tune=46, dur=1.1), at(26), gain=0.36)
    lead_bus.add(lead(hz(81), 2.6), at(26), gain=0.18, pan_=0.0)

    # ---------- 总线
    mix = (reverb(arp.buf, dur=2.2, mix=0.24, damp=6000) * 0.95
           + reverb(lead_bus.buf, dur=2.6, mix=0.28, damp=5200)
           + reverb(bells.buf, dur=3.8, mix=0.42, damp=5200)
           + low.buf
           + reverb(air.buf, dur=3.4, mix=0.40, damp=3200)
           + reverb(drums.buf, dur=2.2, mix=0.16, damp=5000))
    return render(out / "09_celestial_echo.wav", mix, fade=(0.02, 2.5), drive=0.10)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
