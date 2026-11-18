"""示例 7 · 星轨 —— 92 BPM，E 小调。

情绪：在星空下缓慢旋转。铺底、琶音、钟声各自以不同的速度在左右声道之间
绕圈，沙锤每半拍硬切一次左右；鼓与低音始终留在中间，否则人声会发晕。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (Track, bass, bell, hat, kick, pad, pluck, reverb,
                       snare, swirl)

BPM = 92
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 24
DUR = BARS * BAR + 4.5

VOICING = {
    "Em": [52, 55, 59, 64],
    "C": [48, 55, 60, 64],
    "G": [50, 55, 59, 62],
    "D": [50, 57, 62, 66],
}
BASS = {"Em": 40, "C": 36, "G": 43, "D": 38}

PROGRESSION = ["Em", "C", "G", "D"] * 5 + ["Em", "C", "D", "Em"]

ARP_STEPS = [0, 1, 2, 3, 2, 1, 2, 3] * 2

MELODY = [
    [(0, 1, 76), (1, 1, 74), (2, 2, 71)],
    [(0, 1, 72), (1, 1, 76), (2, 2, 79)],
    [(0, 1, 74), (1, 1, 71), (2, 2, 67)],
    [(0, 1, 69), (1, 1, 74), (2, 2, 78)],
    [(0, 1, 76), (1, .5, 79), (1.5, 1.5, 81), (3, 1, 79)],
    [(0, 2, 76), (2, 1, 72), (3, 1, 67)],
    [(0, 1, 74), (1, 1, 71), (2, 2, 74)],
    [(0, 2, 69), (2, 2, 74)],
]


def main(out: Path) -> Path:
    pad_bus = Track(DUR)
    arp_bus = Track(DUR)
    bell_bus = Track(DUR)
    low = Track(DUR)
    perc = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # ---------- 铺底：每小节一层，最后整体缓慢绕圈
    for bar, name in enumerate(PROGRESSION):
        for j, m in enumerate(VOICING[name][:3]):
            pad_bus.add(pad(hz(m), BAR * 1.3, voices=3, detune=0.005,
                            cutoff=1400, attack=1.0),
                        at(bar), gain=0.050, pan_=0.0)

    # ---------- 琶音：16 分音符，第 5 小节进入
    for bar in range(4, BARS):
        notes = VOICING[PROGRESSION[bar]]
        tones = [n + 12 for n in notes[:3]]
        for step in range(16):
            idx = ARP_STEPS[step]
            m = tones[idx % len(tones)] + (12 if idx >= len(tones) else 0)
            gain = 0.065 if bar < 12 else 0.082
            arp_bus.add(pluck(hz(m), BEAT * 0.42, bright=0.55),
                        at(bar, step * 0.25), gain=gain, pan_=0.0)

    # ---------- 钟声：前奏的散点 + 后半段的主旋律
    for bar in range(0, 4):
        notes = VOICING[PROGRESSION[bar]]
        for beat in (0.0, 2.0):
            bell_bus.add(bell(hz(notes[0] + 12), BEAT * 3.2),
                         at(bar, beat), gain=0.11, pan_=0.0)
    for i, phrase in enumerate(MELODY):
        bar = 12 + i
        for beat, dur, m in phrase:
            note = bell(hz(m), dur * BEAT * 1.05)
            bell_bus.add(note, at(bar, beat), gain=0.145, pan_=0.0)
            # 左右交替的回声，让旋律在空间里来回
            bell_bus.add(note * 0.5, at(bar, beat + 0.75), gain=0.075, pan_=-0.75)
            bell_bus.add(note * 0.25, at(bar, beat + 1.5), gain=0.055, pan_=0.75)

    # ---------- 低音：整小节长音，始终留在中间
    for bar, name in enumerate(PROGRESSION):
        if bar < 4:
            continue
        low.add(bass(hz(BASS[name]), BAR * 0.95, cutoff=300, sub=0.7),
                at(bar), gain=0.19, pan_=0.0)

    # ---------- 沙锤：每半拍硬切左右，制造最直观的旋转
    for bar in range(4, 12):
        for i in range(8):
            perc.add(hat(dur=0.1), at(bar, i * 0.5),
                     gain=0.050 if i % 2 == 0 else 0.035,
                     pan_=0.85 if i % 2 == 0 else -0.85)

    # ---------- 鼓组：第 13 小节进入，鼓与低音一样保持在中间
    for bar in range(12, 20):
        for beat in (0.0, 2.5):
            perc.add(kick(tune=50), at(bar, beat), gain=0.30, pan_=0.0)
        for beat in (1.0, 3.0):
            perc.add(snare(), at(bar, beat), gain=0.17, pan_=0.0)
        for i in range(8):
            perc.add(hat(), at(bar, i * 0.5),
                     gain=0.042 if i % 2 == 0 else 0.028,
                     pan_=0.55 if i % 2 == 0 else -0.55)
        perc.add(hat(open_=True, dur=0.22), at(bar, 3.5), gain=0.055, pan_=0.0)

    # ---------- 收尾：回到 E 小调
    for m in VOICING["Em"]:
        pad_bus.add(pad(hz(m), 7.0, voices=3, cutoff=1200, attack=0.8),
                    at(23), gain=0.05, pan_=0.0)
    bell_bus.add(bell(hz(88), 6.0), at(23, 0.1), gain=0.10, pan_=0.0)

    # ---------- 声部各自绕圈：速度与相位都不同，避免一起转到同一边
    pad_st = swirl(pad_bus.buf.mean(axis=1), rate=0.09, depth=0.9, phase=np.pi)
    arp_st = swirl(arp_bus.buf.mean(axis=1), rate=0.36, depth=0.95)
    bell_st = swirl(bell_bus.buf.mean(axis=1), rate=0.18, depth=0.70, phase=np.pi / 2)

    mix = (reverb(pad_st, dur=4.0, mix=0.40, damp=3200)
           + reverb(arp_st, dur=2.4, mix=0.28, damp=4600)
           + reverb(bell_st, dur=3.4, mix=0.34, damp=5200)
           + low.buf
           + perc.buf)
    return render(out / "07_orbit.wav", mix, fade=(0.05, 3.2))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
