import io, sys
from fontTools.cffLib import CFFFontSet
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.boundsPen import BoundsPen
D=sys.argv[1]
def load(p):
    c=CFFFontSet(); c.decompile(io.BytesIO(open(p,'rb').read()),None)
    return c[c.fontNames[0]].CharStrings
DIG=dict(zero='0',one='1',two='2',three='3',four='4',five='5',six='6',seven='7',eight='8',nine='9')
def build(sources, mapping_fn, out, name):
    glyphs={}; cmap={}; widths={}
    order=['.notdef','space']
    pen=TTGlyphPen(None); glyphs['.notdef']=pen.glyph(); widths['.notdef']=(500,0)
    pen=TTGlyphPen(None); glyphs['space']=pen.glyph(); widths['space']=(280,0); cmap[32]='space'
    for ch,(src,gn) in mapping_fn().items():
        cs=sources[src][gn]
        tp=TTGlyphPen(None); cs.draw(Cu2QuPen(tp,1.0,reverse_direction=True))
        g='g%04x'%ord(ch); glyphs[g]=tp.glyph(); order.append(g)
        bp=BoundsPen(None); cs.draw(bp)
        widths[g]=(int(cs.width), int(bp.bounds[0]) if bp.bounds else 0); cmap[ord(ch)]=g
    fb=FontBuilder(1000,isTTF=True); fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(widths)
    fb.setupHorizontalHeader(ascent=900,descent=-250); fb.setupNameTable({'familyName':name,'styleName':'Regular'})
    fb.setupOS2(sTypoAscender=900,sTypoDescender=-250,usWinAscent=1000,usWinDescent=300); fb.setupPost(); fb.save(out)
    print(out, sorted(chr(c) for c in cmap))
K1=load(f'{D}/DBEMCM+Kokoschka_11.cff'); K2=load(f'{D}/PZMBOO+Kokoschka_73.cff')
def kmap():
    m={}
    def find(names):
        for n in names:
            for s,cs in (('k1',K1),('k2',K2)):
                if n in cs.charStrings: return (s,n)
    for c in 'abcdefghijklmnopqrstuvwxyz':
        u=c.upper()
        m[u]=find([u,c,c+'.3']); m[c]=find([c,c+'.3',u])
    for n,d in DIG.items(): m[d]=find([n])
    m['-']=find(['hyphen']); m['€']=find(['Euro'])
    return {k:v for k,v in m.items() if v}
build({'k1':K1,'k2':K2},kmap,f'{D}/Kokoschka-casa.ttf','KokoschkaCasa')
SB=load(f'{D}/DBEMCM+Stolzl-Bold_19.cff')
def sbmap():
    m={}
    for n in SB.charStrings.keys():
        if n=='.notdef': continue
        m[DIG.get(n,n)]=('b',n)
    return m
build({'b':SB},sbmap,f'{D}/Stolzl-Bold-casa.ttf','StolzlBoldCasa')
L1=load(f'{D}/DBEMCM+Stolzl-Light_17.cff'); L2=load(f'{D}/PZMBOO+Stolzl-Light_74.cff')
def slmap():
    m={}
    for s,cs in (('l1',L1),('l2',L2)):
        for n in cs.charStrings.keys():
            if n in ('.notdef','space'): continue
            ch={'egrave':'è'}.get(n,DIG.get(n,n)); m.setdefault(ch,(s,n))
    return m
build({'l1':L1,'l2':L2},slmap,f'{D}/Stolzl-Light-casa.ttf','StolzlLightCasa')
