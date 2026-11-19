"""示例 12 · 机器合唱 —— 使用共振峰合成演唱“我爱你中国”

### 核心编曲与声音设计
1. 动态双元音 (Diphthongs) 与滑音：
   - 为了让机器“说话”，程序不仅要生成静态的元音，还要在两个元音之间平滑过渡（Crossfade）。例如“我 (Wo)”是 u 过渡到 o，“爱 (Ai)”是 a 过渡到 i。
   - “国 (Guo)”这个字加入了从 A4 到 G4 的平滑音高下滑（Portamento）。
2. 大规模人声叠置 (Choir Layering)：
   - 仅有一个声音听起来太单薄，因此这里叠加了主音色、低八度的男低音（Sub）、以及轻微失调（Detuned）的伴唱，组合成了一个史诗感的“机器合唱团”。
3. scipy 滤波器优化：
   - 使用 scipy.signal.lfilter 替代了原先的纯 Python for 循环，让复杂的共振峰带通滤波计算速度提升了上百倍。
4. 大教堂混响 (Cathedral Reverb)：
   - 利用多重延迟（Multi-tap Delay）和低通滤波，构建了一个巨大的空间混响，掩盖了纯数字合成的干涩感，营造出神圣的听感。
"""

import numpy as np
from pathlib import Path
from scipy.io import wavfile
from scipy.signal import lfilter, butter

# 共振峰参数 (F1, F2, F3 频率与带宽)
FORMANTS = {
    'a': [(730, 109), (1090, 119), (2440, 131)],
    'e': [(530,  77), (1840, 128), (2480, 138)],
    'i': [(270,  53), (2290, 201), (3010, 212)],
    'o': [(570,  73), ( 840,  92), (2410, 131)],
    'u': [(300,  59), ( 870,  92), (2240, 119)],
}

def bp_filter(signal, sr, f_c, bw):
    """基于 scipy.signal.lfilter 的极速带通滤波器"""
    w_c = 2 * np.pi * f_c / sr
    w_b = 2 * np.pi * bw / sr
    alpha = np.sin(w_c) * np.sinh(np.log(2) / 2 * w_b * w_c / np.sin(w_c))
    
    a0 = 1 + alpha
    b0 = alpha / a0
    b1 = 0
    b2 = -alpha / a0
    a1 = -2 * np.cos(w_c) / a0
    a2 = (1 - alpha) / a0
    
    return lfilter([b0, b1, b2], [1.0, a1, a2], signal)

def make_vowel(freq_array, vowel, sr=44100):
    t = np.arange(len(freq_array)) / sr
    # 加入 5.5Hz 的真实人声颤音
    vibrato = 0.015 * freq_array * np.sin(2 * np.pi * 5.5 * t)
    phase = np.cumsum(2 * np.pi * (freq_array + vibrato) / sr)
    
    # 锯齿波作为声带激励源
    source = 2 * (phase / (2 * np.pi) - np.floor(0.5 + phase / (2 * np.pi)))
    # 低通削弱高频，模拟真实声带滚降
    source = np.convolve(source, np.ones(5)/5, mode='same')
    
    out = np.zeros_like(source)
    for f_c, bw in FORMANTS[vowel]:
        out += bp_filter(source, sr, f_c, bw)
    return out

def make_word(freq_start, freq_end, vowels, duration, sr=44100):
    length = int(sr * duration)
    t = np.arange(length) / sr
    
    # 平滑的音高过渡 (Portamento)
    if freq_start == freq_end:
        freq_array = np.full(length, float(freq_start))
    else:
        curve = (1 - np.cos(np.pi * t / duration)) / 2
        freq_array = freq_start + (freq_end - freq_start) * curve
        
    # 双元音交叉渐变 (Crossfade)
    if len(vowels) == 1:
        audio = make_vowel(freq_array, vowels[0], sr)
    else:
        v1 = make_vowel(freq_array, vowels[0], sr)
        v2 = make_vowel(freq_array, vowels[1], sr)
        fade_in = np.linspace(0, 1, length)
        audio = v1 * (1 - fade_in) + v2 * fade_in
        
    # 词语首尾的呼吸包络
    env = np.ones(length)
    fade_len = int(sr * 0.1)
    if length > fade_len * 2:
        env[:fade_len] = np.linspace(0, 1, fade_len)
        env[-fade_len:] = np.linspace(1, 0, fade_len)
        
    return audio * env * 0.1

def make_choir_word(f1, f2, vowels, dur, sr=44100):
    # 主声部
    v_main = make_word(f1, f2, vowels, dur, sr)
    # 男低音 (低八度)
    v_sub = make_word(f1/2, f2/2, vowels, dur, sr) * 0.5
    # 伴唱 (轻微失调，增加厚度)
    v_det1 = make_word(f1*1.008, f2*1.008, vowels, dur, sr) * 0.3
    v_det2 = make_word(f1*0.992, f2*0.992, vowels, dur, sr) * 0.3
    return v_main + v_sub + v_det1 + v_det2

def main(out_dir: Path) -> None:
    sr = 44100
    
    # 旋律：我爱你中国 (Wo Ai Ni Zhong Guo)
    words = [
        (392.00, 392.00, ['u', 'o'], 0.8), # 我 (G4)
        (329.63, 329.63, ['a', 'i'], 0.4), # 爱 (E4)
        (392.00, 392.00, ['i'],      0.4), # 你 (G4)
        (523.25, 523.25, ['o', 'u'], 1.2), # 中 (C5)
        (440.00, 392.00, ['u', 'o'], 2.5)  # 国 (A4 -> G4 滑音)
    ]
    
    audio_parts = []
    for f1, f2, vowels, dur in words:
        audio_parts.append(make_choir_word(f1, f2, vowels, dur, sr))
        # 字与字之间的短暂停顿
        audio_parts.append(np.zeros(int(sr * 0.08)))
        
    audio = np.concatenate(audio_parts)
    
    # 大教堂混响
    wet = np.zeros(len(audio) + int(sr * 3.0))
    wet[:len(audio)] = audio
    
    for i in range(1, 12):
        delay = int(sr * 0.15 * i)
        decay = 0.6 ** i
        wet[delay:delay+len(audio)] += audio * decay
        
    b, a = butter(2, 2000 / (sr/2), btype='low')
    wet = lfilter(b, a, wet)
    
    out = np.zeros_like(wet)
    out[:len(audio)] += audio * 0.8
    out += wet * 0.6
    
    out = np.clip(out, -1, 1)
    out = np.int16(out * 32767)
    
    out_file = out_dir / "12_vocal_choir.wav"
    wavfile.write(out_file, sr, out)

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "output"
    out.mkdir(exist_ok=True)
    main(out)
