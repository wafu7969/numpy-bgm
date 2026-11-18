"""示例 3 · 白噪音之前 —— 60 BPM 的自由速度，D♭ 大调。

情绪：清晨、空房间、还没开始的一天。没有鼓，只有长音量的铺底、
一个持续的低音和几颗很远的钟。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import SR, Track, bell, highpass, lowpass, osc, pad, reverb, samples, timeline

SECTION = 10.0
SECTIONS = 6
DUR = SECTION * SECTIONS + 6.0

PADS = [
    [49, 56, 60, 63, 68],
    [46, 53, 56, 61, 65],
    [42, 49, 53, 58, 61],
    [44, 46, 51, 56, 63],
    [49, 53, 56, 60, 63],
    [49, 56, 60, 63, 68],
]

# (进入时间, midi)：D♭ 大调五声音阶上的散点
BELLS = [
    (4.0, 73), (7.5, 68), (12.0, 75), (17.0, 77), (22.0, 73), (27.0, 70),
    (32.0, 75), (37.0, 80), (42.0, 77), (47.0, 73), (52.0, 75), (57.0, 68),
]


def main(out: Path) -> Path:
    pads = Track(DUR)
    drone = Track(DUR)
    bells = Track(DUR)
    air = Track(DUR)

    # ---------- 铺底：每 10 秒换一次和声，长起音 + 长释放，靠重叠融合
    for i, notes in enumerate(PADS):
        start = i * SECTION
        for j, m in enumerate(notes):
            pads.add(pad(hz(m), SECTION * 1.35, voices=3, detune=0.0055,
                         cutoff=900, attack=2.4),
                     start, gain=0.055, pan_=(-0.5 + 0.25 * j))

    # ---------- 持续低音：D♭2 + A♭2，带极慢的呼吸
    n = samples(SECTION * SECTIONS, SR)
    t = timeline(SECTION * SECTIONS, SR)
    breath = 0.55 + 0.45 * np.sin(2 * np.pi * 0.035 * t - 1.2) ** 2
    for m, level in ((37, 0.20), (44, 0.11)):
        drone.add(osc("sine", hz(m), SECTION * SECTIONS, SR) * breath, 0.0, gain=level)

    # ---------- 空气：被切掉低频的噪声，随和声一起起伏
    noise = np.random.default_rng(7).standard_normal(n)
    noise = lowpass(highpass(noise, 400, SR), 2400, SR)
    noise *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)
    air.add(noise, 0.0, gain=0.018, pan_=0.0)

    # ---------- 钟：稀疏、远、每个都带长混响
    for start, m in BELLS:
        bells.add(bell(hz(m), 6.5), start, gain=0.16, pan_=(-0.4 if m % 2 else 0.4))

    # ---------- 总线：氛围曲的混响给得很大方
    mix = (reverb(pads.buf, dur=6.0, mix=0.55, damp=3000)
           + drone.buf * 0.9
           + reverb(bells.buf, dur=7.0, mix=0.60, damp=4200)
           + air.buf)
    return render(out / "03_before_noise.wav", mix, fade=(0.5, 4.0))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
