"""示例 05 山河入梦 ——

情绪：远山、宣纸、留白。像坐火车经过一片山，山不说话。
底层的低频脉冲与沙锤模仿火车平稳的行驶，
宽广的 Pad 铺垫远山的轮廓，拨弦与钟声是偶尔掠过的风景。
主旋律极为克制，大量留白。

### 核心编曲与声音设计
1. 火车的节奏 (Train Rhythm)：
   - 用带有低通滤波的白噪声模拟铁轨的“隆隆”声，并通过包络线让其产生“滚过”的动态感。
   - 辅以极弱的高频沙锤（Shaker）模拟车轮与铁轨摩擦，以及沉闷的战鼓（Tom）模拟车厢压过铁轨接缝的沉闷声响。
2. 远山的轮廓 (Pad)：
   - 极慢起振和释放的合成器 Pad 被压在很低的频率下，像雾气和群山的轮廓，宽广且静谧。
3. 偶尔掠过的风景 (Melody & Bell)：
   - 主旋律极度克制，拨弦（模拟古筝/古琴）带着悠远的延迟混响。每段旋律开头有一声悠远的钟声（Bell）。
   - 旋律间留白时间极长，强化“山不说话”的清冷与孤独感。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (SR, Track, bell, echo, pad, pluck, reverb, shaker, tom, lowpass)

BPM = 68
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 20
DUR = BARS * BAR + 4.0

VOICING = {
    "D": [50, 57, 62, 66],
    "Bm": [47, 54, 59, 62],
    "G": [43, 50, 55, 59],
    "A": [45, 52, 57, 61],
}

PROGRESSION = ["D", "D", "Bm", "Bm", "G", "G", "A", "A"] * 2 + ["D", "D", "D", "D"]

# 旋律极简，留白
MELODY = [
    # 第一次 (Bar 4-7)
    [(0, 2, 69), (2, 1, 74), (3, 1, 71)],
    [(0, 4, 66)],
    [(0, 2, 62), (2, 1, 64), (3, 1, 69)],
    [(0, 4, 71)],
    
    # 第二次 (Bar 8-11)
    [(0, 1.5, 74), (1.5, .5, 76), (2, 2, 74)],
    [(0, 4, 69)],
    [(0, 1, 66), (1, 1, 69), (2, 2, 62)],
    [(0, 4, 62)],

    # 第三次 (Bar 12-15) - 高八度
    [(0, 2, 81), (2, 1, 86), (3, 1, 83)],
    [(0, 4, 78)],
    [(0, 2, 74), (2, 1, 76), (3, 1, 81)],
    [(0, 4, 83)],
]

def train_rumble(dur, vel=1.0, sr=SR):
    """模仿火车铁轨的隆隆声"""
    t = np.arange(int(dur * sr)) / sr
    noise = np.random.default_rng(int(dur*1000)).standard_normal(len(t))
    # 用低通滤波闷住，只留低频
    noise = lowpass(noise, 250, sr)
    # 包络：两头轻中间重，像是一个车厢滚过去
    env = np.sin(np.pi * t / dur) ** 2
    return noise * env * vel * 0.6

def main(out: Path) -> Path:
    melody = Track(DUR)
    texture = Track(DUR)
    perc = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # ---------- 1. 火车的节奏 (Train Rhythm)
    # 贯穿全曲的铁轨声：每拍两次滚动
    for bar in range(BARS - 2):
        for beat in range(4):
            # chug - chug
            perc.add(train_rumble(BEAT * 0.45), at(bar, beat), gain=0.35, pan_=-0.1)
            perc.add(train_rumble(BEAT * 0.45), at(bar, beat + 0.5), gain=0.25, pan_=0.1)
            
            # 沙锤增加高频摩擦感，像车轮
            perc.add(shaker(dur=0.1), at(bar, beat), gain=0.02, pan_=0.2)
            perc.add(shaker(dur=0.1), at(bar, beat + 0.5), gain=0.01, pan_=-0.2)
            
            # 偶尔的铁轨接缝声 (Tom 模拟)
            if beat == 0:
                perc.add(tom(tune=45, dur=0.8), at(bar, beat), gain=0.2)
            elif beat == 2.5:
                perc.add(tom(tune=50, dur=0.6), at(bar, beat), gain=0.12)

    # ---------- 2. 远山的轮廓 (Pad & Drone)
    for bar, name in enumerate(PROGRESSION):
        if bar < 2 or bar >= BARS - 2:
            continue
        # 极慢的 Pad，代表大山
        for j, m in enumerate(VOICING[name][:3]):
            texture.add(pad(hz(m - 12), BAR * 1.5, voices=3, detune=0.006,
                            cutoff=700, attack=1.5),
                        at(bar), gain=0.07, pan_=(-0.3 + 0.3 * j))

    # ---------- 3. 偶尔掠过的风景 (Melody & Bell)
    for i, phrase in enumerate(MELODY):
        bar = 4 + i
        for beat, dur, m in phrase:
            # 拨弦主旋律，极具空间感
            note = pluck(hz(m), dur * BEAT * 1.5, bright=0.45)
            melody.add(echo(note, delay=BEAT * 0.75, feedback=0.4, mix=0.35),
                       at(bar, beat), gain=0.24, pan_=0.0)
            
            # 每句的开头加一声悠远的钟声
            if beat == 0:
                melody.add(bell(hz(m + 12), dur * BEAT * 2.0),
                           at(bar, beat), gain=0.1, pan_=0.3)

    # ---------- 收尾：长音逐渐消散，火车远去
    texture.add(pad(hz(38), BAR * 3.0, cutoff=500, attack=2.0), at(BARS - 2), gain=0.08)
    melody.add(bell(hz(74), 6.0), at(BARS - 2), gain=0.1, pan_=-0.2)

    # ---------- 总线
    mix = (reverb(melody.buf, dur=4.0, mix=0.45, damp=3000)
           + reverb(texture.buf, dur=5.0, mix=0.55, damp=2000)
           + reverb(perc.buf, dur=1.5, mix=0.15, damp=6000))
           
    return render(out / "05_chinese_dream.wav", mix, fade=(0.05, 4.0))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")