"""示例 09 赛博之城 ——

情绪：赛博朋克、Synthwave、合成器浪潮、迷幻。
厚重的 Supersaw、锯齿贝斯、巨大的军鼓混响与复古琶音。

### 核心编曲与声音设计
1. 经典的 Synthwave 音色：
   - 使用了大量失谐的超级锯齿波（Supersaw）铺底，呈现出浓厚的八十年代复古未来主义色彩。
2. 标志性的门限混响军鼓 (Gated Reverb Snare)：
   - 军鼓上加了极大的混响，但混响时间被突然切断，这是 80 年代流行乐和赛博朋克音乐中最具标志性的鼓声设计，带来极其猛烈的打击感。
3. 16分音符的机械贝斯：
   - 密集的锯齿波低音以 16 分音符不断滚动，像是在雨夜的霓虹城市中高速驾驶。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import Track, supersaw, bass, lead, pad, kick, snare, hat, crash, reverb, echo, adsr, osc, _fit

BPM = 120
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 16
DUR = BARS * BAR + 4.0

PROGRESSION = (["Em", "C", "G", "D"] * 4)

VOICING = {
    "Em": [52, 55, 59, 64],
    "C": [48, 55, 60, 64],
    "G": [43, 55, 59, 62],
    "D": [50, 57, 62, 66],
}

BASS = {"Em": 40, "C": 36, "G": 43, "D": 38}

MELODY = [
    [(0, 1, 71), (1, 1, 76), (2, 2, 74)],
    [(0, 1, 76), (1, 1, 79), (2, 2, 74)],
    [(0, 1.5, 83), (1.5, .5, 81), (2, 1, 79), (3, 1, 76)],
    [(0, 4, 74)],
]

def synth_arp(freq, dur, vel=1.0):
    out = osc("saw", freq, dur, harmonics=20)
    env = adsr(dur, a=0.005, d=0.1, s=0.0, r=0.05)
    return _fit(out * env, vel)

def main(out: Path) -> Path:
    synths = Track(DUR)
    low = Track(DUR)
    arp = Track(DUR)
    drums = Track(DUR)
    snare_track = Track(DUR) # 单独给军鼓加巨大混响

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # Supersaw 和弦
    for bar, name in enumerate(PROGRESSION):
        if bar >= 4:
            for j, m in enumerate(VOICING[name]):
                synths.add(supersaw(hz(m), BAR, voices=5, cutoff=2800),
                           at(bar), gain=0.12, pan_=(-0.3 + 0.2 * j))

    # 锯齿贝斯 (16 分音符脉冲)
    for bar, name in enumerate(PROGRESSION):
        root = BASS[name]
        for step in range(16):
            if step == 15 and bar % 4 == 3:
                continue
            low.add(bass(hz(root), BEAT * 0.22, cutoff=800, sub=0.8),
                    at(bar, step * 0.25), gain=0.25)

    # 琶音 (Arp)
    for bar, name in enumerate(PROGRESSION):
        if bar >= 8:
            notes = VOICING[name]
            for step in range(16):
                m = notes[step % 4] + 12
                arp.add(synth_arp(hz(m), BEAT * 0.25), at(bar, step * 0.25), gain=0.1, pan_=0.25 if step % 2 else -0.25)

    # 旋律 (Lead)
    for bar in range(8, 16, 4):
        for i, phrase in enumerate(MELODY):
            for beat, dur, m in phrase:
                note = lead(hz(m + 12), dur * BEAT)
                synths.add(echo(note, delay=BEAT * 0.75, feedback=0.3, mix=0.3),
                           at(bar + i, beat), gain=0.18, pan_=0.0)

    # 鼓组 (4 on the floor + 80s Snare)
    for bar in range(BARS):
        for beat in (0.0, 1.0, 2.0, 3.0):
            drums.add(kick(tune=52), at(bar, beat), gain=0.4)
        for beat in (1.0, 3.0):
            # 军鼓，单独放一轨加长混响
            snare_track.add(snare(dur=0.4), at(bar, beat), gain=0.3)
        for beat in np.arange(0.5, 4.0, 0.5):
            drums.add(hat(open_=False), at(bar, beat), gain=0.08, pan_=0.1)

    for bar in (0, 4, 8, 12):
        drums.add(crash(), at(bar), gain=0.2, pan_=-0.1)

    # 收尾
    low.add(bass(hz(40), BAR * 1.5, cutoff=600, sub=0.8), at(BARS), gain=0.25)
    synths.add(supersaw(hz(52), BAR * 1.5, cutoff=1500), at(BARS), gain=0.15)
    drums.add(crash(), at(BARS), gain=0.2)

    # 混音：巨大的 Synthwave 混响
    snare_bus = reverb(snare_track.buf, dur=2.5, mix=0.5, damp=4000)
    synth_bus = reverb(synths.buf, dur=1.8, mix=0.25, damp=5000)
    arp_bus = echo(arp.buf, delay=BEAT * 0.5, feedback=0.4, mix=0.2)
    
    mix = synth_bus + low.buf + arp_bus + drums.buf + snare_bus
    return render(out / "09_cyber_city.wav", mix, fade=(0.02, 3.0))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
