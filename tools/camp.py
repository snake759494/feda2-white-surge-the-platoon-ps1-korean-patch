# 캠프 대사(KODAIRA 블록 8~15): 원본 디스크에서 원문을 읽어 고유 문장 순서로 정리
# text/ko/camp.txt 의 각 줄은 그 순서(첫 등장 순)에 대응. '=' 은 원문 그대로 둠(화면에 나오지 않는 주석)
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import script


def blocks(kd):
    """KODAIRA.DAT -> [(블록번호, 시작오프셋, 원문 str)]"""
    out = []
    i = 0
    hdr = []
    while True:
        s, n = struct.unpack_from('<HH', kd, i * 4)
        if s == 0 and n == 0: break
        hdr.append((s, n)); i += 1
    for k in range(8, 16):
        s, n = hdr[k]
        b = kd[s * 2048:(s + n) * 2048]
        st = 0x109e0 if k in (8, 15) else 0x191c0
        e = b.find(b'\0', st)
        out.append((k, st, bytes(b[st:e]).decode('cp932')))
    return out


def src_lines(kd):
    """@화자 줄 + 고유 문장 (예전 text/src/camp.txt 와 같은 순서)"""
    seen = set(); out = []
    for k, st, t in blocks(kd):
        spk = '?'; cur = None
        for i, kind, pre, body, suf in script.units(t):
            if kind == 'name': spk = body.strip('　 ') or '-'; continue
            if body in seen: continue
            seen.add(body)
            if cur != spk: out.append('@' + spk); cur = spk
            out.append(body)
    return out


def table(kd):
    src = src_lines(kd)
    ko = [l.rstrip('\n') for l in open('text/ko/camp.txt', encoding='utf-8')]
    assert len(src) == len(ko), (len(src), len(ko))
    return {s: (s if k == '=' else k) for s, k in zip(src, ko) if not s.startswith('@')}


def units_ko(ja, T):
    return [T[u[3]] for u in script.units(ja) if u[1] == 'text']
