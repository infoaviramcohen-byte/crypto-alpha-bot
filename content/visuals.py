#!/usr/bin/env python3
"""Branded visual card generator for the Crypto News AI daily series."""
from PIL import Image, ImageDraw, ImageFont
import textwrap

W = H = 1080
GREEN=(20,241,149); PURPLE=(153,69,255); WHITE=(236,239,246)
RED=(255,95,95); GOLD=(255,196,0); MUT=(150,157,172); DIM=(95,102,118)

def font(sz):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc"]:
        try: return ImageFont.truetype(p, sz)
        except: pass
    return ImageFont.load_default()

def _lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

def _fit(d, text, start, maxw, stroke=2):
    s=start
    while s>34:
        f=font(s); bb=d.textbbox((0,0),text,font=f,stroke_width=stroke)
        if bb[2]-bb[0]<=maxw: return f
        s-=2
    return font(34)

def _center(d, text, f, y, fill, stroke=0):
    bb=d.textbbox((0,0),text,font=f,stroke_width=stroke); w=bb[2]-bb[0]
    d.text(((W-w)//2-bb[0],y),text,font=f,fill=fill,stroke_width=stroke,stroke_fill=(0,0,0))

def render_card(out_path, title, subtitle, lines, accent=GREEN):
    """lines = list of (text, color). Empty text = spacer."""
    top=tuple(min(255,int((14,18,26)[i]+accent[i]*0.05)) for i in range(3)); bot=(9,11,18)
    img=Image.new("RGB",(W,H),top); d=ImageDraw.Draw(img)
    for y in range(H): d.line([(0,y),(W,y)],fill=_lerp(top,bot,y/H))
    # accent glow
    glow=Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    gd.ellipse([W-620,-380,W+260,320],fill=(*accent,40))
    gd.ellipse([-260,H-360,320,H+260],fill=(*PURPLE,28))
    img=Image.alpha_composite(img.convert("RGBA"),glow).convert("RGB"); d=ImageDraw.Draw(img)
    M=90
    # brand + accent bar + bolt
    d.text((M,62),"CRYPTO NEWS AI",font=font(38),fill=GREEN)
    bar=Image.new("RGB",(220,10),GREEN); bd=ImageDraw.Draw(bar)
    for i in range(220): bd.line([(i,0),(i,10)],fill=_lerp(GREEN,PURPLE,i/220))
    img.paste(bar,(M,116)); d=ImageDraw.Draw(img)
    d.polygon([(W-148,60),(W-110,60),(W-128,112),(W-98,112),(W-158,190),(W-136,132),(W-166,132)],fill=GREEN)
    # title (auto-fit)
    tf=_fit(d,title,96,W-2*M,stroke=2)
    tb=d.textbbox((0,0),title,font=tf,stroke_width=2)
    _center(d,title,tf,236,WHITE,stroke=2)
    # subtitle
    if subtitle: _center(d,subtitle,font(42),236+(tb[3]-tb[1])+28,accent)
    # divider
    d.line([(M,392),(W-M,392)],fill=(40,46,60),width=3)
    # body lines (left aligned)
    y=440; lf=font(48)
    for text,color in lines:
        if not text: y+=30; continue
        d.text((M,y),text,font=lf,fill=color or WHITE); y+=70
    # footer
    _center(d,"@cryptonewsweb_3",font(32),H-78,MUT)
    img.save(out_path,"PNG")
    return out_path

def wrap_lines(text, width, color=WHITE):
    """Wrap a paragraph into card lines."""
    out=[]
    for para in text.split("\n"):
        for ln in textwrap.wrap(para, width=width) or [""]:
            out.append((ln, color))
    return out
