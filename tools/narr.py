# TIMDATA 나레이션 이미지 한글화 (text/ko/narr.txt)
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tim
from narrband import bands, lum

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, '..', 'fonts', 'NanumSquareNeo-cBd.ttf')
SRC = os.path.join(HERE, '..', 'text', 'ko', 'narr.txt')


def load():
    spec = {}
    cur = None
    for l in open(SRC, encoding='utf-8'):
        l = l.rstrip('\n')
        if l.startswith(';'):
            continue
        m = re.match(r'#(\d+) ([csC])$', l)
        if m:
            cur = int(m.group(1)); spec[cur] = (m.group(2), [], [])
            continue
        if cur is None:
            continue
        if l.startswith('@'):
            box, t = l[1:].split('|', 1)
            spec[cur][2].append((tuple(map(int, box.split(','))), t))
        else:
            spec[cur][1].append(l)
    return spec


GAL = [(os.path.join(HERE, '..', 'fonts', 'Galmuri%d.ttf' % n), z) for n, z in ((14, 15), (11, 12), (9, 10))]


LO = 0


def fit(t, w, h):
    for k, (fp, z) in enumerate(GAL):
        bb = ImageFont.truetype(fp, z).getbbox(t)
        if bb[2] - bb[0] <= w - 2 and z - 1 <= h:
            return k
    return len(GAL) - 1


