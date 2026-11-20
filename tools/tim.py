# TIM 파싱/렌더/재인코딩 + PCK 컨테이너
import struct,os,glob
import numpy as np
from PIL import Image
def parse(d,o=0):
    """-> dict(bpp, clut:(x,y,w,h,arr u16), img:(x,y,w16,h,raw bytes), end)"""
    tag,fl=struct.unpack_from('<II',d,o)
    if tag!=0x10: return None
    bpp=fl&3; p=o+8; clut=None
    if fl&8:
        ln,x,y,w,h=struct.unpack_from('<IHHHH',d,p)
        if ln!=12+w*h*2 or w==0 or h==0: return None
        clut=dict(x=x,y=y,w=w,h=h,off=p+12,data=np.frombuffer(d,np.uint16,w*h,p+12).reshape(h,w)); p+=ln
    ln,x,y,w,h=struct.unpack_from('<IHHHH',d,p)
    if ln!=12+w*h*2 or w==0 or h==0 or bpp>2: return None
    raw=d[p+12:p+ln]
    return dict(bpp=bpp,clut=clut,x=x,y=y,w=w,h=h,off=p+12,raw=raw,end=p+ln,start=o)
def pix(t):
    w,h=t['w'],t['h']; r=np.frombuffer(t['raw'],np.uint8)
    if t['bpp']==0:
        a=np.empty(w*h*4,np.uint8); a[0::2]=r&15; a[1::2]=r>>4; return a.reshape(h,w*4)
    if t['bpp']==1: return r.reshape(h,w*2)
    return np.frombuffer(t['raw'],np.uint16).reshape(h,w)
def c15(v):
    v=v.astype(np.uint32)
    rgb=np.stack([(v&31)<<3,((v>>5)&31)<<3,((v>>10)&31)<<3],-1).astype(np.uint8)
    a=np.where(v==0,0,255).astype(np.uint8)
    return np.concatenate([rgb,a[...,None]],-1)
def render(t,cl=0):
    p=pix(t)
    if t['bpp']==2: return Image.fromarray(c15(p),'RGBA')
    pal=t['clut']['data']
    pal=pal.reshape(-1,16 if t['bpp']==0 else 256)[cl] if pal.size>=(16 if t['bpp']==0 else 256) else pal.ravel()
    return Image.fromarray(c15(pal[p]),'RGBA')
def pck(d):
    """[u32 n][u32 size][data]... -> [(off,size)]"""
    n=struct.unpack_from('<I',d,0)[0]; o=4; out=[]
    if not 0<n<2000: return None
    for i in range(n):
        if o+4>len(d): return None
        s=struct.unpack_from('<I',d,o)[0]; o+=4
        if o+s>len(d): return None
        out.append((o,s)); o+=s
    return out if o==len(d) or len(d)-o<2048 else None
def scan(d):
    """파일 안 모든 TIM (4바이트 정렬)"""
    out=[];o=0
    while o<len(d)-20:
        if d[o]==0x10 and d[o+1:o+4]==b'\0\0\0' and d[o+4] in (0,1,2,8,9) and d[o+5:o+8]==b'\0\0\0':
            t=parse(d,o)
            if t: out.append(t); o=t['end']; continue
        o+=4
    return out
def scan2(d):
    """scan()이 놓친 2바이트 정렬 TIM까지 (scan 결과 + 추가분, 오프셋 순)"""
    out=[];o=0
    while o<len(d)-20:
        if d[o]==0x10 and d[o+1:o+4]==b'\0\0\0' and d[o+4] in (0,1,2,8,9) and d[o+5:o+8]==b'\0\0\0':
            t=parse(d,o)
            if t: out.append(t); o=t['end']; continue
        o+=2
    return out
