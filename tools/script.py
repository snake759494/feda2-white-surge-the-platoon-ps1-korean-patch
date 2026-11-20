# 대본 파일(TXTDATA/BATMSG 블록 본문) <-> 번역 단위
# 번역 단위: '#','$P','$B' 등 제어줄이 아닌 텍스트 줄의 본문(끝의 $코드 제외), $N 줄의 이름
import re

CODE_TAIL = re.compile(r'((?:\$[A-Z]+\d*(?:\[\d+\])*)+[　 ]*)$')
NAME = re.compile(r'^(\$N\d+(?:\[\d+\])*)\s*(.*)$')


def units(text):
    """-> list of (line_index, kind, prefix, body, suffix)"""
    out = []
    for i, l in enumerate(text.split('\r\n')):
        if l.startswith('#') or l.strip('') == '':
            continue
        m = NAME.match(l)
        if m:
            sp = l[len(m.group(1)):len(l) - len(m.group(2))]
            out.append((i, 'name', m.group(1) + sp, m.group(2), ''))
            continue
        if l.startswith('$'):
            # 순수 제어줄 ($P, $B, $END1, $IF1[007] ...)
            if CODE_TAIL.sub('', l.strip('　 ')) == '':
                continue
        m = CODE_TAIL.search(l)
        suf = m.group(1) if m else ''
        body = l[:len(l) - len(suf)]
        if body.strip('　 ') == '':
            continue
        out.append((i, 'text', '', body, suf))
    return out


def apply(text, trans):
    """trans: list of bodies in units() order"""
    lines = text.split('\r\n')
    us = units(text)
    assert len(us) == len(trans), (len(us), len(trans))
    for (i, k, pre, body, suf), t in zip(us, trans):
        lines[i] = pre + t + suf
    return '\r\n'.join(lines)
