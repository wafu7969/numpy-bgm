"""示例 4 · 山河入梦 —— 68 BPM，D 宫五声音阶。

情绪：远山、宣纸、慢镜头。用拨弦音色模仿古筝，低音鼓与沙锤只做点缀，
主旋律完全落在 D、E、F♯、A、B 五个音上。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (SR, Track, bell, echo, pad, pluck, reverb, shaker, tom)

BPM = 68
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 18
DUR = BARS * BAR + 3.5

VOICING = {
    "D": [50, 57, 62, 66],
    "Bm": [47, 54, 59, 62],
    "G": [43, 50, 55, 59],
    "A": [45, 52, 57, 61],
}
BASS = {"D": "D2", "Bm": "B2", "G": "G2", "A": "A2"}

PROGRESSION = ["D", "Bm", "G", "A"] * 3 + ["G", "A", "D", "D", "D", "D"]

MELODY = [
    [(0, 1, 69), (1, .5, 71), (1.5, 1.5, 74), (3, 1, 69)],
    [(0, 1, 71), (1, 1, 74), (2, 1, 71), (3, 1, 66)],
    [(0, 1.5, 74), (1.5, .5, 71), (2, 1, 66), (3, 1, 69)],
    [(0, 2, 69), (2, .5, 66), (2.5, .5, 64), (3, 1, 66)],
    [(0, 1, 74), (1, .5, 76), (1.5, 1.5, 78), (3, 1, 74)],
    [(0, 1, 71), (1, 1, 74), (2, 2, 76)],
    [(0, 1, 74), (1, .5, 71), (1.5, .5, 69), (2, 1, 66), (3, 1, 69)],
    [(0, 2, 69), (2, 2, 62)],
    # 第 13-16 小节：加花
    [(0, .5, 66), (.5, .5, 69), (1, 1, 71), (2, .5, 74), (2.5, .5, 76), (3, 1, 74)],
    [(0, .5, 69), (.5, .5, 71), (1, 1, 74), (2, 2, 76)],
    [(0, 1, 78), (1, .5, 76), (1.5, 1.5, 74), (3, 1, 69)],
    [(0, 2, 74), (2, 2, 69)],
]

INTRO = [
    [(0, 1, 62), (1, 1, 69), (2, 1, 74), (3, 1, 69)],
    [(0, 1, 71), (1, 1, 74), (2, 1, 71), (3, 1, 66)],
    [(0, 1.5, 74), (1.5, .5, 71), (2, 1, 66), (3, 1, 69)],
    [(0, 2, 69), (2, 2, 62)],
]


def main(out: Path) -> Path:
    melody = Track(DUR)
    texture = Track(DUR)
    low = Track(DUR)
    perc = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # ---------- 持续低音（D2 + A2），从头到尾托住整首曲子
    for m, level in (("D2", 0.16), ("A2", 0.07)):
        t = np.arange(int(DUR * SR)) / SR
        wave = np.sin(2 * np.pi * hz(m) * t)
        envelope = 0.6 + 0.4 * np.sin(2 * np.pi * 0.045 * t - 1.0) ** 2
        low.add(wave * envelope, 0.0, gain=level)

    # ---------- 拨弦旋律：主歌 + 加花 + 前奏
    for i, phrase in enumerate(INTRO):
        for beat, dur, m in phrase:
            note = pluck(hz(m), dur * BEAT * 1.2, bright=0.55)
            melody.add(echo(note, delay=BEAT * 0.75, feedback=0.30, mix=0.22),
                       at(i, beat), gain=0.16, pan_=0.15)
    for i, phrase in enumerate(MELODY):
        bar = 4 + i
        for beat, dur, m in phrase:
            note = pluck(hz(m), dur * BEAT * 1.15, bright=0.62)
            melody.add(echo(note, delay=BEAT * 0.75, feedback=0.32, mix=0.24),
                       at(bar, beat), gain=0.24, pan_=0.12)

    # ---------- 弦乐铺底：每小节一层，很轻
    for bar, name in enumerate(PROGRESSION):
        if bar < 2:
            continue
        for j, m in enumerate(VOICING[name][:3]):
            texture.add(pad(hz(m), BAR * 1.2, voices=2, detune=0.004,
                            cutoff=1100, attack=0.9),
                        at(bar), gain=0.040, pan_=(-0.45 + 0.3 * j))

    # ---------- 打击：鼓点只在 1、3 拍，沙锤打八分
    for bar in range(4, 18):
        perc.add(tom(tune=76, dur=0.6), at(bar, 0.0), gain=0.30)
        perc.add(tom(tune=82, dur=0.5), at(bar, 2.0), gain=0.18)
        for i in range(8):
            perc.add(shaker(), at(bar, i * 0.5),
                     gain=0.055 if i % 2 == 0 else 0.035,
                     pan_=0.32 if i % 2 else -0.2)
    # 段落缝隙里的木鱼声（用短促的高音拨弦代替）
    for bar in (3, 7, 11, 15):
        perc.add(pluck(hz(86), 0.18, bright=0.8), at(bar, 3.5), gain=0.12, pan_=-0.35)

    # ---------- 收尾：长音 + 高音钟
    for j, m in enumerate([50, 57, 62, 66, 74]):
        melody.add(pluck(hz(m), 5.0, bright=0.6), at(16) + j * 0.08, gain=0.16, pan_=-0.1)
    melody.add(bell(hz(86), 4.5), at(16, 0.2), gain=0.10, pan_=0.35)

    # ---------- 总线
    mix = (reverb(melody.buf, dur=3.6, mix=0.36, damp=4200)
           + low.buf
           + reverb(texture.buf, dur=4.5, mix=0.45, damp=2600)
           + perc.buf * 0.9)
    return render(out / "04_chinese_dream.wav", mix, fade=(0.05, 3.2))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
