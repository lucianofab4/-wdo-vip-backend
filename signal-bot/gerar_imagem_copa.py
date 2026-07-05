from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1080
img = Image.new("RGB", (W, H), "#050a05")
draw = ImageDraw.Draw(img)

font_black  = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf",  88)
font_bold72 = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf",  72)
font_bold   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 46)
font_medium = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
font_small  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
font_xs     = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   22)
font_emoji  = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 44)
font_emoji_sm = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 28)

GREEN  = "#16a34a"
GOLD   = "#f59e0b"
WHITE  = "#ffffff"
GRAY   = "#9ca3af"
DARK   = "#0a1f0a"
RED    = "#dc2626"

# ── Gradiente de fundo ────────────────────────────────────────────────────────
for y in range(H):
    t = y / H
    r = int(5  + 10*t)
    g = int(10 + 25*t)
    b = int(5  + 5*t)
    draw.line([(0,y),(W,y)], fill=(r,g,b))

# Brilho central
for i in range(200):
    alpha = int(30 * (1 - i/200))
    draw.ellipse([W//2-i*2, 300-i, W//2+i*2, 300+i], outline=(0, alpha, 0))

# ── Header — Copa branding ────────────────────────────────────────────────────
draw.rounded_rectangle([60, 50, W-60, 130], radius=20, fill="#0a2e0a", outline="#16a34a", width=2)
draw.text((W//2, 90), "🏆  COPA DO MUNDO 2026  🏆", font=font_emoji_sm, fill=GOLD, anchor="mm")

# ── Headline principal ────────────────────────────────────────────────────────
draw.text((W//2, 210), "Quem tinha o bot", font=font_bold72, fill=WHITE, anchor="mm")
draw.text((W//2, 300), "na última Copa", font=font_bold72, fill=WHITE, anchor="mm")
draw.text((W//2, 400), "garantiu 89%", font=font_black, fill=GOLD, anchor="mm")
draw.text((W//2, 490), "de acerto.", font=font_black, fill=GOLD, anchor="mm")

# ── Linha divisória ────────────────────────────────────────────────────────────
draw.line([120, 540, W-120, 540], fill="#16a34a", width=2)

# ── Você já perdeu a última ───────────────────────────────────────────────────
draw.text((W//2, 580), "Você já perdeu a última.", font=font_bold, fill=GRAY, anchor="mm")
draw.text((W//2, 635), "Vai ficar de fora dessa também?", font=font_bold, fill=WHITE, anchor="mm")

# ── Countdown visual ──────────────────────────────────────────────────────────
boxes = [("8", "DIAS"), ("11", "JUN"), ("64", "JOGOS"), ("48", "SELEÇÕES")]
bw = 185
gap = 20
total = len(boxes) * bw + (len(boxes)-1) * gap
sx = (W - total) // 2
by = 690

for val, label in boxes:
    draw.rounded_rectangle([sx, by, sx+bw, by+110], radius=14, fill="#0a2e0a", outline="#16a34a", width=1)
    draw.text((sx + bw//2, by + 46), val,   font=font_bold,   fill=GREEN, anchor="mm")
    draw.text((sx + bw//2, by + 84), label, font=font_xs,     fill=GRAY,  anchor="mm")
    sx += bw + gap

# ── Preços ────────────────────────────────────────────────────────────────────
draw.rounded_rectangle([80, 830, W-80, 940], radius=18, fill="#0a2e0a", outline="#f59e0b", width=2)
draw.text((W//2, 865), "Bot Copa: R$59  |  Brasil 6m + Copa: R$80", font=font_medium, fill=WHITE, anchor="mm")
draw.text((W//2, 912), "Brasil Vitalício + Copa: R$99  🎁 Brinde até 11/06", font=font_small, fill=GOLD, anchor="mm")

# ── CTA ───────────────────────────────────────────────────────────────────────
draw.rounded_rectangle([120, 960, W-120, 1048], radius=14, fill=GREEN)
draw.text((W//2, 1004), "GARANTIR ACESSO AGORA →", font=font_bold, fill=WHITE, anchor="mm")

# ── Rodapé ────────────────────────────────────────────────────────────────────
draw.text((W//2, 1068), "@futebolze_sinais_bot  •  Sinais Copa 2026", font=font_xs, fill="#374151", anchor="mm")

out = "C:/Users/Game-PC/signal-bot/ad_image_copa.png"
img.save(out, "PNG")
print(f"Salvo: {out}")
