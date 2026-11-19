"""一次性渲染全部示例曲目。

    python generate_all.py

WAV 会写到 output/ 目录，可以直接拖进任何播放器或剪辑软件。
"""

import time
from pathlib import Path
import importlib

MODULE_NAMES = [
    "01_toward_the_light",
    "02_summer_letter",
    "03_neon_night",
    "04_before_noise",
    "05_chinese_dream",
    "06_midnight_radio",
    "07_orbit",
    "08_pixel_memories",
    "09_cyber_city",
    "10_war_drums",
    "11_sfx_showcase",
]

def main() -> None:
    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    start = time.time()
    for name in MODULE_NAMES:
        module = importlib.import_module(f"examples.{name}")
        t0 = time.time()
        module.main(out)
        print(f"   {name}  用时 {time.time() - t0:.1f}s")
    print(f"\n全部完成：{len(MODULE_NAMES)} 首，共 {time.time() - start:.1f}s -> {out}")


if __name__ == "__main__":
    main()
