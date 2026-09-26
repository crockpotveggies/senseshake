"""Compose the existing favicon and Segoe UI Bold as a self-contained SVG.

Build-only dependency: fonttools. No font file is shipped or required at runtime.
Run on Windows: python sw/ui/build_wordmark.py --font C:/Windows/Fonts/segoeuib.ttf
"""
import argparse
import base64
from pathlib import Path


def build(font_path):
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen

    assets = Path(__file__).parent / 'assets'
    font = TTFont(font_path)
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = 40 / font['head'].unitsPerEm
    x = 84
    paths = []
    for letter in 'Groundlark':
        name = cmap[ord(letter)]
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 47)))
        paths.append(f'<path d="{pen.getCommands()}"/>')
        x += font['hmtx'][name][0] * scale - 0.8
    width = round(x + 14)
    png = base64.b64encode((assets / 'groundlark-icon.png').read_bytes()).decode('ascii')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {width} 72" role="img" aria-labelledby="title desc">
<title id="title">Groundlark</title>
<desc id="desc">Lark with a seismic waveform tail, beside the Groundlark name in Segoe UI Bold.</desc>
<rect width="{width}" height="72" rx="10" fill="#0d131c"/>
<image x="4" y="4" width="64" height="64" xlink:href="data:image/png;base64,{png}"/>
<g fill="#e2ebf4">{''.join(paths)}</g>
</svg>
'''
    (assets / 'groundlark-wordmark.svg').write_text(svg, encoding='utf-8')
    font.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', required=True, type=Path)
    build(parser.parse_args().font)
