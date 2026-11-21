# 부대관리(장비 확인) 화면: KODAIRA 블록 22 의 병종명·설명 번역 + 자체 한자 폰트/테이블 교체
#  블록 22: 폰트 4bpp 256폭 3페이지(0x14000~, 12x16 셀 21열), 테이블 0x37510 (코드,x,y)*0x3f0
#  화면의 작은 이름(8x8 반각 폰트)은 EXE 변환표 0x80099ec4(128칸)와 폰트1 사본 하단(y=216~)을 한글로 교체
import struct, os
import numpy as np
import hg, fonts

BLK = 22
FONT_OFF = 0x14000
TAB_OFF = 0x37510
NMAX = 38 * 21          # 원본이 쓰던 행(0~37)까지만 사용: 그 뒤는 다른 데이터

CLASS = {  # 블록 오프셋: 번역 (원문은 디스크에서 확인)
    0x2d210: '기동백병전', 0x2d21c: '중장요격병', 0x2d228: 'ＭＥＳ연술', 0x2d234: '기동비행병',
    0x2d240: '염옥마장병', 0x2d24c: '수린마장병', 0x2d258: '열풍마장병', 0x2d264: '명토마장병',
    0x2d270: '초수기승병', 0x2d27c: '기동친위병', 0x2d288: '육탄백병전', 0x2d294: '특수암살병',
    0x2d2a0: '육탄ＭＥＳ', 0x2d2ac: '후방공격병', 0x2d2b8: '초중병기병', 0x2d2c4: '거점방위병',
    0x2d2d0: '중장돌격병', 0x2d2dc: '용족근위병', 0x2d2e8: '후방지원병', 0x2d2f4: '회복지원병',
    0x2d300: '요격격퇴병', 0x2d30c: '　　무사　', 0x2d33c: '인술첩보병', 0x2d348: '공격마장병',
    0x2d354: '간호마장병', 0x2d360: '유격비공병', 0x2d36c: '강습비공병',
}
DESC = {
    0x2d390: '기동력을 살린 대마장병 장비/개인 근접전에 능하다',
    0x2d3e0: '요격용으로 장갑을 강화한 장비/최전선에서 기동병을 친다',
    0x2d430: '주로 연술에 약한 중장갑병/등을 노리는 ＭＥＳ 장비',
    0x2d480: '최신 기술을 구사한 비공 장비/지형 효과를 받지 않는다',
    0x2d4d0: '화계 대기원소 증폭 마장 장비/화계 연술에 약한 적을 구축',
    0x2d520: '수계 대기원소 증폭 마장 장비/통신 시스템 탑재 특수 유닛',
    0x2d570: '풍계 대기원소 증폭 마장 장비/풍계 연술에 약한 적을 구축',
    0x2d5c0: '토계 대기원소 증폭 마장 장비/통신 시스템 탑재 특수 유닛',
    0x2d610: '광대한 기동력의 초수기병 장비/어떤 적에게도 유리하게 싸운다',
    0x2d660: '셸퍼에서 내린 상태/순발력을 살린 대마장병 장비',
    0x2d6b0: '격투술로 유격 임무를 수행/경장보병과의 백병전에 능하다',
    0x2d700: '게릴라전 야간전 특수공작 장비/암기를 쓰는 암살 임무에 능숙',
    0x2d750: '대중갑병용 연술병기ＭＥＳ 탑재/격투전용으로 개량한 최신 장비',
    0x2d7a0: '후방 지원 공격용 장비/총화기로 다양하게 공격한다',
    0x2d7f0: '최신 포격병기 Ｇ－건을 구사/거점 방위가 주임무인 포격병',
    0x2d840: '국지전용 총기를 다수 탑재/화력이 매력인 요격격퇴병 장비',
    0x2d890: '최전선 근접전을 상정한 중장비/기동보병 상대로 무적을 자랑',
    0x2d8e0: '로열가드라 불리는 근위 장비/공방의 균형이 잡힌 전사',
    0x2d930: '의료 기능 탑재 후방지원 장비/전투 중 부상병을 응급처치',
    0x2d980: '의료 지원 전용 유닛/모든 이상 상태를 지원한다',
    0x2d9d0: '배틀 모드로 메모리 변환된/국지 전투용 기인',
    0x2da20: '「은빛뇌명」이라 불린 기동보병/풍부한 전투경험이 강함의 비결',
}


def _full(s):
    return ''.join(hg.HALF2FULL.get(c, c) for c in s)


def texts():
    out = {o: _full(k) for o, k in CLASS.items()}
    for o, k in DESC.items():
        a, b = k.split('/')
        assert len(_full(a)) <= 16 and len(_full(b)) <= 16, k
        out[o] = _full(a) + '\n' + _full(b)
    return out


EQ_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'text', 'ko', 'equip.txt')
EQ_START, EQ_END = 0x2db60, 0x37500


def _strings(B):
    """블록의 장비 문자열 목록: (접두 포함 시작, 본문 시작, 본문 일본어)"""
    out = []
    o = EQ_START
    while o < EQ_END:
        if B[o] == 0: o += 1; continue
        e = B.find(b'\0', o)
        k = o
        while k < e and B[k] < 0x80: k += 1
        if k < e: out.append((o, k, bytes(B[k:e]).decode('cp932')))
        o = e
    return out


