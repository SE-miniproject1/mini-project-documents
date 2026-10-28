"""Turn the frames saved by record_demo.js into an H.264 video at a steady 10 frames a second.

Usage:  python tools/demo/encode_video.py <frames folder> <output.mp4>
Needs:  pip install imageio imageio-ffmpeg pillow numpy
"""

import json
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image

FPS = 10


def main(frames_dir, output):
    frames_dir = Path(frames_dir)
    stamps = json.loads((frames_dir / "frames.json").read_text())
    total = int((stamps[-1] - stamps[0]) * FPS) + 1
    writer = imageio.get_writer(
        output, fps=FPS, codec="libx264", pixelformat="yuv420p", macro_block_size=None, quality=7
    )
    index, current = 0, None
    for n in range(total):
        moment = stamps[0] + n / FPS
        while index + 1 < len(stamps) and stamps[index + 1] <= moment:
            index += 1
            current = None
        if current is None:
            current = np.asarray(Image.open(frames_dir / f"f{index:05d}.jpg").convert("RGB"))
        writer.append_data(current)
    writer.close()
    print(f"{total} frames, {total / FPS:.1f} seconds")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
