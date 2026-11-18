"""示例 5 · 深夜电台 —— 78 BPM，C 大调，带摇摆的 Lo-Fi。

情绪：凌晨两点、台灯、写到一半的日记。电钢琴的七和弦、黑胶底噪、
轻微走音的磁带抖动，是这类 BGM 让人放松的全部秘密。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.notation import swing_offset
from bgm.synth import (Track, bass, echo, ep, hat, kick, lowpass, reverb,
                       snare, tape, vinyl)

BPM = 78
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 20
DUR = BARS * BAR + 3.0

VOICING = {
    "Cmaj7": [52, 55, 59, 64],
    "Am7": [52, 55, 60, 64],
    "Dm7": [50, 53, 57, 60, 65],
    "G7": [50, 53, 55, 59],
}
BASS = {"Cmaj7": 36, "Am7": 45, "Dm7": 38, "G7": 43}
PROGRESSION = ["Cmaj7", "Am7", "Dm7", "G7"] * 5

MELODY = [
    [(0, 1, 76), (1, 1, 74), (2, 2, 72)],
    [(0, 1.5, 72), (1.5, .5, 71), (2, 2, 69)],
    [(0, 1, 69), (1, .5, 72), (1.5, 2.5, 74)],
    [(0, 2, 74), (2, 2, 71)],
    [(0, 1, 76), (1, 1, 79), (2, 2, 76)],
    [(0, 1.5, 72), (1.5, .5, 69), (2, 2, 67)],
    [(0, 1, 69), (1, 1, 72), (2, 2, 69)],
    [(0, 2, 71), (2, 2, 67)],
]

SWING = swing_offset(BPM, 0.63)


def main(out: Path) -> Path:
    keys = Track(DUR)
    low = Track(DUR)
    drums = Track(DUR)
    lead = Track(DUR)
    noise = Track(DUR)

    rng = np.random.default_rng(42)

    def at(bar: int, beat: float = 0.0, human: float = 0.0) -> float:
        return bar * BAR + beat * BEAT + human

    # ---------- 电钢琴：两小节一个循环，第二小节加一个提前的切分
    for bar, name in enumerate(PROGRESSION):
        if bar >= 18:
            continue
        notes = VOICING[name]
        if bar % 2 == 0:
            hits = [(0.0, 1.9), (2.5, 1.3)]
        else:
            hits = [(0.0, 1.3), (1.5, 1.1), (3.0, 1.2)]
        if bar < 4:
            hits = hits[:1]
        for beat, dur in hits:
            for j, m in enumerate(notes):
                keys.add(ep(hz(m), dur * BEAT, vel=0.9),
                         at(bar, beat, 0.018 + j * 0.006 + rng.normal(0, 0.004)),
                         gain=0.075, pan_=(-0.22 + 0.16 * j))

    # ---------- 旋律：中段进入，用同一台电钢琴的高音区
    for i, phrase in enumerate(MELODY):
        bar = 8 + i
        for beat, dur, m in phrase:
            note = ep(hz(m), dur * BEAT * 1.05)
            lead.add(echo(note, delay=BEAT * 0.75, feedback=0.20, mix=0.16),
                     at(bar, beat, rng.normal(0, 0.006)), gain=0.16, pan_=0.18)

    # ---------- 贝斯：每小节两个长音，很闷
    for bar, name in enumerate(PROGRESSION):
        if bar >= 18:
            continue
        for beat, dur in ((0.0, 1.8), (2.5, 1.4)):
            low.add(bass(hz(BASS[name]), dur * BEAT, cutoff=300, sub=0.7),
                    at(bar, beat), gain=0.20)

    # ---------- 鼓：底鼓 1、3 拍，军鼓 2、4 拍，踩镲带摇摆
    for bar in range(4, 18):
        drums.add(kick(tune=52, dur=0.5), at(bar, 0.0), gain=0.26)
        drums.add(kick(tune=52, dur=0.4), at(bar, 2.5), gain=0.16)
        for beat in (1.0, 3.0):
            drums.add(snare(dur=0.22), at(bar, beat), gain=0.13)
        for i in range(8):
            pos = i * 0.5 * BEAT + (SWING if i % 2 else 0.0)
            drums.add(hat(), at(bar) + pos, gain=0.045, pan_=0.2)
            if i % 2 == 1 and rng.random() < 0.45:
                drums.add(hat(dur=0.06), at(bar) + pos + 0.09, gain=0.022, pan_=-0.3)

    # ---------- 黑胶底噪铺满全曲
    noise.add(vinyl(DUR), 0.0, gain=0.5)

    # ---------- 总线：低通 + 磁带抖动 + 混响
    dry = keys.buf + low.buf + drums.buf * 0.9
    wet = reverb(lead.buf, dur=2.2, mix=0.28, damp=3800) + reverb(keys.buf, dur=1.8, mix=0.16, damp=3600)
    mix = dry + wet + noise.buf
    mix = lowpass(mix, 11000)
    mix = tape(mix, wow=0.0016, flutter=0.0005)
    return render(out / "05_midnight_radio.wav", mix, fade=(0.05, 3.0), drive=0.08)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
