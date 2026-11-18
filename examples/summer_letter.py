"""示例 1 · 夏日信笺 —— 76 BPM，C 大调。

情绪：午后、信纸、慢镜头。钢琴分解和弦开场，旋律进来后加弦垫与
极轻的沙锤，最后停在主和弦上。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (Track, bell, echo, kick, pad, piano, reverb, shaker)

BPM = 76
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 16
DUR = BARS * BAR + 4.0

VOICING = {
    "C": [48, 55, 60, 64],
    "G/B": [47, 55, 59, 62],
    "Am": [45, 52, 57, 60, 64],
    "F": [41, 53, 57, 60, 65],
    "G": [43, 55, 59, 62],
    "Em": [40, 52, 55, 59, 64],
}
PAD = {
    "C": [48, 55, 64],
    "G/B": [47, 55, 62],
    "Am": [45, 52, 60],
    "F": [41, 53, 60],
    "G": [43, 55, 62],
    "Em": [40, 52, 59],
}
BASS = {"C": "C2", "G/B": "B1", "Am": "A2", "F": "F2", "G": "G2", "Em": "E2"}

PROGRESSION = ["C", "G/B", "Am", "F", "C", "G", "Am", "F",
               "F", "G", "Em", "Am", "F", "G", "C", "C"]

# 每个元素是 (小节内第几拍, 时值, midi)，从第 5 小节开始
MELODY = [
    [(0, 1, 67), (1, .5, 69), (1.5, 1.5, 72), (3, .5, 76), (3.5, .5, 74)],
    [(0, 1.5, 74), (1.5, .5, 71), (2, 1, 67), (3, .5, 71), (3.5, .5, 74)],
    [(0, 1, 72), (1, 1, 76), (2, .5, 74), (2.5, .5, 72), (3, 1, 69)],
    [(0, 1.5, 69), (1.5, .5, 72), (2, 1.5, 77), (3.5, .5, 76)],
    [(0, 1, 77), (1, .5, 76), (1.5, .5, 74), (2, 1, 72), (3, 1, 69)],
    [(0, 1, 71), (1, 1, 74), (2, 1.5, 79), (3.5, .5, 77)],
    [(0, 1, 76), (1, .5, 74), (1.5, .5, 71), (2, 2, 67)],
    [(0, 1, 72), (1, .5, 71), (1.5, .5, 69), (2, 2, 64)],
    [(0, 1, 69), (1, .5, 72), (1.5, .5, 77), (2, 1, 76), (3, 1, 74)],
    [(0, 1.5, 74), (1.5, .5, 71), (2, 1, 74), (3, 1, 79)],
    [(0, 1, 76), (1, 1, 79), (2, 1, 76), (3, 1, 74)],
    [(0, 2, 72), (2, .5, 71), (2.5, .5, 69), (3, 1, 72)],
]
FINAL = [(0, 2, 76), (2, 2, 72)]


def main(out: Path) -> Path:
    comp = Track(DUR)    # 钢琴伴奏
    lead = Track(DUR)    # 钢琴旋律
    low = Track(DUR)     # 低音
    air = Track(DUR)     # 弦垫
    perc = Track(DUR)    # 沙锤与轻鼓

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # ---------- 钢琴：前四小节分解和弦，之后柱式 + 偶尔高音点缀
    for bar, name in enumerate(PROGRESSION):
        notes = VOICING[name]
        if bar < 4:
            pattern = [0, 1, 2, 3, 2, 1, 2, 3]
            for i, idx in enumerate(pattern):
                m = notes[idx % len(notes)] + (12 if idx >= len(notes) else 0)
                comp.add(piano(hz(m), BEAT * 1.6), at(bar, i * 0.5),
                         gain=0.20, pan_=-0.15)
        else:
            for beat, dur, gain in ((0.0, 2.2, 0.19), (2.5, 1.6, 0.15)):
                for j, m in enumerate(notes):
                    # 轻微琶音错位，像手指依次按下
                    comp.add(piano(hz(m), dur * BEAT), at(bar, beat + j * 0.012),
                             gain=gain / np.sqrt(len(notes)), pan_=-0.22)
            if bar % 2 == 1:
                comp.add(piano(hz(notes[-1] + 12), BEAT * 1.4), at(bar, 3.5),
                         gain=0.10, pan_=0.25)

    # ---------- 旋律
    for i, phrase in enumerate(MELODY):
        bar = 4 + i
        for beat, dur, m in phrase:
            note = piano(hz(m), dur * BEAT * 0.98)
            lead.add(echo(note, delay=BEAT * 0.75, feedback=0.22, mix=0.18),
                     at(bar, beat), gain=0.26, pan_=0.10)
    for beat, dur, m in FINAL:
        lead.add(echo(piano(hz(m), dur * BEAT), delay=BEAT * 0.75, mix=0.2),
                 at(14, beat), gain=0.24, pan_=0.10)

    # ---------- 低音：从第二小节进入
    for bar, name in enumerate(PROGRESSION):
        if bar < 2:
            continue
        m = BASS[name]
        low.add(piano(hz(m), BAR * 1.02), at(bar), gain=0.30 if bar < 4 else 0.26)

    # ---------- 弦垫：每小节铺一层，靠重叠形成呼吸
    for bar, name in enumerate(PROGRESSION):
        level = 0.052 if bar < 4 else 0.062
        for j, m in enumerate(PAD[name]):
            air.add(pad(hz(m), BAR * 1.25, voices=3, cutoff=1300, attack=1.1),
                    at(bar), gain=level, pan_=(-0.35 + 0.35 * j))

    # ---------- 打击：沙锤打满八分音符，轻底鼓从第 9 小节进入
    for bar in range(4, 16):
        for i in range(8):
            accent = 0.085 if i % 2 == 0 else 0.055
            perc.add(shaker(), at(bar, i * 0.5), gain=accent,
                     pan_=0.3 if i % 2 == 0 else -0.25)
    for bar in range(8, 16):
        for beat in (0.0, 2.0):
            perc.add(kick(tune=46), at(bar, beat), gain=0.30)

    # ---------- 收尾
    for j, m in enumerate([36, 48, 55, 60, 64, 67]):
        comp.add(piano(hz(m), 6.0), at(15) + j * 0.045, gain=0.14, pan_=-0.1)
    lead.add(bell(hz(84), 5.0), at(15, 0.05), gain=0.12, pan_=0.3)

    # ---------- 总线
    keys = comp.buf + low.buf
    keys = reverb(keys, dur=2.8, mix=0.20, damp=4800)
    lead_bus = reverb(lead.buf, dur=3.4, mix=0.32, damp=5200)
    air_bus = reverb(air.buf, dur=5.0, mix=0.48, damp=3600)

    mix = keys + lead_bus + air_bus + perc.buf * 0.85
    return render(out / "01_summer_letter.wav", mix, fade=(0.02, 3.0))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
