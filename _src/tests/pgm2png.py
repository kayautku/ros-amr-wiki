import zlib,struct,re,sys
src=sys.argv[1]; dst=sys.argv[2]; S=int(sys.argv[3]) if len(sys.argv)>3 else 2
d=open(src,"rb").read()
m=re.match(rb"P5\s+(?:#.*\n)?\s*(\d+)\s+(\d+)\s+255\s",d); w,h=int(m.group(1)),int(m.group(2)); px=d[m.end():]
rows=[y for y in range(h) if any(px[y*w+x]!=205 for x in range(w))]
cols=[x for x in range(w) if any(px[y*w+x]!=205 for y in range(h))]
y0,y1,x0,x1=min(rows),max(rows),min(cols),max(cols)
W=x1-x0+1; H=y1-y0+1
crop=bytearray()
for y in range(y0,y1+1): crop+=px[y*w+x0:y*w+x1+1]
big=bytearray()
for y in range(H):
    row=b"".join(bytes([crop[y*W+x]])*S for x in range(W)); big+=row*S
def ch(t,c): return struct.pack(">I",len(c))+t+c+struct.pack(">I",zlib.crc32(t+c)&0xffffffff)
raw=b"".join(b"\x00"+bytes(big[y*W*S:(y+1)*W*S]) for y in range(H*S))
open(dst,"wb").write(b"\x89PNG\r\n\x1a\n"+ch(b"IHDR",struct.pack(">IIBBBBB",W*S,H*S,8,0,0,0,0))+ch(b"IDAT",zlib.compress(raw))+ch(b"IEND",b""))
print(f"harita {w}x{h}; bilinen bölge {W}x{H} hücre ({W*0.05:.1f} x {H*0.05:.1f} m); png {W*S}x{H*S}")
