# 나레이션 TIM 글줄 영역 검출
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, tim
from scipy import ndimage


def lum(t):
    return np.array(tim.render(t, 0).convert('L')).astype(int)


def bands(L, thr=60):
    m = L > thr
    m2 = ndimage.binary_closing(m, structure=np.ones((1, 9)))
    rows = m2.any(1)
    out = []
    y = 0
    while y < len(rows):
        if rows[y]:
            y0 = y
            while y < len(rows) and rows[y]: y += 1
            xs = np.nonzero(m[y0:y].any(0))[0]
            out.append((y0, y, int(xs.min()), int(xs.max()) + 1))
        else:
            y += 1
    return out


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read(); ts = tim.scan(d)
    for k in map(int, sys.argv[2:]):
        print(k, bands(lum(ts[k])))