def eq_texts(B, exe_dict):
    """본문 시작 오프셋 -> 번역(\n 줄바꿈)"""
    import re
    tr = {}
    for l in open(EQ_FILE, encoding='utf-8'):
        l = l.rstrip('\n')
        if not l or l.startswith('#'): continue
        o, k = l.split('\t'); tr[int(o, 16)] = k
    S = _strings(B)
    names = dict(exe_dict)
    for o, k, ja in S:
        if not ja.startswith('＜') and '：' not in ja and o in tr:
            names[ja] = tr[o]
    out = {}
    for o, k, ja in S:
        if ja.startswith('＜'):
            body = tr[o]
            if not body.startswith('＜'):
                t = re.match('＜(.*?)＞', ja).group(1)
                body = '＜' + names[t] + '＞/' + body
            lines = [_full(x) for x in body.split('/')]
            for x in lines[1:]: assert len(x) <= 16, (hex(o), x)
            out[k] = '\n'.join(lines)
        elif '：' in ja:
            out[k] = _full(tr[o])
        elif o in tr and o < 0x2dd00:
            a, b = tr[o].split('/')
            assert len(_full(a)) <= 16 and len(_full(b)) <= 16, tr[o]
            out[k] = _full(a) + '\n' + _full(b)
        else:
            out[k] = _full(tr.get(o) or names[ja.strip('\u3000')])
    return out


def patch_block(kd, hdr, extra, exe_dict, fixed=()):
    """kd: KODAIRA bytearray(제자리 수정). extra: 이 화면에 나올 수 있는 EXE 쪽 비고정 한글"""
    s, n = hdr[BLK]
    base = s * 2048
    B = kd[base:base + n * 2048]
    T = texts()
    T.update(eq_texts(B, exe_dict))
    syl = []
    for o in sorted(T):
        e = B.find(b'\0', o)
        nxt = e
        while B[nxt] == 0 and nxt < TAB_OFF: nxt += 1
        kb = hg.encode_text(T[o])
        assert len(kb) < nxt - o, (T[o], len(kb), nxt - o)
        B[o:nxt] = kb.ljust(nxt - o, b'\0')
        for c in T[o]:
            if hg.is_hangul(c) and c not in syl and c not in fixed: syl.append(c)
    for c in extra:
        if c not in syl: syl.append(c)
    assert len(syl) <= NMAX, len(syl)
    # 폰트 3페이지(연속 608행)
    rows = 38 * 16
    pix = np.zeros((rows, 256), np.uint8)
    for k, ch in enumerate(syl):
        pix[(k // 21) * 16:(k // 21) * 16 + 16, (k % 21) * 12:(k % 21) * 12 + 12] = hg.glyph(ch)
    p = pix.reshape(-1)
    B[FONT_OFF:FONT_OFF + rows * 128] = ((p[0::2] & 15) | ((p[1::2] & 15) << 4)).astype(np.uint8).tobytes()
    tab = bytearray(0x3f0 * 6)
    for k, ch in enumerate(syl):
        struct.pack_into('<HHH', tab, k * 6, hg.ENC[ch], k % 21, k // 21)
    B[TAB_OFF:TAB_OFF + len(tab)] = tab
    kd[base:base + n * 2048] = B
    return len(syl)


# ---- 8x8 작은 폰트 ----
STAB = 0x80099ec4 - 0x80010000 + 0x800
SMALL_Y = 216
# 한글로 바꿀 칸: 잘 안 쓰는 기호와 반각 가나 (숫자·영문·－．／・ 는 유지)
SLOTS = list(range(1, 13)) + list(range(26, 33)) + list(range(59, 67)) + list(range(68, 128)) + [42, 49, 58]  # J Q Z 도 사용
SLOTS = [i for i in SLOTS if i % 32 != 31]  # 각 행 마지막 칸(x=248)은 실행 중 다른 그림에 덮임
GAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'Galmuri7.ttf')
_sg = {}


def small_glyph(ch):
    """7x7 본체(12) + 오른쪽/아래 그림자(8) 8x8"""
    if ch in _sg: return _sg[ch]
    from PIL import Image, ImageDraw, ImageFont
    F = ImageFont.truetype(GAL, 8)
    im = Image.new('L', (16, 16), 0); d = ImageDraw.Draw(im); d.fontmode = '1'
    d.text((0, 0), ch, 255, font=F)
    a = np.array(im) > 0
    body = a[1:8, 0:7]
    g = np.zeros((8, 8), np.uint8)
    sh = np.zeros((8, 8), bool); sh[1:8, 1:8] = body
    B = np.zeros((10, 10), bool); B[1:8, 1:8] = body  # 1칸 여백
    for r in range(8):
        for c in range(8):
            if sh[r, c] and ((B[r + 1, c] and B[r + 1, c + 2]) or (B[r, c + 1] and B[r + 2, c + 1])):
                sh[r, c] = False  # 획 사이 틈은 그림자로 메우지 않음
    g[sh] = 8
    g[:7, :7][body] = 12
    _sg[ch] = g
    return g


def small_set(names):
    out = []
    for nm in names:
        for c in nm:
            if hg.is_hangul(c) and c not in out: out.append(c)
    assert len(out) <= len(SLOTS), (len(out), len(SLOTS))
    return out


def patch_small_table(exe, syl):
    for i, ch in zip(SLOTS, syl):
        struct.pack_into('<H', exe, STAB + i * 2, hg.ENC[ch])


def patch_small_font(buf, sig, syl):
    """폰트1 사본(서명으로 찾음)의 작은 폰트 칸에 한글 기록"""
    n = 0
    i = buf.find(sig)
    while i >= 0:
        po = i - 128 * 40
        for slot, ch in zip(SLOTS, syl):
            g = small_glyph(ch)
            x = (slot % 32) * 8; y = SMALL_Y + (slot // 32) * 8
            for r in range(8):
                o = po + (y + r) * 128 + x // 2
                buf[o:o + 4] = bytes(int(g[r, 2 * j]) | (int(g[r, 2 * j + 1]) << 4) for j in range(4))
        n += 1
        i = buf.find(sig, i + 1)
    return n
