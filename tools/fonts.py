# 폰트 TIM(4bpp 256x256, 12px 셀 21열) 조작
import struct
import numpy as np
from hg import glyph

COLS = 21


def tim_pixels(buf, off):
    """off = TIM 시작. 4bpp 256x256 픽셀 배열(np) 과 픽셀 데이터 오프셋 반환"""
    tag, fl = struct.unpack_from('<II', buf, off)
    assert tag == 0x10 and fl == 8
    p = off + 8
    ln = struct.unpack_from('<I', buf, p)[0]
    p += ln
    ln, x, y, w, h = struct.unpack_from('<IHHHH', buf, p)
    po = p + 12
    raw = np.frombuffer(bytes(buf[po:po + w * h * 2]), np.uint8)
    a = np.empty(raw.size * 2, np.uint8)
    a[0::2] = raw & 15
    a[1::2] = raw >> 4
    return a.reshape(h, w * 4).copy(), po


def tim_store(buf, po, pix):
    p = pix.reshape(-1)
    raw = (p[0::2] & 15) | ((p[1::2] & 15) << 4)
    buf[po:po + raw.size] = raw.astype(np.uint8).tobytes()


def put(pix, col, row, ch):
    g = glyph(ch)
    pix[row * 16:row * 16 + 16, col * 12:col * 12 + 12] = g


def clear(pix, col, row):
    pix[row * 16:row * 16 + 16, col * 12:col * 12 + 12] = 0
