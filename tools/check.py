# 번역 파일 검사: 단위 수 일치, 줄 폭(20), 페이지 줄 수(3)
import sys, os, glob, re
sys.path.insert(0, os.path.dirname(__file__))
import script
W = 20


def load_ko(path):
    return [l.rstrip('\n') for l in open(path, encoding='utf-8') if not l.startswith('@')]


def width(s):
    return len(s)


def merge(ja_text, ko_units):
    """ja 텍스트 + ko 텍스트단위 -> 새 텍스트. '/' 는 줄나눔, 같은 페이지 빈줄 흡수"""
    lines = ja_text.split('\r\n')
    us = [u for u in script.units(ja_text) if u[1] == 'text']
    assert len(us) == len(ko_units), ('count', len(us), len(ko_units))
    rep = {}
    for (i, k, pre, body, suf), t in zip(us, ko_units):
        if t == '=':  # 화면에 나오지 않는 주석: 원문 유지
            t = body
        parts = t.split('/')
        rep[i] = [p for p in parts[:-1]] + [parts[-1] + suf]
    out = []
    for i, l in enumerate(lines):
        if i in rep:
            out.extend(rep[i])
        else:
            out.append(l)
    # 페이지 단위로 빈 줄 흡수
    res = []
    page = []

    def flush():
        n = len(page)
        p = list(page)
        while n > 3:
            # 뒤쪽 빈 줄부터 제거
            for j in range(len(p) - 1, -1, -1):
                if p[j] == '':
                    del p[j]
                    n -= 1
                    break
            else:
                break
        res.extend(p)
        page.clear()

    for l in out:
        ctrl = l == '' or l.startswith('#') or l.startswith('$N') or (l.startswith('$') and script.CODE_TAIL.sub('', l.strip('　 ')) == '')
        if ctrl:
            flush()
            res.append(l)
            continue
        page.append(l)
        if re.search(r'\$(P|B)', l):
            flush()
    flush()
    return '\r\n'.join(res)


def pages(text):
    out = []
    page = []
    for l in text.split('\r\n'):
        ctrl = l == '' or l.startswith('#') or l.startswith('$N') or (l.startswith('$') and script.CODE_TAIL.sub('', l.strip('　 ')) == '')
        if ctrl:
            if page: out.append(page)
            page = []
            continue
        page.append(script.CODE_TAIL.sub('', l))
        if re.search(r'\$(P|B)', l):
            out.append(page)
            page = []
    if page: out.append(page)
    return out


def check(name):
    ja = open(f'text/ja/{name}.txt', encoding='utf-8', newline='').read()
    ko = load_ko(f'text/ko/{name}.txt')
    errs = []
    try:
        t = merge(ja, ko)
    except AssertionError as e:
        return [f'{name}: 단위 수 불일치 {e}']
    for pg in pages(t):
        if len(pg) > 3:
            errs.append(f'{name}: 페이지 {len(pg)}줄 {pg}')
        for l in pg:
            if width(l) > W and not l.startswith('<<'):
                errs.append(f'{name}: 폭 {width(l)} 「{l}」')
    return errs


if __name__ == '__main__':
    names = sys.argv[1:] or [os.path.basename(f)[:-4] for f in sorted(glob.glob('text/ko/*.txt'))]
    for n in names:
        for e in check(n):
            print(e)
