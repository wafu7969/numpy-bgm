"""一次性渲染全部示例曲目。

    python generate_all.py

WAV 会写到 output/ 目录，可以直接拖进任何播放器或剪辑软件。
"""

import time
from pathlib import Path

from examples import (before_noise, cyber_city, chinese_dream, pixel_memories,
                      midnight_radio, neon_night, orbit, sfx_showcase,
                      summer_letter, toward_the_light, war_drums)

MODULES = [
    toward_the_light,
    summer_letter,
    neon_night,
    before_noise,
    chinese_dream,
    midnight_radio,
    orbit,
    pixel_memories,
    cyber_city,
    war_drums,
    sfx_showcase,
]


def main() -> None:
    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    start = time.time()
    for module in MODULES:
        t0 = time.time()
        module.main(out)
        print(f"   {module.__name__}  用时 {time.time() - t0:.1f}s")
    print(f"\n全部完成：{len(MODULES)} 首，共 {time.time() - start:.1f}s -> {out}")


if __name__ == "__main__":
    main()
