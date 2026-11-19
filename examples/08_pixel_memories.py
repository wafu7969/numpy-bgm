"""示例 08 像素回忆 ——

情绪：红白机、8-bit 游戏、芯片音乐、欢快跳跃。
纯使用方波、三角波与噪声，不加混响，致敬最原汁原味的电子游戏音乐。

### 核心编曲与声音设计
1. 原汁原味的芯片音乐 (Chiptune) 限制：
   - 严格致敬早期游戏机（如红白机 FC）的发声机制，全曲只使用了三种基本波形：方波（主旋律与和弦）、三角波（极其干净的低音）以及白噪声（模拟打击乐）。
2. 无混响的干涩感：
   - 全程不加任何空间混响，声音非常干脆、直接，带来了强烈的跳跃感和复古游戏氛围。
3. 高频的脉冲调制与琶音：
   - 主旋律使用了不同脉冲宽度的方波，并在和弦上使用了极速的琶音（Arpeggio）来弥补早期游戏机发声通道不足的问题，形成了芯片音乐标志性的听感。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import Track, osc, adsr, _fit

BPM = 150
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 16
DUR = BARS * BAR + 2.0

PROGRESSION = (["C", "G", "Am", "F"] * 2 + ["F", "G", "C", "C"] * 2)

VOICING = {
    "C": [48, 52, 55, 60],
    "G": [43, 47, 50, 55],
    "Am": [45, 48, 52, 57],
    "F": [41, 45, 48, 53],
}

BASS = {"C": 36, "G": 31, "Am": 33, "F": 29}

MELODY = [
    # 第一段：跳跃的动机
    [(0, .5, 72), (0.5, .5, 72), (1.5, .5, 72), (2.5, .5, 76), (3, 1, 79)],
    [(0, .5, 74), (0.5, .5, 74), (1.5, .5, 74), (2.5, .5, 71), (3, 1, 67)],
    [(0, .5, 76), (0.5, .5, 76), (1.5, .5, 76), (2.5, .5, 72), (3, 1, 69)],
    [(0, 2, 69), (2, 2, 71)],
] * 2 + [
    # 第二段：连贯的长句
    [(0, 1, 72), (1, 1, 76), (2, 1, 79), (3, 1, 84)],
    [(0, 1, 83), (1, 1, 79), (2, 2, 74)],
    [(0, 1, 72), (1, 1, 76), (2, 1, 79), (3, 1, 84)],
    [(0, 4, 84)],
] * 2


def square_lead(freq, dur, vel=1.0):
    """主音：带快速衰减包络的方波，25% 占空比(Pulse)的近似，用 square 凑合。"""
    out = osc("square", freq, dur, harmonics=15)
    env = adsr(dur, a=0.01, d=0.1, s=0.5, r=0.05, curve=2.0)
    return _fit(out * env, vel)

def triangle_bass(freq, dur, vel=1.0):
    """贝斯：三角波，红白机经典贝斯。"""
    out = osc("triangle", freq, dur, harmonics=10)
    env = adsr(dur, a=0.01, d=0.1, s=0.8, r=0.05)
    return _fit(out * env, vel)

def square_arp(freq, dur, vel=1.0):
    """琶音：极短的方波。"""
    out = osc("square", freq, dur, harmonics=10)
    env = adsr(dur, a=0.01, d=0.05, s=0.0, r=0.02)
    return _fit(out * env, vel)

def noise_snare(dur, vel=1.0):
    """白噪军鼓。"""
    out = osc("noise", 0, dur)
    env = adsr(dur, a=0.005, d=0.1, s=0.0, r=0.05)
    return _fit(out * env, vel)

def noise_hat(dur, vel=1.0):
    """白噪踩镲。"""
    out = osc("noise", 0, dur)
    env = adsr(dur, a=0.002, d=0.03, s=0.0, r=0.01)
    return _fit(out * env, vel)


def main(out: Path) -> Path:
    lead = Track(DUR)
    bass = Track(DUR)
    arp = Track(DUR)
    drums = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # 旋律
    for i, phrase in enumerate(MELODY):
        for beat, dur, m in phrase:
            lead.add(square_lead(hz(m), dur * BEAT), at(i, beat), gain=0.25)

    # 贝斯与琶音
    for bar, name in enumerate(PROGRESSION):
        # 贝斯
        root = BASS[name]
        for beat in (0.0, 0.5, 1.5, 2.0, 2.5, 3.5):
            bass.add(triangle_bass(hz(root), BEAT * 0.45), at(bar, beat), gain=0.3)
        
        # 琶音 (Arpeggio)
        notes = VOICING[name]
        for step in range(16):
            m = notes[step % len(notes)]
            arp.add(square_arp(hz(m + 12), BEAT * 0.25), at(bar, step * 0.25), gain=0.06)

    # 鼓组 (噪声)
    for bar in range(BARS):
        for beat in (1.0, 3.0):
            drums.add(noise_snare(BEAT * 0.3), at(bar, beat), gain=0.2)
        for beat in np.arange(0, 4, 0.5):
            drums.add(noise_hat(BEAT * 0.1), at(bar, beat), gain=0.1)

    # 结尾
    lead.add(square_lead(hz(72), BAR), at(BARS), gain=0.25)
    bass.add(triangle_bass(hz(36), BAR), at(BARS), gain=0.3)

    # 芯片音乐通常不需要混响，保持干声
    mix = lead.buf + bass.buf + arp.buf + drums.buf
    return render(out / "08_pixel_memories.wav", mix, fade=(0.01, 1.0))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
