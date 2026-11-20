# 캠프 위치/인물 라벨 이미지(KODAIRA 0x75800, 8bpp 256x416) 한글화
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, '..', 'fonts', 'NanumSquareNeo-eHv.ttf')
OFF = 0x75800
W, H = 256, 416
COLS = [(4, 86), (86, 168), (168, 252)]
# (밴드 y0, y1) -> 열별 라벨
BANDS = [
    ((47, 73), [None, None, '에이미']),
    ((87, 113), ['로웰', '레이스', '알렉스']),
    ((127, 153), ['모리스', 'M2', '질']),
    ((166, 193), ['나가기', '타이탄II', 'HQ']),
    ((206, 233), ['병원', '모닥불', '막사']),
    ((262, 289), ['브루스', '나가기', '셸퍼']),
    ((302, 329), ['미네르바', '마샤', '디바이스']),
    ((342, 369), ['신시아', '니콜라이', '아인']),
    ((382, 409), ['토비카게', '브라이언', '코발리']),
]


def render(text, maxw):
    S = 4
    for size in (17, 16, 15, 14, 13, 12):
        f = ImageFont.truetype(FONT, size * S)
        bb = f.getbbox(text)
        w = (bb[2] - bb[0]) // S + 4
        if w <= maxw:
            break
    im = Image.new('L', ((bb[2] - bb[0]) + 8 * S, size * S + 8 * S), 0)
    ImageDraw.Draw(im).text((4 * S - bb[0], 4 * S - bb[1]), text, font=f, fill=255)
    # 기울임
    sh = 0.2
    im = im.transform(im.size, Image.AFFINE, (1, sh, -sh * im.size[1] / 2, 0, 1, 0), Image.BICUBIC)
    im = im.resize((im.size[0] // S, im.size[1] // S), Image.LANCZOS)
    m = np.array(im) > 100
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def draw_label(a, y0, y1, x0, x1, text):
    reg = a[y0:y1, x0:x1]
    txt = (reg >= 0x20) & (reg < 0x30)
    if txt.any():
        ys, xs = np.nonzero(txt)
        cy = (ys.min() + ys.max()) / 2
        cx = (xs.min() + xs.max()) / 2
    else:
        cy, cx = (y1 - y0) / 2, (x1 - x0) / 2
    reg[txt] = 0
    if not text:
        return
    LM = 10  # 왼쪽 괄호 장식에 가리지 않도록
    RM = 14  # 오른쪽 고리 장식
    m = render(text, x1 - x0 - LM - RM)
    h, w = m.shape
    oy = int(round(cy - h / 2)); ox = int(round(cx - w / 2))
    ox = max(LM, min(ox, (x1 - x0) - w - RM))
    big = np.zeros((h + 4, w + 4), bool)
    big[2:2 + h, 2:2 + w] = m
    out = ndimage.binary_dilation(big, iterations=1)
    out2 = ndimage.binary_dilation(out, iterations=1)
    # 채움: 위쪽 어둡게 -> 아래 밝게
    fill = np.zeros(big.shape, np.uint8)
    for yy in range(big.shape[0]):
        t = (yy - 2) / max(1, h - 1)
        fill[yy] = 0x26 + int(round(t * 4))
    fill = np.clip(fill, 0x26, 0x2a)
    # 하이라이트 그림자: 글자 위 가장자리 0x24
    top = big & ~np.roll(big, 1, 0)
    col = np.zeros(big.shape, np.uint8)
    col[out2] = 0x21
    col[out & ~big] = 0x22
    col[big] = fill[big]
    pass
    Y0 = oy - 2; X0 = ox - 2
    for yy in range(big.shape[0]):
        for xx in range(big.shape[1]):
            if col[yy, xx]:
                Y, X = Y0 + yy, X0 + xx
                if 0 <= Y < reg.shape[0] and 0 <= X < reg.shape[1] and reg[Y, X] != 0xfe:
                    reg[Y, X] = col[yy, xx]


def patch(kd):
    a = np.frombuffer(bytes(kd[OFF:OFF + W * H]), np.uint8).reshape(H, W).copy()
    for (y0, y1), names in BANDS:
        for (x0, x1), t in zip(COLS, names):
            if t is None and not ((a[y0:y1, x0:x1] >= 0x20) & (a[y0:y1, x0:x1] < 0x30)).any():
                continue
            if t is None:
                continue
            draw_label(a, y0, y1, x0, x1, t)
    kd[OFF:OFF + W * H] = a.tobytes()
    return a


if __name__ == '__main__':
    import sys
    kd = bytearray(open(sys.argv[1], 'rb').read())
    a = patch(kd)
    Image.fromarray(np.where(a == 0xfe, 40, np.where(a > 0x20, (a - 0x20) * 24, 0)).astype(np.uint8)).resize((768, 1248), 0).save(sys.argv[2])


# ---- 작전명 타이틀(KODAIRA 0xd8000, 8bpp 256폭)
OFF2 = 0xd8000
OPS = [
    ((6, 30), (2, 165), '야버드 작전'),
    ((30, 54), (2, 165), '빌간테스 전격 작전'),
    ((54, 78), (2, 165), '데스 리절트 작전'),
    ((78, 102), (2, 165), '사마니스크 작전'),
    ((102, 126), (2, 165), '클리포드 포박 작전'),
    ((126, 150), (2, 165), '의용군 지원 작전'),
    ((150, 174), (2, 165), '더블 레인보 작전'),
    ((174, 198), (2, 165), '나르디노 작전'),
    ((198, 222), (2, 165), '게디스 프로텍트 작전'),
    ((222, 246), (2, 165), '카타로프 섬멸 작전'),
    ((6, 30), (165, 254), '어드밴스'),
    ((30, 54), (165, 254), '자하 작전'),
    ((54, 78), (165, 254), '다이달로스'),
    ((78, 102), (165, 226), "파괴작전"),
]


def render2(text, maxw, maxh=18):
    S = 4
    for size in range(20, 9, -1):
        f = ImageFont.truetype(FONT, size * S)
        bb = f.getbbox(text)
        w = (bb[2] - bb[0]) // S + int(0.25 * size) + 4
        if w <= maxw:
            break
    im = Image.new('L', ((bb[2] - bb[0]) + 16 * S, size * S + 8 * S), 0)
    ImageDraw.Draw(im).text((8 * S - bb[0], 4 * S - bb[1]), text, font=f, fill=255)
    sh = 0.25
    im = im.transform(im.size, Image.AFFINE, (1, sh, -sh * im.size[1] / 2, 0, 1, 0), Image.BICUBIC)
    im = im.resize((im.size[0] // S, im.size[1] // S), Image.LANCZOS)
    m = np.array(im) > 110
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def patch_ops(kd):
    a = np.frombuffer(bytes(kd[OFF2:OFF2 + 256 * 256]), np.uint8).reshape(256, 256).copy()
    for (y0, y1), (x0, x1), t in OPS:
        reg = a[y0:y1, x0:x1]
        reg[(reg != 0) & (reg != 0xfe)] = 0
        m = render2(t, x1 - x0 - 10)
        h, w = m.shape
        big = np.zeros((h + 4, w + 4), bool); big[2:2 + h, 2:2 + w] = m
        o1 = ndimage.binary_dilation(big)
        o2 = ndimage.binary_dilation(o1)
        col = np.zeros(big.shape, np.uint8)
        col[o2] = 0xec; col[o1 & ~big] = 0xe9; col[big] = 0xe1
        oy = (y1 - y0 - big.shape[0]) // 2
        ox = 6
        for yy in range(big.shape[0]):
            for xx in range(big.shape[1]):
                Y, X = oy + yy, ox + xx
                if col[yy, xx] and 0 <= Y < reg.shape[0] and 0 <= X < reg.shape[1] and reg[Y, X] != 0xfe:
                    reg[Y, X] = col[yy, xx]
    kd[OFF2:OFF2 + 256 * 256] = a.tobytes()
    return a


# ---- 상태창 '兵装' 음각 라벨(SAYSUN.TIM 2번째 8bpp TIM, 256폭) -> '무장'
def patch_heisou(pix, clut):
    """pix: 256x256 uint8 배열(제자리 수정)"""
    c = clut.astype(int)
    L = ((c & 31) * 3 + ((c >> 5) & 31) * 6 + ((c >> 10) & 31)) * 8 // 10
    y0, y1, x0, x1 = 228, 244, 91, 126
    reg = pix[y0 - 2:y1 + 2, x0 - 2:x1 + 2]
    used = np.unique(reg)
    dark = int(used[np.argmin(np.abs(L[used] - 75))]); light = int(used[np.argmax(L[used])])
    for y in range(y0, y1):
        pix[y, x0:x1] = pix[245, x0:x1]
    S = 4
    f = ImageFont.truetype(os.path.join(HERE, '..', 'fonts', 'NanumSquareNeo-eHv.ttf'), 14 * S)
    t = '무장'
    bb = f.getbbox(t)
    w, h = x1 - x0 - 2, y1 - y0 - 1
    im = Image.new('L', (w * S, h * S), 0)
    ImageDraw.Draw(im).text(((w * S - (bb[2] - bb[0])) // 2 - bb[0], (h * S - (bb[3] - bb[1])) // 2 - bb[1]), t, font=f, fill=255)
    m = np.array(im.resize((w, h), Image.LANCZOS)) > 110
    for yy in range(h):
        for xx in range(w):
            if m[yy, xx]:
                if yy + 1 < h and xx + 1 < w and not m[yy + 1, xx + 1]:
                    pix[y0 + yy + 1, x0 + xx + 1] = light
                pix[y0 + yy, x0 + xx] = dark
    return pix
