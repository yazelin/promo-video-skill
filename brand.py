#!/usr/bin/env python3
"""promo-video 品牌/合成工具箱(PIL)。改頂部 CONFIG 就能用;也可 import 各函式。
守比例是鐵律(GOTCHA 1):背景 cover(等比裁切)、主體 contain(等比放入),絕不非等比 scale。
QR 走 api.qrserver.com(GOTCHA 8);上線前手機掃一次。
"""
import os, sys, glob, subprocess
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont

# ── CONFIG(每專案換)─────────────────────────────
BRAND   = "catime"                              # 字標
URL     = "yazelin.github.io/example"           # 常駐角標 / CTA 網址
HANDLE  = "@example"                             # 社群 handle
QR_LINK = "https://t.me/example"                # QR 目標(公開連結)
PINK=(255,107,157); CREAM=(255,245,249); GRAY=(138,107,118); DARK=(43,43,43); GOLD=(217,178,90)
FB = os.path.expanduser("~/.local/share/fonts/1NotoSansTC-Black.ttf")   # 黑體(字標)
FR = os.path.expanduser("~/.local/share/fonts/NotoSansTC-Bold.ttf")     # 粗體(內文)
# ─────────────────────────────────────────────────

def F(p, s): return ImageFont.truetype(p, s)
def _rr(d, xy, r, **k): d.rounded_rectangle(xy, radius=r, **k)
def ctext(d, cx, y, f, t, fill):
    w = d.textlength(t, font=f); d.text((cx-w/2, y), t, font=f, fill=fill); return w

def cover(im, W, H, blur=30, bright=0.7):
    """等比放大 + 裁切填滿 WxH(當模糊背景)。守比例。"""
    r = max(W/im.width, H/im.height); b = im.resize((int(im.width*r), int(im.height*r)))
    b = b.crop(((b.width-W)//2, (b.height-H)//2, (b.width-W)//2+W, (b.height-H)//2+H))
    return ImageEnhance.Brightness(b.filter(ImageFilter.GaussianBlur(blur))).enhance(bright)

def contain(im, mw, mh):
    """等比縮放放入 mw×mh(主體,完整不裁)。守比例。"""
    r = min(mw/im.width, mh/im.height); return im.resize((int(im.width*r), int(im.height*r)))

def composite(catfile, W, H, out, fg_w=0.92, fg_h=0.62, write_h=True):
    """模糊底 + 主體垂直置中。回傳並可寫圖高 sidecar(給文字貼緣用,GOTCHA 4)。"""
    im = Image.open(catfile).convert("RGB"); bg = cover(im, W, H)
    fg = contain(im, int(W*fg_w), int(H*fg_h)); bg.paste(fg, ((W-fg.width)//2, (H-fg.height)//2))
    bg.save(out)
    if write_h: open(out.rsplit(".",1)[0]+".h", "w").write(str(fg.height))
    return fg.height

def corner_tag(W, H, out, scale=1.0):
    """常駐角標(透明全幀,左上 pill:BRAND + URL)。整支 overlay。GOTCHA 12。"""
    img = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(img)
    f1, f2 = F(FB, int(32*scale)), F(FR, int(21*scale))
    pad, x0, y0 = int(14*scale), int(28*scale), int(30*scale)
    w = max(d.textlength(BRAND, font=f1), d.textlength(URL, font=f2)) + pad*2
    h = int(34*scale)+int(21*scale)+pad*2+6
    _rr(d, [x0,y0,x0+w,y0+h], int(10*scale), fill=(20,18,20,150))
    d.text((x0+pad, y0+pad-2), BRAND, font=f1, fill=PINK)
    d.text((x0+pad, y0+pad+int(34*scale)+4), URL, font=f2, fill=CREAM)
    img.save(out)

def qr_fetch(out, size=440):
    """QR via API(PEP668 裝不了 lib 時)。只放公開連結。"""
    c1, c2 = "43-43-43", "255-245-249"
    subprocess.run(["curl","-s","-L","-o",out,
        f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&margin=10&color={c1}&bgcolor={c2}&data={QR_LINK}"], check=True)

def minigrid(files, side):
    """n×n 迷你圖庫縮圖(CTA 用,讓網站那側具體)。"""
    import math; n = int(math.isqrt(len(files))) or 1; cell = side//n
    g = Image.new("RGB", (cell*n, cell*n), (240,225,232))
    for i, f in enumerate(files[:n*n]):
        im = Image.open(f).convert("RGB"); r = max(cell/im.width, cell/im.height)
        b = im.resize((int(im.width*r), int(im.height*r)))
        b = b.crop(((b.width-cell)//2,(b.height-cell)//2,(b.width-cell)//2+cell,(b.height-cell)//2+cell))
        g.paste(b, ((i%n)*cell, (i//n)*cell))
    return g

def ratio_check(files):
    """GOTCHA 1 稽核:每張圖 原始比例 vs contain 顯示比例,回傳最大誤差%。"""
    worst = 0.0
    for f in files:
        im = Image.open(f); w, h = im.size; orig = w/h
        r = min(1000/w, 1000/h)  # 代表性 contain box(避免 1px 捨入除零)
        disp = (int(w*r))/(int(h*r))
        worst = max(worst, abs(orig-disp)/orig*100)
    return worst

if __name__ == "__main__":
    # demo/self-check:合成一張 + 角標 + QR + 比例稽核
    imgs = sorted(glob.glob(sys.argv[1]+"/*"))[:9] if len(sys.argv) > 1 else []
    out = os.path.dirname(os.path.abspath(__file__)) + "/_demo"
    os.makedirs(out, exist_ok=True)
    corner_tag(1080, 1920, f"{out}/corner.png")
    try: qr_fetch(f"{out}/qr.png")
    except Exception as e: print("QR skip:", e)
    if imgs:
        composite(imgs[0], 1080, 1920, f"{out}/reveal.png")
        assert ratio_check(imgs) < 0.1, "比例失真!"
        print(f"ok — ratio worst {ratio_check(imgs):.3f}%  (<0.1 過)")
    print("brand.py demo →", out)
