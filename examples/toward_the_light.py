"""示例 1 · 向光而行 —— 104 BPM，D 大调。

情绪：清晨出发前的一次深呼吸。钢琴分解和弦起步，弦垫与贝斯逐层加入，
第八小节进鼓、第十二小节全编制，结尾收在一个长和弦上。
适合片头、年度总结、励志向剪辑。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (Track, bass, bell, crash, echo, hat, kick, pad, piano,
                       reverb, snare, swell, tom)

BPM = 104
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 24
DUR = BARS * BAR + 3.5

VOICING = {
    "D": [50, 57, 62, 66],
    "A": [45, 52, 57, 61],
    "Bm": [47, 54, 59, 62],
    "G": [43, 50, 55, 59],
}
BASS = {"D": 38, "A": 45, "Bm": 47, "G": 43}

PROGRESSION = (["D", "A", "Bm", "G"] * 3
               + ["G", "A", "Bm", "A", "G", "A", "D", "D"]
               + ["Bm", "G", "A", "D"])

# 第 9-12 小节的旋律（低八度，像在积蓄）
MELODY_A = [
    [(0, 1, 74), (1, 1, 78), (2, 1.5, 81), (3.5, .5, 79)],
    [(0, 1, 76), (1, 1, 73), (2, 2, 69)],
    [(0, 1, 78), (1, 1, 74), (2, 1, 71), (3, 1, 74)],
    [(0, 2, 79), (2, 1, 78), (3, 1, 74)],
]

# 第 13-20 小节：主旋律，音区抬高一个层次
MELODY_B = [
    [(0, 1, 79), (1, 1, 81), (2, 2, 83)],
    [(0, 1, 81), (1, 1, 76), (2, 2, 78)],
    [(0, 1, 83), (1, .5, 81), (1.5, .5, 78), (2, 2, 74)],
    [(0, 2, 76), (2, 2, 73)],
    [(0, 1, 79), (1, 1, 81), (2, 2, 86)],
    [(0, 1, 81), (1, 1, 83), (2, 2, 81)],
    [(0, 1, 78), (1, 1, 81), (2, 2, 86)],
    [(0, 4, 81)],
]


def main(out: Path) -> Path:
    keys = Track(DUR)
    lead = Track(DUR)
    low = Track(DUR)
    air = Track(DUR)
    drums = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # ---------- 钢琴：前 4 小节分解，之后柱式，结尾再次分解
    for bar, name in enumerate(PROGRESSION):
        notes = VOICING[name]
        if bar < 8 or bar >= 20:
            pattern = [0, 1, 2, 3, 2, 1, 2, 3]
            for i, idx in enumerate(pattern):
                m = notes[idx % len(notes)] + (12 if idx >= len(notes) else 0)
                gain = 0.13 if bar < 4 else 0.16
                keys.add(piano(hz(m), BEAT * 1.5), at(bar, i * 0.5),
                         gain=gain, pan_=-0.18)
        else:
            for beat, dur, gain in ((0.0, 2.1, 0.14), (2.5, 1.5, 0.11)):
                for j, m in enumerate(notes):
                    keys.add(piano(hz(m), dur * BEAT), at(bar, beat + j * 0.01),
                             gain=gain / np.sqrt(len(notes)), pan_=-0.2)
                keys.add(piano(hz(notes[-1] + 12), dur * BEAT), at(bar, beat),
                         gain=0.07, pan_=0.28)

    # ---------- 低音：第 5 小节进入，第 13 小节起改为八分音符推进
    for bar, name in enumerate(PROGRESSION):
        if bar < 4:
            continue
        root = BASS[name]
        if bar < 12:
            for beat in (0.0, 2.0):
                low.add(bass(hz(root), BEAT * 1.85, cutoff=320), at(bar, beat),
                        gain=0.20)
        elif bar < 20:
            for i in range(8):
                offset = 12 if i in (3, 7) else 0
                low.add(bass(hz(root + offset), BEAT * 0.44, cutoff=380),
                        at(bar, i * 0.5), gain=0.17)
        else:
            low.add(bass(hz(root), BAR * 0.95, cutoff=300), at(bar), gain=0.16)

    # ---------- 弦垫：逐段加厚
    for bar, name in enumerate(PROGRESSION):
        level = 0.040 if bar < 8 else (0.052 if bar < 12 else 0.060)
        cutoff = 1200 if bar < 8 else (1600 if bar < 12 else 2200)
        for j, m in enumerate(VOICING[name][:3]):
            air.add(pad(hz(m), BAR * 1.3, voices=3, detune=0.005,
                        cutoff=cutoff, attack=0.9),
                    at(bar), gain=level, pan_=(-0.4 + 0.35 * j))

    # ---------- 旋律
    for i, phrase in enumerate(MELODY_A):
        bar = 8 + i
        for beat, dur, m in phrase:
            note = piano(hz(m), dur * BEAT * 1.02)
            lead.add(echo(note, delay=BEAT * 0.75, feedback=0.20, mix=0.14),
                     at(bar, beat), gain=0.24, pan_=0.08)
    for i, phrase in enumerate(MELODY_B):
        bar = 12 + i
        for beat, dur, m in phrase:
            note = piano(hz(m), dur * BEAT * 1.02)
            lead.add(echo(note, delay=BEAT * 0.75, feedback=0.22, mix=0.16),
                     at(bar, beat), gain=0.27, pan_=0.08)
            if bar >= 16:
                lead.add(bell(hz(m + 12), dur * BEAT * 1.4), at(bar, beat),
                         gain=0.06, pan_=-0.3)

    # ---------- 鼓组：第 9 小节进入，第 13 小节全编制，第 21 小节撤出
    for bar in range(8, 20):
        full = bar >= 12
        for beat in (0.0, 2.0):
            drums.add(kick(tune=48), at(bar, beat), gain=0.34)
        if full:
            for beat in (1.0, 3.0):
                drums.add(snare(), at(bar, beat), gain=0.20)
            for beat in (0.5, 1.5, 2.5, 3.5):
                drums.add(hat(open_=True, dur=0.2), at(bar, beat), gain=0.06,
                          pan_=0.15)
            drums.add(tom(tune=58, dur=0.9), at(bar, 0.0), gain=0.13)
        for i in range(8):
            drums.add(hat(), at(bar, i * 0.5),
                      gain=0.050 if i % 2 == 0 else 0.032,
                      pan_=-0.15)

    # 段落连接：军鼓滚奏与镲片
    for bar in (11, 19):
        for k in range(8):
            drums.add(snare(), at(bar, 2 + k * 0.25), gain=0.06 + 0.012 * k)
    for bar in (12, 20):
        drums.add(crash(), at(bar), gain=0.15, pan_=0.0)
    for bar, beat, dur in ((7, 2, 2.0), (11, 2, 2.0), (19, 2, 2.0)):
        air.add(swell(dur), at(bar, beat), gain=0.16)

    # ---------- 收尾
    for j, m in enumerate([38, 50, 57, 62, 66, 69]):
        keys.add(piano(hz(m), 6.5), at(22) + j * 0.04, gain=0.13, pan_=-0.1)
    lead.add(bell(hz(86), 5.0), at(23, 0.1), gain=0.10, pan_=0.3)

    # ---------- 总线
    piano_bus = reverb(keys.buf + low.buf, dur=2.6, mix=0.20, damp=5000)
    lead_bus = reverb(lead.buf, dur=3.2, mix=0.28, damp=5200)
    air_bus = reverb(air.buf, dur=4.5, mix=0.45, damp=3400)

    mix = piano_bus + lead_bus + air_bus + drums.buf * 0.95
    return render(out / "01_toward_the_light.wav", mix, fade=(0.02, 2.6))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
