"""示例 12 · 机器合唱 —— 使用共振峰合成的人声演唱

### 核心编曲与声音设计
1. 声带模拟 (Vocal Fold)：
   - 使用带有颤音 (Vibrato) 和滑音 (Portamento) 的低通锯齿波模拟人类声带的基础脉冲。
2. 口腔共鸣 (Vocal Tract & Formants)：
   - 人的元音由口腔的共振频率决定。这里使用了三组带通滤波器 (Bandpass Filters) 来模拟发 a、e、i、o、u 时的前三个共振峰 (F1, F2, F3)。
3. 歌词包络与切换：
   - 将不同的元音按旋律节奏拼接，辅以平滑的过渡，让程序“唱”出一段类似于“啊-哦-衣-欸”的机器感合唱。
"""

import numpy as np
from pathlib import Path
from scipy.io import wavfile

# 共振峰参数 (F1, F2, F3 频率与带宽)
FORMANTS = {
    'a': [(730, 109), (1090, 119), (2440, 131)],
    'e': [(530,  77), (1840, 128), (2480, 138)],
    'i': [(270,  53), (2290, 201), (3010, 212)],
    'o': [(570,  73), ( 840,  92), (2410, 131)],
    'u': [(300,  59), ( 870,  92), (2240, 119)],
}

def bp_filter(signal, sr, f_c, bw):
    """带通滤波器 (基于双二阶滤波器模拟共振峰)"""
    w_c = 2 * np.pi * f_c / sr
    w_b = 2 * np.pi * bw / sr
    alpha = np.sin(w_c) * np.sinh(np.log(2) / 2 * w_b * w_c / np.sin(w_c))
    
    a0 = 1 + alpha
    b0 = alpha
    b1 = 0
    b2 = -alpha
    a1 = -2 * np.cos(w_c)
    a2 = 1 - alpha
    
    b0, b1, b2, a1, a2 = b0/a0, b1/a0, b2/a0, a1/a0, a2/a0
    
    y = np.zeros_like(signal)
    x = signal
    for i in range(2, len(x)):
        y[i] = b0 * x[i] + b1 * x[i-1] + b2 * x[i-2] - a1 * y[i-1] - a2 * y[i-2]
    return y

def make_vowel(freq, vowel, duration, sr=44100):
    t = np.arange(int(sr * duration)) / sr
    
    # 1. 模拟声带 (带颤音的锯齿波)
    vibrato = 0.015 * freq * np.sin(2 * np.pi * 5.5 * t)  # 5.5Hz 颤音
    phase = np.cumsum(2 * np.pi * (freq + vibrato) / sr)
    source = 2 * (phase / (2 * np.pi) - np.floor(0.5 + phase / (2 * np.pi)))
    
    # 低通削弱高频，模拟真实的声带滚降
    source = np.convolve(source, np.ones(5)/5, mode='same')
    
    # 2. 口腔共鸣 (并联带通滤波器)
    out = np.zeros_like(source)
    for f_c, bw in FORMANTS[vowel]:
        out += bp_filter(source, sr, f_c, bw)
        
    # 3. 呼吸包络
    env = np.ones_like(t)
    fade_len = int(sr * 0.1)
    if len(env) > fade_len * 2:
        env[:fade_len] = np.linspace(0, 1, fade_len)
        env[-fade_len:] = np.linspace(1, 0, fade_len)
    
    return out * env * 0.1

def main(out_dir: Path) -> None:
    sr = 44100
    
    # 旋律：欢乐颂片段 (C大调: E E F G | G F E D)
    # 对应音节：a  e  i  o | u  a  e  i
    melody = [
        (329.63, 'a', 0.5), (329.63, 'e', 0.5), (349.23, 'i', 0.5), (392.00, 'o', 0.5),
        (392.00, 'u', 0.5), (349.23, 'a', 0.5), (329.63, 'e', 0.5), (293.66, 'i', 0.5)
    ]
    
    voice = []
    for freq, vowel, dur in melody:
        voice.append(make_vowel(freq, vowel, dur, sr))
        
    audio = np.concatenate(voice)
    
    # 加上大混响，掩盖机器感
    delay_len = int(sr * 0.3)
    wet = np.zeros(len(audio) + delay_len)
    wet[:len(audio)] = audio
    wet[delay_len:] += audio * 0.4
    audio = wet
    
    # 标准化并导出
    audio = np.clip(audio, -1, 1)
    audio = np.int16(audio * 32767)
    
    out_file = out_dir / "12_vocal_choir.wav"
    wavfile.write(out_file, sr, audio)

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    main(out)
