from PIL import Image, ImageDraw, ImageFont, ImageFilter


W, H = 1600, 1000
paper = (247, 245, 239)
ink = (36, 33, 28)
muted = (112, 106, 96)
line = (216, 210, 199)
sage = (126, 139, 122)
clay = (183, 111, 82)
cream = (255, 250, 241)


def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


serif_path = "/System/Library/Fonts/Supplemental/Songti.ttc"
sans_path = "/System/Library/Fonts/Hiragino Sans GB.ttc"
latin_path = "/System/Library/Fonts/HelveticaNeue.ttc"

f_serif_86 = font(serif_path, 86)
f_serif_36 = font(serif_path, 36)
f_serif_30 = font(serif_path, 30)
f_sans_24 = font(sans_path, 24)
f_sans_22 = font(sans_path, 22)
f_sans_20 = font(sans_path, 20)
f_sans_18 = font(sans_path, 18)
f_sans_16 = font(sans_path, 16)
f_latin_18 = font(latin_path, 18)


def text_size(draw, text, ft):
    box = draw.textbbox((0, 0), text, font=ft)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw, text, ft, max_width):
    lines = []
    current = ""
    for ch in text:
        candidate = current + ch
        if text_size(draw, candidate, ft)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_multiline(draw, xy, text, ft, fill, max_width, line_gap):
    x, y = xy
    for line_text in wrap_text(draw, text, ft, max_width):
        draw.text((x, y), line_text, font=ft, fill=fill)
        y += ft.size + line_gap
    return y


img = Image.new("RGB", (W, H), paper)
draw = ImageDraw.Draw(img)

# Fine paper grain.
grain = Image.effect_noise((W, H), 7).convert("L")
grain_rgb = Image.merge("RGB", (grain, grain, grain))
img = Image.blend(img, grain_rgb, 0.035)
draw = ImageDraw.Draw(img)

# Header.
draw.line((64, 86, W - 64, 86), fill=line, width=1)
draw.text((72, 36), "Lin / Notes", font=f_serif_30, fill=ink)
for x, label in [(1160, "About"), (1265, "Journal"), (1382, "Contact")]:
    draw.text((x, 43), label, font=f_latin_18, fill=muted)

# Layout divider.
left_w = 950
draw.line((left_w, 86, left_w, H - 72), fill=line, width=1)
draw.line((64, H - 72, W - 64, H - 72), fill=line, width=1)

# Eyebrow.
draw.line((82, 174, 132, 174), fill=sage, width=2)
draw.text((152, 160), "Personal essays, field notes, quiet work", font=f_latin_18, fill=sage)

# Hero copy.
headline = "写一些长期有用的观察，也记录生活里真实的纹理。"
draw_multiline(draw, (80, 220), headline, f_serif_86, ink, 770, 10)
lead = "这是一个以个人内容为中心的网站：不堆砌头衔，不急着证明什么，只把经历、阅读、旅行和项目里的思考整理成可被反复阅读的文字。"
draw_multiline(draw, (84, 514), lead, f_sans_24, muted, 710, 14)

# Content topics.
topic_y = 748
draw.line((80, topic_y, left_w - 72, topic_y), fill=line, width=1)
topic_w = (left_w - 152) // 3
topics = [
    ("01", "生活观察", "关于城市、关系、节奏与选择，保留一点距离，也保留一点温度。"),
    ("02", "旅行笔记", "把路上的信息、细节和判断沉淀下来，少一点攻略腔，多一点真实经验。"),
    ("03", "长期项目", "展示正在慢慢推进的研究、创作或产品想法，像一间开放的工作室。"),
]
for i, (num, title, body) in enumerate(topics):
    x = 80 + i * topic_w
    if i:
        draw.line((x - 22, topic_y, x - 22, H - 106), fill=line, width=1)
    draw.text((x, topic_y + 34), num, font=f_sans_16, fill=clay)
    draw.text((x, topic_y + 70), title, font=f_sans_24, fill=ink)
    draw_multiline(draw, (x, topic_y + 112), body, f_sans_18, muted, topic_w - 55, 8)

# Right visual area: quiet editorial photo-like panel.
vx0, vy0, vx1, vy1 = left_w + 1, 86, W, H - 72
visual = Image.new("RGB", (vx1 - vx0, vy1 - vy0), (164, 157, 141))
vdraw = ImageDraw.Draw(visual)
for y in range(visual.height):
    ratio = y / visual.height
    r = int(154 + ratio * 38)
    g = int(148 + ratio * 28)
    b = int(130 + ratio * 18)
    vdraw.line((0, y, visual.width, y), fill=(r, g, b))

# Architectural shadow shapes.
vdraw.polygon([(0, 0), (visual.width * 0.72, 0), (visual.width * 0.42, visual.height)], fill=(118, 121, 108))
vdraw.polygon([(visual.width * 0.52, 0), (visual.width, 0), (visual.width, visual.height), (visual.width * 0.68, visual.height)], fill=(205, 188, 159))
vdraw.rectangle((90, 88, 355, 630), fill=(235, 224, 202))
vdraw.rectangle((145, 148, 300, 580), fill=(70, 80, 77))
vdraw.rectangle((365, 170, 455, 740), fill=(92, 95, 84))
vdraw.polygon([(80, 705), (visual.width, 595), (visual.width, visual.height), (0, visual.height)], fill=(84, 83, 72))

for x in range(120, 332, 38):
    vdraw.line((x, 165, x, 560), fill=(111, 122, 116), width=2)
for y in range(210, 540, 56):
    vdraw.line((144, y, 300, y), fill=(111, 122, 116), width=2)

visual = visual.filter(ImageFilter.GaussianBlur(0.35))
img.paste(visual, (vx0, vy0))
draw = ImageDraw.Draw(img)

# Soft overlay to keep the right side restrained.
overlay = Image.new("RGBA", (vx1 - vx0, vy1 - vy0), (17, 16, 14, 35))
img.paste(Image.alpha_composite(img.crop((vx0, vy0, vx1, vy1)).convert("RGBA"), overlay).convert("RGB"), (vx0, vy0))
draw = ImageDraw.Draw(img)

# Right bottom panel.
panel = (left_w + 58, H - 322, W - 66, H - 126)
draw.rectangle(panel, fill=(45, 42, 36), outline=(211, 199, 178), width=1)
draw.text((panel[0] + 32, panel[1] + 30), "Quiet but memorable.", font=f_serif_36, fill=cream)
panel_text = "适合个人介绍、深度内容、旅行记录、独立创作者主页。重点是气质稳定、阅读舒服、不过度装饰。"
draw_multiline(draw, (panel[0] + 34, panel[1] + 88), panel_text, f_sans_20, (226, 219, 203), panel[2] - panel[0] - 72, 10)

# Footer meta.
draw.text((72, H - 44), "Selected visual direction", font=f_latin_18, fill=muted)
draw.rectangle((W // 2 - 18, H - 54, W // 2 + 18, H - 18), outline=line, width=1)
draw.text((W // 2 - 5, H - 49), "L", font=f_latin_18, fill=clay)
draw.text((W - 325, H - 44), "Minimal editorial website", font=f_latin_18, fill=muted)

out = "/Users/g90/Documents/Codex/2026-06-13/hermes/outputs/personal_intro_site_style_preview.png"
img.save(out)
print(out)