def text_img(t, w, h, size_max=None):
    # 갈무리 원본 크기(확대·축소 없음) 중 들어맞는 가장 큰 것 (LO: 이미지 내 통일 하한)
    for fp, z in GAL[LO:]:
        f = ImageFont.truetype(fp, z)
        bb = f.getbbox(t)
        if bb[2] - bb[0] <= w - 2 and z - 1 <= h:
            break
    tw = bb[2] - bb[0] + 2
    im = Image.new('L', (tw, h), 0)
    dr = ImageDraw.Draw(im); dr.fontmode = '1'
    dr.text((1 - bb[0], (h - (z - 1)) // 2 - 1), t, font=f, fill=255)
    return np.array(im)


class Pal:
    def __init__(s, t, pix):
        c = t['clut']['data'][0].astype(int)
        r = (c & 31) * 8; g = ((c >> 5) & 31) * 8; b = ((c >> 10) & 31) * 8
        s.lum = (r * 3 + g * 6 + b) / 10
        s.bg = int(np.bincount(pix.ravel(), minlength=256).argmax())
        used = np.unique(pix)
        s.lut = np.array([used[np.argmin(np.abs(s.lum[used] - v))] for v in range(256)], np.uint8)
        s.lut[0] = s.bg
        cand = [int(i) for i in used if i != s.bg]
        s.white = max(cand, key=lambda i: s.lum[i]) if cand else 255

    def put(s, reg, g):
        g = g[:reg.shape[0], :reg.shape[1]]
        reg = reg[:g.shape[0], :g.shape[1]]
        reg[g > 85] = s.white


def patch_one(d, t, mode, lines, boxes):
    w, h = t['w'] * 2, t['h']
    o = t['off']
    pix = np.frombuffer(bytes(d[o:o + w * h]), np.uint8).reshape(h, w).copy()
    P = Pal(t, pix)
    orig = pix.copy()
    L = lum(t)
    global LO
    LO = 0
    if mode in 'cC':
        bs = bands(L)
        assert len(bs) == len(lines), (t['start'], len(bs), len(lines))
        LO = max([fit(ln, w - 20, b[1] - b[0]) for b, ln in zip(bs, lines) if ln not in ('=', '-', '')] or [0])
        for (y0, y1, x0, x1), ln in zip(bs, lines):
            if ln == '=':
                continue
            pix[max(0, y0 - 1):y1 + 1, max(0, x0 - 3):x1 + 3] = P.bg
            if ln == '-' or ln == '':
                continue
            hh = y1 - y0
            center = mode == 'C' or (abs((x0 + x1) / 2 - w / 2) < 16 and x0 > 8)
            if center:
                g = text_img(ln, w - 20, hh, min(14, hh))
                X = (w - g.shape[1]) // 2
            else:
                g = text_img(ln, w - x0 - 2, hh, min(14, hh))
                X = x0
            P.put(pix[y0:y0 + hh, X:X + g.shape[1]], g[:, :min(g.shape[1], w - X)])
    else:
        bs = bands(L)
        y = bs[0][0] if bs else 4
        x = min(b[2] for b in bs) if bs else 4
        pix[:, :] = P.bg
        LO = max([fit(ln, w - x - 2, 15) for ln in lines if ln] or [0])
        for ln in lines:
            if ln:
                g = text_img(ln, w - x - 2, 15, 13)
                P.put(pix[y:y + 15, x:x + g.shape[1]], g[:, :min(g.shape[1], w - x)])
            y += 16
        assert y <= h + 1, ('overflow', t['start'], y)
    LO = 0
    # 상자 글씨색: 원본 상자들 안 글씨에 가장 많이 쓰인 색(날짜를 다른 팔레트로 보여 주는 화면 대비)
    r = np.concatenate([orig[y0:y1, x0:x1].ravel() for (x0, y0, x1, y1), _ in boxes] or [np.zeros(0, np.uint8)])
    r = r[r != P.bg]
    white = int(np.bincount(r).argmax()) if r.size else P.white
    for (x0, y0, x1, y1), ln in boxes:
        pix[y0:y1, x0:x1] = P.bg
        left = ln.startswith('<')
        ln = ln.lstrip('<')
        g = text_img(ln, x1 - x0, y1 - y0, min(15, y1 - y0))
        X = x0 if left else x0 + (x1 - x0 - g.shape[1]) // 2
        reg = pix[y0:y1, X:X + g.shape[1]]; gg = g[:reg.shape[0], :reg.shape[1]]
        reg[gg > 85] = white
    d[o:o + w * h] = pix.tobytes()


def patch(d):
    ts = tim.scan(bytes(d))
    for k, (mode, lines, boxes) in load().items():
        patch_one(d, ts[k], mode, lines, boxes)
    patch_credits(d, ts)


# ---- 엔딩 크레딧(887~899: 각 페이지 8~247행이 이어지는 스크롤)
CREDITS = '''이그제큐티브 프로듀서|야노 세이이치|아베 다케히사|프로듀서|나카가와 요시히토|구보 야스유키|디렉션|오리모 겐지|게임 디자인 팀|다마키 요시타카|와키노 요시아키|스즈키 다카히로|우에노 미즈에|스즈키 고|프로그램 팀|시게타 기요미|아나미즈 유지|후지이 쇼지|고다이라 히데유키|마쓰모토 나오유키|다카노 히데오|구마가이 야스히로|미스터 X|그래픽 팀|나카자와 미유키|야마모토 가쓰미|야스다 레이가|구마노 미쓰오|가도노 데쓰야|히노 기요후미|사사키 히로유키|지바 히로미|매트릭스 CG 팀|다마키 히사요시|히로이 데쓰오|우에무라 야스히로|사운드 팀|에노모토 히데히코|다마야마 후미토|드라마 팀|시오자와 가네토|미도리카와 히카루|하기모리 준코|고야마 마미|아오노 다케시|긴가 반조|가네다 사오리|에가와 히사오|데라세 메구미|야마자키 와카나|소가베 가즈유키|고리 다이스케|구와시마 호코|노지마 겐지|시마다 빈|가미야 히로시|아오니 프로덕션|후루이치 도시오|단게 사쿠라|택트 스튜디오'''.split('|')
CR_FONT = os.path.join(HERE, '..', 'fonts', 'NanumSquareNeo-cBd.ttf')


def patch_credits(d, ts):
    ks = list(range(887, 900))
    pages = [np.frombuffer(bytes(d[ts[k]['off']:ts[k]['off'] + 65536]), np.uint8).reshape(256, 256).copy() for k in ks]
    A = np.vstack([p[8:248] for p in pages])
    t = ts[887]
    P = Pal(t, pages[0])
    P.bg = 0
    Lm = P.lum[A].copy(); Lm[A == 31] = 0; Lm[:, :10] = 0; Lm[:, 246:] = 0
    bs = [b for b in bands(Lm) if b[1] - b[0] >= 13]
    assert len(bs) == len(CREDITS), len(bs)
    global FONT
    f0 = FONT; FONT = CR_FONT
    for (y0, y1, x0, x1), name in zip(bs, CREDITS):
        h = min(16, y1 - y0)
        sub = Lm[y0:y0 + h] > 60
        xs = np.nonzero(sub.any(0))[0]
        a0, a1 = int(xs.min()), int(xs.max()) + 1
        reg = A[y0:y0 + h, max(10, a0 - 2):min(246, a1 + 2)]
        reg[reg != 31] = 0
        g = text_img(name, 236, h, 14)
        X = (256 - g.shape[1]) // 2
        P.put(A[y0:y0 + h, X:X + g.shape[1]], g)
    FONT = f0
    for i, k in enumerate(ks):
        pages[i][8:248] = A[i * 240:(i + 1) * 240]
        d[ts[k]['off']:ts[k]['off'] + 65536] = pages[i].tobytes()


if __name__ == '__main__':
    d = bytearray(open(sys.argv[1], 'rb').read())
    patch(d)
    ts = tim.scan(bytes(d))
    ks = list(load().keys())
    for p in range(0, len(ks), 8):
        c = Image.new('RGB', (256 * 4, 256 * 2))
        for i, k in enumerate(ks[p:p + 8]):
            c.paste(tim.render(ts[k], 0).convert('RGB'), (256 * (i % 4), 256 * (i // 4)))
        c.save(sys.argv[2] + '_%d.png' % (p // 8))

