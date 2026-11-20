# 한글 패치 빌드: python tools/build.py <원본.bin> <출력.bin>
#  원본 bin 복사 -> TXTDATA(대본)+WINDATA(씬별 서브셋 폰트), BATMSG(전투 대사+폰트), EXE 고정테이블 충돌 제거
import sys, os, re, struct, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg, fonts, check, script
from disc import Writer

TOK = re.compile(r'(\$[A-Z]+\d*(?:\[\d+\])*)')
NSLOT = 336


def conv_body(b):
    """본문: $코드 보존, ASCII -> 전각"""
    out = []
    for part in TOK.split(b):
        if TOK.fullmatch(part):
            out.append(part)
        else:
            out.append(''.join(hg.HALF2FULL.get(c, c) for c in part))
    return ''.join(out)


def korean_text(name, ja):
    ko = check.load_ko(f'text/ko/{name}.txt')
    t = check.merge(ja, ko)
    lines = t.split('\r\n')
    for i, l in enumerate(lines):
        if l == '' or l.startswith('#') or l.startswith('$N'):
            continue
        m = script.CODE_TAIL.search(l)
        suf = m.group(1) if m else ''
        body = l[:len(l) - len(suf)]
        lines[i] = conv_body(body) + suf
    return '\r\n'.join(lines)


FIXED = set()


def hangul_set(text):
    seen = []
    s = set(FIXED)
    for l in text.split('\r\n'):
        if l.startswith('$N') or l.startswith('#'):
            continue
        for c in l:
            if hg.is_hangul(c) and c not in s:
                s.add(c); seen.append(c)
    return seen


