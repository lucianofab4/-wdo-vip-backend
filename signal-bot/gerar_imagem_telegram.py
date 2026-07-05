from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1080
img = Image.new("RGB", (W, H), "#e5ddd5")  # fundo bege Telegram
draw = ImageDraw.Draw(img)

font_bold   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
font_medium = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
font_small  = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   26)
font_xs     = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   22)
font_emoji  = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 28)
font_emoji_sm = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 22)

WHITE  = "#ffffff"
GRAY   = "#667781"
BLACK  = "#111111"
GREEN  = "#25d366"
DARK_G = "#128c7e"
WIN_G  = "#dcf8c6"   # bolha verde (mensagens enviadas / bot)
TIME   = "#8696a0"

# ── Fundo com padrão sutil (wallpaper Telegram) ───────────────────────────────
for y in range(H):
    t = y / H
    r = int(229 - 10*t)
    g = int(221 - 8*t)
    b = int(213 - 5*t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# ── Header do chat ────────────────────────────────────────────────────────────
draw.rectangle([0, 0, W, 100], fill="#128c7e")
# Avatar
draw.ellipse([18, 14, 78, 74], fill="#25d366")
draw.text((48, 44), "20K", font=font_bold, fill=WHITE, anchor="mm")
# Nome e status
draw.text((100, 28), "20k_bot", font=font_bold, fill=WHITE, anchor="lm")
draw.text((100, 64), "bot", font=font_xs, fill="#b2dfdb", anchor="lm")

# ── Função para desenhar bolha de mensagem ────────────────────────────────────
def msg_bubble(y, lines, time_str, is_win=False, is_entrada=False):
    pad_x, pad_y = 18, 14
    line_h = 38
    max_line_w = 680

    bh = pad_y * 2 + len(lines) * line_h + 10
    bw = max_line_w

    x1 = 60
    x2 = x1 + bw

    bg = WIN_G if is_win else WHITE
    # Sombra leve
    draw.rounded_rectangle([x1+2, y+2, x2+2, y+bh+2], radius=12, fill="#d0d0d0")
    draw.rounded_rectangle([x1, y, x2, y+bh], radius=12, fill=bg)

    # Triângulo (cauda da bolha)
    draw.polygon([(x1, y+16), (x1-12, y+8), (x1, y+28)], fill=bg)

    for i, (txt, color, use_emoji) in enumerate(lines):
        ty = y + pad_y + i * line_h + line_h // 2
        fn = font_emoji if use_emoji else font_medium
        draw.text((x1 + pad_x, ty), txt, font=fn, fill=color, anchor="lm")

    # Horário
    draw.text((x2 - 12, y + bh - 10), time_str, font=font_emoji_sm, fill=TIME, anchor="rm")

    return y + bh + 14

# ── Mensagens ─────────────────────────────────────────────────────────────────
y = 118

# Mensagem 1 — ENTRADA
y = msg_bubble(y, [
    ("🎮 ENTRADA CONFIRMADA",        "#c0392b", True),
    ("",                             BLACK,     False),
    ("🎮 Jogo: BACBO",               BLACK,     True),
    ("Entrar: AZUL (Player)",        BLACK,     False),
    ("📊 Estratégia: streak",        BLACK,     True),
    ("",                             BLACK,     False),
    ("⏳ Próxima rodada",            GRAY,      True),
], time_str="08:41", is_entrada=True)

# Mensagem 2 — WIN
y = msg_bubble(y, [
    ("✅ WIN!",                          "#128c7e", True),
    ("Entrada: AZUL (Player)",           BLACK,     False),
], time_str="08:41", is_win=True)

# Mensagem 3 — ENTRADA
y = msg_bubble(y, [
    ("🎮 ENTRADA CONFIRMADA",        "#c0392b", True),
    ("",                             BLACK,     False),
    ("🎮 Jogo: BACBO",               BLACK,     True),
    ("Entrar: VERMELHO (Banker)",    BLACK,     False),
    ("📊 Estratégia: streak",        BLACK,     True),
    ("",                             BLACK,     False),
    ("⏳ Próxima rodada",            GRAY,      True),
], time_str="08:43", is_entrada=True)

# Mensagem 4 — WIN
y = msg_bubble(y, [
    ("✅ WIN!",                             "#128c7e", True),
    ("Entrada: VERMELHO (Banker)",          BLACK,     False),
], time_str="08:43", is_win=True)

# Mensagem 5 — ENTRADA
y = msg_bubble(y, [
    ("🎮 ENTRADA CONFIRMADA",        "#c0392b", True),
    ("",                             BLACK,     False),
    ("🎮 Jogo: BACBO",               BLACK,     True),
    ("Entrar: AZUL (Player)",        BLACK,     False),
    ("📊 Estratégia: streak",        BLACK,     True),
    ("",                             BLACK,     False),
    ("⏳ Próxima rodada",            GRAY,      True),
], time_str="08:47", is_entrada=True)

# Mensagem 6 — WIN
y = msg_bubble(y, [
    ("✅ WIN!",                          "#128c7e", True),
    ("Entrada: AZUL (Player)",           BLACK,     False),
], time_str="08:47", is_win=True)

# ── CTA no rodapé ─────────────────────────────────────────────────────────────
draw.rectangle([0, H-110, W, H], fill="#128c7e")
draw.text((W//2, H-68), "Receba sinais assim no seu Telegram", font=font_medium, fill="#b2dfdb", anchor="mm")
draw.text((W//2, H-28), "Acesse agora: @20k_bot", font=font_bold, fill=WHITE, anchor="mm")

out = "C:/Users/Game-PC/signal-bot/ad_image_telegram.png"
img.save(out, "PNG")
print(f"Salvo: {out}")
