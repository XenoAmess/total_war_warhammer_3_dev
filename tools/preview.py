"""Export the project's own geometric Workshop cover as a small PNG."""
from pathlib import Path

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
    text(256, 132, '征募与迁都', 53, chinese=True)
    line([(58, 186), (454, 186)], 1)
    d.arc((120, 448, 380, 708), 35, 300, fill=gold, width=12)
    line([(176, 244), (145, 244)], 6)
    line([(176, 244), (176, 275)], 6)
    d.ellipse((216, 524, 284, 592), outline=gold, width=10)
    d.arc((188, 586, 312, 694), 195, 345, fill=gold, width=10)
    line([(300, 328), (300, 252), (322, 252), (322, 278), (342, 278), (342, 252),
          (365, 252), (365, 278), (385, 278), (385, 252), (407, 252), (407, 328), (300, 328)], 6)
    line([(344, 328), (344, 300), (366, 300), (366, 328)], 6)
    line([(310, 234), (354, 211), (397, 234)], 6)
    text(128, 371, '刷新候选', 25, chinese=True)
    text(354, 371, '迁移首都', 25, chinese=True)
    text(256, 440, 'RECRUITMENT + CAPITALS', 17, gold)
    text(256, 474, 'XenoAmess · 0.1.0 Alpha', 13, '#8999a5')
    output.parent.mkdir(parents=True, exist_ok=True)
    image.resize((512, 512), Image.Resampling.LANCZOS).save(output, optimize=True)


if __name__ == '__main__':
    target = ROOT / 'build/preview.png'
    render(target)
    print(target)
