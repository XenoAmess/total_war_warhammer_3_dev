"""Export the project's own geometric Workshop cover as a small PNG."""
from pathlib import Path
import argparse

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def render(output: Path):
    scale = 2
    image = Image.new('RGB', (512 * scale, 512 * scale), '#111b24')
    d = ImageDraw.Draw(image)
    gold, white = '#bba367', '#f6f1e4'

    def text(x, y, value, size, color=white, chinese=False):
        font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc' if chinese else 'C:/Windows/Fonts/segoeui.ttf', size * scale)
        d.text((x * scale, y * scale), value, font=font, fill=color, anchor='mm')

    def line(points, width=3):
        d.line([(x * scale, y * scale) for x, y in points], fill=gold, width=width * scale, joint='curve')

    d.rounded_rectangle((40, 40, 984, 984), radius=24, outline=gold, width=4)
    text(256, 63, 'WARHAMMER III · CAMPAIGN MOD', 17, gold)
    text(256, 132, '招募候选刷新', 45, chinese=True)
    line([(58, 186), (454, 186)], 1)

    # Single centered person + refresh arrow icon
    # Person
    d.ellipse((468, 482, 556, 570), outline=gold, width=10)
    d.arc((422, 568, 602, 748), 180, 360, fill=gold, width=10)

    # Refresh arrow (circular)
    d.arc((332, 410, 692, 770), 40, 325, fill=gold, width=12)
    line([(330, 243), (307, 243)], 6)
    line([(330, 243), (330, 266)], 6)

    text(256, 440, 'RECRUITMENT REFRESH', 17, gold)
    text(256, 474, 'XenoAmess · 0.2.0 Alpha', 13, '#8999a5')
    output.parent.mkdir(parents=True, exist_ok=True)
    image.resize((512, 512), Image.Resampling.LANCZOS).save(output, optimize=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'build/preview.png')
    args = parser.parse_args()
    render(args.output)
    print(args.output)
