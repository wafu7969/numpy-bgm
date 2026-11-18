# numpy-bgm

只用 **numpy + 标准库** 写 BGM 的实验仓库。没有音源、没有采样包、没有 DAW，
每一个音符都是逐样本算出来的。

仓库里包含 5 首可以直接听的完整曲子（WAV/MP3）和生成它们的全部代码：

| # | 曲目 | 风格 | BPM | 调性 | 情绪 |
|---|------|------|-----|------|------|
| 01 | [夏日信笺](demos/01_summer_letter.mp3) | 钢琴叙事 | 76 | C 大调 | 午后、信纸、慢镜头 |
| 02 | [霓虹夜行](demos/02_neon_night.mp3) | 电子 / EDM | 122 | A 小调 | 夜路、车灯、肾上腺素 |
| 03 | [白噪音之前](demos/03_before_noise.mp3) | 氛围 Ambient | 自由 | D♭ 大调 | 清晨、空房间 |
| 04 | [山河入梦](demos/04_chinese_dream.mp3) | 中国风 | 68 | D 宫五声 | 远山、宣纸、留白 |
| 05 | [深夜电台](demos/05_midnight_radio.mp3) | Lo-Fi Hip-Hop | 78 | C 大调 | 凌晨两点、台灯、日记 |

> GitHub 页面里点上面的文件名即可在线试听；`output/` 下是渲染出来的 44.1kHz/16bit WAV。

## 快速开始

```bash
pip install numpy          # 唯一的依赖
python generate_all.py     # 一次渲染 5 首，输出到 output/
```

单独渲染某一首：

```bash
python -m examples.summer_letter
python -m examples.neon_night
python -m examples.before_noise
python -m examples.chinese_dream
python -m examples.midnight_radio
```

## 目录结构

```
numpy-bgm/
├── bgm/
│   ├── synth.py        # 振荡器、包络、滤波、混响、鼓组、总线、导出
│   └── notation.py     # 音名 / 音阶 / 和弦 / 摇摆
├── examples/
│   ├── summer_letter.py    # 01 温暖钢琴
│   ├── neon_night.py       # 02 电子
│   ├── before_noise.py     # 03 氛围
│   ├── chinese_dream.py    # 04 中国风
│   └── midnight_radio.py   # 05 Lo-Fi
├── demos/              # 试听用的 MP3
├── output/             # 渲染结果（gitignore）
└── generate_all.py
```

## 三分钟写出第一段声音

```python
import numpy as np
from bgm.synth import piano, reverb, master, write_wav
from bgm import hz

SR = 44100

# C - G/B - Am - F 四个和弦，每个两拍
chords = [[60, 64, 67], [59, 62, 67], [57, 60, 64], [57, 60, 65]]
buf = np.zeros(int(10 * SR))

for i, chord in enumerate(chords):
    for m in chord:
        note = piano(hz(m), 2.4)          # 合成一个音
        start = int(i * 2 * SR)
        buf[start:start + len(note)] += note * 0.2

buf = reverb(buf, dur=2.4, mix=0.3)   # 加空间
write_wav("first.wav", master(buf))   # 母带并导出
```

## 它是怎么工作的

1. **采样**：所有声音都是一条长度为 `秒数 × 44100` 的 float 数组。
2. **波形**：`osc()` 用叠加谐波的方式生成正弦 / 锯齿 / 方波 / 三角波，并按奈奎斯特频率截断，避免混叠。
3. **包络**：`adsr()` 决定声音怎么出现、怎么消失——这是“像乐器”的关键。
4. **音色**：`piano()` 叠加衰减谐波，`ep()` 用两算子 FM 做 Rhodes，`pluck()` 用高次谐波快速衰减模仿拨弦，`pad()` 是多个失谐锯齿再低通。
5. **滤波**：`lowpass / highpass / bandpass` 全部用 FFT 实现，零相位、无逐样本循环，几十秒音频也是毫秒级。
6. **空间**：`reverb()` 用指数衰减噪声当脉冲响应做卷积混响，`echo()` 是多抽头延迟。
7. **编排**：`Track` 是一条时间线，`track.add(声音, at=秒)` 把音符放到任意位置，最后一次性导出。
8. **总线**：`master()` 负责淡入淡出、软削波与 -1dBFS 归一化；`write_wav()` 用标准库 `wave` 写 16bit PCM。

## 一些实践里的坑

- **相位要连续**：滑音、颤音用 `cumsum(freq)` 积分出相位，直接 `sin(2πft)` 会爆音。
- **归一化单音**：每个音先归一化到固定峰值再乘力度，否则低音会盖住高音。
- **混响别给太多**：氛围曲可以 50%+，流行/电子通常 20%~30%，否则会糊。
- **母带只做一件事**：保证峰值在 -1dBFS 附近，不要指望在 numpy 里做真正的母带。
- **渲染慢就查循环**：单个音符内部的 Python 循环可以接受，但不要在样本级别循环。

## 想做自己的曲子

1. 定 BPM 与调性，写 4 或 8 小节的和弦进行（`bgm.notation.chord` 能直接生成）；
2. 先铺低音和 Pad，确定速度与和声；
3. 写主旋律，让强拍落在和弦音上，弱拍用经过音；
4. 加鼓组与打击，注意留白；
5. 给每个声部一点声像与混响差异，最后用 `master()` 收口。

## License

MIT，见 [LICENSE](LICENSE)。随意使用、修改，商用也无需署名。