def make_table(syl):
    assert len(syl) <= NSLOT, len(syl)
    tab = bytearray(NSLOT * 6)
    for k, ch in enumerate(syl):
        struct.pack_into('<HHH', tab, k * 6, hg.ENC[ch], k % 21, k // 21)
    return tab


def draw_font(buf, off, syl):
    pix, po = fonts.tim_pixels(buf, off)
    pix[:, :] = 0
    for k, ch in enumerate(syl):
        fonts.put(pix, k % 21, k // 21, ch)
    fonts.tim_store(buf, po, pix)


def make_table_rows(syl, row0):
    tab = bytearray(NSLOT * 6)
    for k, ch in enumerate(syl):
        struct.pack_into('<HHH', tab, k * 6, hg.ENC[ch], k % 21, row0 + k // 21)
    return tab


def draw_raw(buf, po, syl):
    import numpy as np
    pix = np.zeros((256, 256), np.uint8)
    assert len(syl) <= NSLOT
    for k, ch in enumerate(syl):
        fonts.put(pix, k % 21, k // 21, ch)
    fonts.tim_store(buf, po, pix)


def camp_blocks(kd, exsyl):
    import camp
    T = camp.table(kd)
    hdr = archive(kd)
    kd = bytearray(kd)
    out = []
    for k in range(8, 16):
        s, n = hdr[k]
        b = bytearray(kd[s * 2048:(s + n) * 2048])
        two = k not in (8, 15)
        st = 0x191c0 if two else 0x109e0
        e = b.find(b'\0', st)
        ja = bytes(b[st:e]).decode('cp932')
        lines_ko = camp.units_ko(ja, T)
        t = check.merge(ja, lines_ko)
        L = t.split('\r\n')
        for i, l in enumerate(L):
            if l == '' or l.startswith('#') or l.startswith('$N') or l.startswith(';'):
                continue
            m = script.CODE_TAIL.search(l)
            suf = m.group(1) if m else ''
            L[i] = conv_body(l[:len(l) - len(suf)]) + suf
        ko = '\r\n'.join(L)
        syl = hangul_set(ko)
        cap = 2 * NSLOT if two else NSLOT
        for c in exsyl:
            if len(syl) >= cap: break
            if c not in syl: syl.append(c)
        assert len(syl) <= cap, (k, len(syl))
        enc = hg.encode_text(ko) + b'\0'
        assert st + len(enc) <= len(b), (k, len(enc), len(b) - st)
        b[st:] = enc.ljust(len(b) - st, b'\0')
        if two:
            a, bb = syl[:NSLOT], syl[NSLOT:]
            draw_raw(b, 0x8000, a); draw_raw(b, 0x10000, bb)
            b[0x18200:0x189e0] = make_table_rows(a, 0)
            b[0x189e0:0x191c0] = make_table_rows(bb, 16)
        else:
            draw_raw(b, 0x8000, syl)
            b[0x10200:0x109e0] = make_table_rows(syl, 0)
        kd[s * 2048:(s + n) * 2048] = b
        out.append((f'camp{k-8}', len(syl), len(enc), len(b) - st))
    return bytes(kd), out


def split_text(raw):
    """블록 텍스트 영역 -> (본문 str, 꼬리 bytes)"""
    i = raw.find(b'\0')
    return raw[:i].decode('cp932'), b''


def archive(data):
    hdr = []
    i = 0
    while True:
        s, n = struct.unpack_from('<HH', data, i * 4)
        if s == 0 and n == 0: break
        hdr.append((s, n)); i += 1
    return hdr


def pack_archive(blocks, hdr_secs):
    out = bytearray(hdr_secs * 2048)
    s = hdr_secs
    for i, b in enumerate(blocks):
        n = (len(b) + 2047) // 2048
        struct.pack_into('<HH', out, i * 4, s, n)
        out += b.ljust(n * 2048, b'\0')
        s += n
    return bytes(out)


FREE = [(c, 9) for c in range(6, 21)] + [(c, 10) for c in range(6, 21)] + [(c, 12) for c in range(13, 21)] + [(6, 5), (7, 5), (2, 8), (8, 8)]
FTAB = 0x800997e0 - 0x80010000 + 0x800


def exe_strings(exe):
    """text/exe_ko.tsv: 오프셋(16진, 쉼표)<TAB>원문 바이트 수<TAB>번역. 원문은 원본 EXE에서 읽음"""
    out = []
    for l in open('text/exe_ko.tsv', encoding='utf-8'):
        offs, n, k = l.rstrip('\n').split('\t')
        offs = [int(x, 16) for x in offs.split(',')]; n = int(n)
        jj = bytes(exe[offs[0]:offs[0] + n]).decode('cp932')
        kk = ''.join(hg.HALF2FULL.get(c, c) for c in k.replace('/', '\n'))
        out.append((jj, kk, offs))
    return out


def choose_fixed(exe, ncell):
    import collections
    dia = collections.Counter()
    for f in os.listdir('text/ko'):
        for l in check.load_ko('text/ko/' + f):
            dia.update(c for c in l if hg.is_hangul(c))
    sc = collections.Counter()
    pri = {0, 228, 229, 230, 231, 232, 233, 180, 181, 272}
    for i, (_, k, _) in enumerate(exe):
        for c in set(k):
            if hg.is_hangul(c):
                sc[c] += 1000 if i in pri else 10
    allc = set(sc) | set(dia)
    order = sorted(allc, key=lambda c: (-sc[c], -dia[c], c))
    return order[:ncell]


def fixed_cells(exe_bytes):
    import collections
    cells = collections.OrderedDict()
    for k in range(294):
        c, x, y = struct.unpack_from('<HHH', exe_bytes, FTAB + k * 6)
        if c == 0: continue
        if (0x829F <= c <= 0x82F1) or (0x8340 <= c <= 0x8396) or c >= 0x889F:
            if (x, y) != (1, 8):
                cells.setdefault((x, y), []).append(k)
    return cells


def put_raw(buf, po, col, row, ch):
    g = hg.glyph(ch)
    for y in range(16):
        r = g[y]
        o = po + (row * 16 + y) * 128 + col * 6
        buf[o:o + 6] = bytes(int(r[2 * i]) | (int(r[2 * i + 1]) << 4) for i in range(6))


def patch_font1(buf, sig, assign):
    """buf 안의 모든 폰트1 사본에 고정 글리프 기록"""
    n = 0
    i = buf.find(sig)
    while i >= 0:
        po = i - 128 * 40
        for (x, y), ch in assign.items():
            put_raw(buf, po, x, y, ch)
        n += 1
        i = buf.find(sig, i + 1)
    return n


def patch_ops_copies(buf):
    """작전명 타이틀 이미지 사본(KODAIRA 0xd8000 과 동일) 한글화"""
    import labels
    oj = ORIG_KD[0xd8000:0xd8000 + 65536]
    i = buf.find(oj[:4096]); n = 0
    while i >= 0:
        if buf[i:i + 65536] == oj:
            tmp = bytearray(0xd8000) + buf[i:i + 65536]
            labels.patch_ops(tmp); buf[i:i + 65536] = tmp[0xd8000:]; n += 1
        i = buf.find(oj[:4096], i + 1)
    return n


ORIG_KD = None


def main(src, dst):
    global ORIG_KD
    shutil.copyfile(src, dst)
    w = Writer(dst)
    rd = lambda p: w.read(w.files[p][1], w.files[p][2])
    ORIG_KD = rd('/BIN/KODAIRA.DAT')

    # ---- 고정 폰트 배정
    exe = bytearray(rd('/FEDA2.EXE'))
    exs = exe_strings(exe)
    cells = fixed_cells(exe)
    allcells = list(cells) + FREE
    fx = choose_fixed(exs, len(allcells))
    FIXED.update(fx)
    assign = dict(zip(allcells, fx))
    # 고정 테이블 재작성
    for (x, y), ks in cells.items():
        for k in ks:
            struct.pack_into('<H', exe, FTAB + k * 6, 0)
    empt = [k for k in range(294) if struct.unpack_from('<H', exe, FTAB + k * 6)[0] == 0]
    for (x, y), ch in assign.items():
        k = empt.pop(0)
        struct.pack_into('<HHH', exe, FTAB + k * 6, hg.ENC[ch], x, y)
    cs = set(hg.CODES[:len(hg.SYL)])
    for k in range(294):
        c = struct.unpack_from('<H', exe, FTAB + k * 6)[0]
        if c in cs and hg.DEC[c] not in FIXED:
            struct.pack_into('<H', exe, FTAB + k * 6, 0)
    # 코드 오름차순 정렬(캠프 쪽 탐색이 정렬을 가정)
    ents = [struct.unpack_from('<HHH', exe, FTAB + k * 6) for k in range(294)]
    ents = sorted(e for e in ents if e[0]) + [e for e in ents if not e[0]]
    for k, e in enumerate(ents):
        struct.pack_into('<HHH', exe, FTAB + k * 6, *e)
    # EXE 문자열 제자리 교체
    exsyl = []
    for jj, kk, offs in exs:
        jb = jj.encode('cp932'); kb = hg.encode_text(kk)
        for o in offs:
            mx = (((o + len(jb) + 1) + 3) & ~3) - o - 1
            assert len(kb) <= mx, (kk, len(kb), mx)
            assert exe[o:o + len(jb)] == jb, jj
            exe[o:o + len(jb)] = b'\0' * len(jb)
            exe[o:o + len(kb)] = kb
        for c in kk:
            if hg.is_hangul(c) and c not in FIXED and c not in exsyl:
                exsyl.append(c)
    print('fixed', len(fx), 'exe-subset', len(exsyl))
    import equip
    nm = [k for jj, k, o in exs if 0x3900 <= o[0] <= 0x39f4] + ['바이퍼'] + [k for jj, k, o in exs if 0x38a0 <= o[0] <= 0x3b70]
    small = equip.small_set([k.split('・')[0] for k in nm])
    equip.patch_small_table(exe, small)
    print('small', len(small))
    w.replace('/FEDA2.EXE', bytes(exe), allow_move=False)
    # 폰트1 사본 서명
    win0 = rd('/TIM/WINDATA.TIM')
    s0, n0 = struct.unpack_from('<HH', win0, 0)
    e0 = win0[s0 * 2048:(s0 + n0) * 2048]
    ln = struct.unpack_from('<I', e0, 66080 + 8)[0]
    po0 = 66080 + 8 + ln + 12
    sig = bytes(e0[po0 + 128 * 40:po0 + 128 * 40 + 64])
    for path in ('/TIM/BTLMAP.TIM', '/TIM/SAYSUN.TIM', '/BIN/KODAIRA.DAT'):
        b = bytearray(rd(path))
        print(path, patch_font1(b, sig, assign), equip.patch_small_font(b, sig, small))
        if path == '/BIN/KODAIRA.DAT':
            b, cst = camp_blocks(bytes(b), exsyl)
            for x in cst: print(*x)
            import labels
            b = bytearray(b); print('equip', equip.patch_block(b, archive(b), exsyl, {jj.strip('　'): kk for jj, kk, _ in reversed(exs)}, FIXED)); labels.patch(b); labels.patch_ops(b); import tim as _t0; labels.patch_equip(b, _t0.scan(bytes(rd('/TIM/SAYSUN.TIM')))[2]['clut']['data']); import title; title.patch(b)
        w.replace(path, bytes(b), allow_move=False)

    # ---- TIMDATA 나레이션 이미지
    import narr
    td = bytearray(rd('/TIM/TIMDATA.TIM')); narr.patch(td)
    w.replace('/TIM/TIMDATA.TIM', bytes(td), allow_move=False)

    # ---- BATSYS
    bsy = bytearray(rd('/BATSYS.MSG'))
    draw_font(bsy, 0, exsyl)
    bsy[0x8220:0x8a00] = make_table(exsyl)
    w.replace('/BATSYS.MSG', bytes(bsy), allow_move=False)

    # ---- TXTDATA + WINDATA
    txt = rd('/TXTDATA.TXT')
    win = bytearray(rd('/TIM/WINDATA.TIM'))
    print('WINDATA font1', patch_font1(win, sig, assign), equip.patch_small_font(win, sig, small))
    print('WINDATA ops', patch_ops_copies(win))
    sy = bytearray(rd('/TIM/SAYSUN.TIM')); print('SAYSUN ops', patch_ops_copies(sy))
    import tim as _tim, numpy as _np, labels as _lb
    _t = _tim.scan(bytes(sy))[2]; _o = _t['off']
    _a = _np.frombuffer(bytes(sy[_o:_o + 65536]), _np.uint8).reshape(256, 256).copy()
    _lb.patch_heisou(_a, _t['clut']['data'][0]); sy[_o:_o + 65536] = _a.tobytes()
    w.replace('/TIM/SAYSUN.TIM', bytes(sy), allow_move=False)
    camp = [c for jj, kk, _ in exs[341:357] for c in kk]
    th = archive(txt); wh = archive(win)
    blocks = []
    stat = []
    for i, (s, n) in enumerate(th):
        blk = txt[s * 2048:(s + n) * 2048]
        name = f'txt{i:02d}'
        if name == 'txt19':
            syl = list(exsyl)
            ko = ''.join(syl) + '\r\n\x1a'
        else:
            raw = blk[0x7e0:]
            j = raw.find(b'\0')
            ja = raw[:j].decode('cp932')
            ko = korean_text(name, ja)
            syl = hangul_set(ko)
            if name == 'txt72':
                syl += [c for c in dict.fromkeys(camp) if hg.is_hangul(c) and c not in FIXED and c not in syl]
        nb = bytes(make_table(syl)) + hg.encode_text(ko) + b'\0'
        assert len(nb) <= 4 * 2048, (name, len(nb))
        blocks.append(nb)
        ws, wn = wh[i]
        ent = bytearray(win[ws * 2048:(ws + wn) * 2048])
        draw_font(ent, 99392, syl)
        win[ws * 2048:(ws + wn) * 2048] = ent
        stat.append((name, len(syl), len(nb)))
    hs = th[0][0]
    w.replace('/TXTDATA.TXT', pack_archive(blocks, hs))
    w.replace('/TIM/WINDATA.TIM', bytes(win), allow_move=False)

    # ---- BATMSG
    bm = rd('/BATMSG.MSG')
    bh = archive(bm)
    bblocks = []
    for i, (s, n) in enumerate(bh):
        blk = bytearray(bm[s * 2048:(s + n) * 2048])
        name = f'bat{i:02d}'
        raw = blk[0x8a00:]
        j = raw.find(b'\0')
        ja = raw[:j].decode('cp932')
        ko = korean_text(name, ja)
        syl = hangul_set(ko)
        head = bytearray(blk[:0x8a00])
        draw_font(head, 0, syl)
        head[0x8220:0x8a00] = make_table(syl)
        nb = bytes(head) + hg.encode_text(ko) + b'\0'
        bblocks.append(nb)
        stat.append((name, len(syl), len(nb)))
    w.replace('/BATMSG.MSG', pack_archive(bblocks, bh[0][0]))

    for s in stat:
        print(*s)
    w.f.close()


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
