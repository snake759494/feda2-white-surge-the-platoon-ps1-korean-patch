# 한글 <-> SJIS 1수준 한자 코드 배정, 글리프 렌더
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, '..', 'fonts', 'NanumSquareNeo-cBd.ttf')

# KS X 1001 완성형 2350자
SYL = []
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try:
            SYL.append(bytes([hi, lo]).decode('cp949'))
        except UnicodeDecodeError:
            pass
assert len(SYL) == 2350

BAD_TRAIL = {0x5B, 0x5C, 0x5D, 0x7C, 0x7F}
CODES = []
for lead in range(0x88, 0x99):
    for tr in range(0x40, 0xFD):
        if tr in BAD_TRAIL:
            continue
        c = (lead << 8) | tr
        if c < 0x889F or c > 0x9872:
            continue
        CODES.append(c)
assert len(CODES) >= 2350
ENC = {s: CODES[i] for i, s in enumerate(SYL)}
DEC = {v: k for k, v in ENC.items()}

# 원본 SJIS 로 그대로 둘 문장부호 (전각)
PUNCT = {}
for ch in '　、。，．・：？！ー～…（）「」－＝％＃＆＊＜＞０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺαβγⅡ':
    PUNCT[ch] = int.from_bytes(ch.encode('cp932'), 'big')

HALF2FULL = {chr(c): chr(c + 0xFEE0) for c in range(0x21, 0x7F)}
HALF2FULL[' '] = '　'
HALF2FULL['-'] = '－'
HALF2FULL['~'] = '～'
HALF2FULL['·'] = '・'


def is_hangul(ch):
    return ch in ENC


def encode_text(s):
    """한국어 텍스트(제어코드 포함) -> SJIS 바이트. $ 명령/ASCII 숫자·[] 는 그대로."""
    out = bytearray()
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in ENC:
            out += ENC[ch].to_bytes(2, 'big')
        elif ord(ch) < 0x80:
            out += ch.encode('ascii')
        else:
            try:
                out += ch.encode('cp932')
            except UnicodeEncodeError:
                raise ValueError('인코딩 불가 문자 %r in %r' % (ch, s[max(0, i - 10):i + 10]))
        i += 1
    return bytes(out)


_fcache = {}


def glyph(ch, size=14, cell=12, cellh=16, font=FONT):
    """12x12 4bpp 레벨(0..15) 글리프 배열"""
    key = (ch, size, cell, cellh, font)
    if key in _fcache:
        return _fcache[key]
    S = 4
    f = ImageFont.truetype(font, size * S)
    im = Image.new('L', (cell * S * 3, cellh * S * 3), 0)
    d = ImageDraw.Draw(im)
    d.text((cell * S, cellh * S), ch, font=f, fill=255)
    a = np.array(im)
    ys, xs = np.nonzero(a > 40)
    out = np.zeros((cellh, cell), np.uint8)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        w, h = x1 - x0, y1 - y0
        # 셀 중앙 정렬 (잉크 11px 기준)
        tw = (cell - 1) * S
        ox = x0 - (tw - w) // 2
        # 세로: 15px 박스 안에서 중앙 (마지막 줄은 비움)
        oy = y0 - ((cellh - 1) * S - h) // 2
        crop = im.crop((ox, oy, ox + cell * S, oy + cellh * S))
        small = np.array(crop.resize((cell, cellh), Image.BOX)).astype(np.float32) / 255
        lv = np.clip(np.round(small * 15 * 1.25), 0, 15).astype(np.uint8)
        lv[lv < 4] = 0
        out = lv
    _fcache[key] = out
    return out
