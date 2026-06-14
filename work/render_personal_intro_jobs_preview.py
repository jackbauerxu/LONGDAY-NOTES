from PIL import Image, ImageDraw, ImageFont, ImageFilter


W, H = 1600, 1000
bg = (248, 248, 246)
ink = (18, 18, 18)
soft = (108, 108, 104)
line = (218, 218, 214)
panel = (255, 255, 253)
mist = (232, 232, 228)
accent = (86, 96, 92)


def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


sans_path = "/System/Library/Fonts/HelveticaNeue.ttc"
cn_path = "/System/Library/Fonts/Hiragino Sans GB.ttc"

f_display = font(sans_path, 88)
f_display_small = font(sans_path, 42)
f_nav = font(sans_path, 18)
f_cn_32 = font(cn_path, 32)
f_cn_26 = font(cn_path, 26)
f_cn_22 = font(cn_path, 22)
f_cn_18 = font(cn_path, 18)
f_cn_16 = font(cn_path, 16)


def size(draw, text, ft):
    b = draw.textbbox((0, 0), text, font=ft)
    return b[2] - b[0], b[3] - b[1]


def wrap(draw, text, ft, max_w):
    lines = []
    buf = ""
    for ch in text:
        trial = buf + ch
        if size(draw, trial, ft)[0] <= max_w:
            buf = trial
        else:
            if buf:
                lines.append(buf)
            buf = ch
    if buf:
        lines.append(buf)
    return lines


def multiline(draw, xy, text, ft, fill, max_w, gap):
    x, y = xy
    for line_text in wrap(draw, text, ft, max_w):
        draw.text((x, y), line_text, font=ft, fill=fill)
        y += ft.size + gap
    return y


def rounded_rect_layer(size_xy, radius, fill, shadow=False):
    w, h = size_xy
    layer = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if shadow:
        d.rounded_rectangle((40, 45, 40 + w, 45 + h), radius=radius, fill=(0, 0, 0, 34))
        layer = layer.filter(ImageFilter.GaussianBlur(18))
        d = ImageDraw.Draw(layer)
    d.rounded_rectangle((40, 40, 40 + w, 40 + h), radius=radius, fill=fill)
    return layer


img = Image.new("RGB", (W, H), bg)
draw = ImageDraw.Draw(img)

# Soft background planes.
draw.rectangle((0, 0, W, H), fill=bg)
draw.ellipse((940, 120, 1580, 760), fill=(238, 238, 234))
draw.ellipse((1040, 190, 1480, 640), fill=(243, 243, 240))
blur = img.filter(ImageFilter.GaussianBlur(28))
img = Image.blend(img, blur, 0.55)
draw = ImageDraw.Draw(img)

# Header.
draw.text((72, 48), "Uzbek Notes", font=f_nav, fill=ink)
for x, t in [(1180, "专题"), (1260, "城市"), (1340, "索引"), (1420, "关于")]:
    draw.text((x, 48), t, font=f_cn_16, fill=soft)

# Hero.
draw.text((72, 154), "A quieter guide", font=f_display, fill=ink)
draw.text((76, 246), "to living well abroad.", font=f_display, fill=ink)
headline = "把复杂的出行、通信、支付和住宿登记，整理成一眼能懂的个人资料库。"
multiline(draw, (82, 376), headline, f_cn_32, ink, 760, 14)
body = "这是一个给自己和朋友反复查阅的网站。内容来自小红书原帖整理、人工核对和实用经验沉淀。没有夸张包装，只有清楚、可靠、好维护的专题页面。"
multiline(draw, (84, 500), body, f_cn_22, soft, 760, 12)

# Small command row.
draw.rounded_rectangle((82, 650, 330, 706), radius=28, fill=ink)
draw.text((126, 665), "开始阅读", font=f_cn_18, fill=(255, 255, 255))
draw.text((370, 666), "6 个已完成专题  /  Markdown 持续维护", font=f_cn_18, fill=soft)

# Right main device-like content panel.
card = rounded_rect_layer((510, 640), 34, panel + (255,), shadow=True)
img.paste(card, (965, 152), card)
draw = ImageDraw.Draw(img)
cx, cy = 1005, 192
draw.rounded_rectangle((cx, cy, cx + 510, cy + 640), radius=34, outline=(230, 230, 226), width=1)
draw.text((cx + 42, cy + 46), "专题", font=f_cn_22, fill=soft)
draw.text((cx + 42, cy + 84), "乌兹别克斯坦生活资料库", font=f_cn_32, fill=ink)
draw.line((cx + 42, cy + 146, cx + 468, cy + 146), fill=line, width=1)

items = [
    ("01", "入境攻略", "材料、流程、机票、申报提醒"),
    ("02", "手机卡登记", "电话卡、运营商、现场办理"),
    ("03", "卡槽 IMEI", "机场登记、市区补办、费用"),
    ("04", "支付与取款", "银联、现金、Yandex Go 付款"),
    ("05", "小白条", "住宿登记、出境抽查、保存方式"),
]

y = cy + 176
for num, title, desc in items:
    draw.text((cx + 42, y + 6), num, font=f_nav, fill=accent)
    draw.text((cx + 98, y), title, font=f_cn_26, fill=ink)
    draw.text((cx + 98, y + 38), desc, font=f_cn_16, fill=soft)
    draw.line((cx + 42, y + 78, cx + 468, y + 78), fill=line, width=1)
    y += 92

draw.rounded_rectangle((cx + 42, cy + 556, cx + 230, cy + 604), radius=24, fill=(242, 242, 238))
draw.text((cx + 72, cy + 569), "全文搜索", font=f_cn_16, fill=ink)
draw.text((cx + 292, cy + 570), "Last updated 2026.06", font=f_nav, fill=soft)

# Bottom modules.
draw.line((72, 846, W - 72, 846), fill=line, width=1)
modules = [
    ("Minimal", "单色基调，靠留白和排版建立高级感。"),
    ("Readable", "正文舒服，专题页适合长期查阅。"),
    ("Maintainable", "Markdown 写内容，保存后自动发布。"),
]
for i, (title, desc) in enumerate(modules):
    x = 82 + i * 430
    draw.text((x, 884), title, font=f_display_small, fill=ink)
    multiline(draw, (x, 934), desc, f_cn_18, soft, 320, 8)

out = "/Users/g90/Documents/Codex/2026-06-13/hermes/outputs/personal_intro_site_jobs_style_preview.png"
img.save(out)
print(out)
