from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1080, 1080
img = Image.new("RGB", (W, H), "#0a0f0a")
draw = ImageDraw.Draw(img)

# ── Fontes ───────────────────────────────────────────────────────────────────
font_black  = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf",  80)
font_bold   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 48)
font_medium = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
font_small  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
font_xs     = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   22)

GREEN  = "#10b981"
GOLD   = "#f59e0b"
WHITE  = "#ffffff"
GRAY   = "#9ca3af"
RED    = "#ef4444"
DARK   = "#111827"
TABLE  = "#0d2b0d"
TABLE2 = "#0a220a"

# ── Mesa de cassino (fundo) ───────────────────────────────────────────────────
# Feltro verde escuro
draw.rounded_rectangle([40, 40, W-40, H-40], radius=40, fill="#0d2b0d", outline="#1a5c1a", width=4)

# Linha divisória central vertical
draw.line([W//2, 100, W//2, 650], fill="#1a5c1a", width=3)

# Linha divisória horizontal
draw.line([80, 310, W-80, 310], fill="#1a5c1a", width=2)

# ── Labels PLAYER / BANKER ───────────────────────────────────────────────────
# PLAYER (esquerda)
draw.rounded_rectangle([80, 60, 490, 115], radius=10, fill="#0a1f0a")
draw.text((285, 88), "PLAYER", font=font_bold, fill="#4ade80", anchor="mm")

# BANKER (direita) - destaque vencedor
draw.rounded_rectangle([590, 60, W-80, 115], radius=10, fill="#1a4a1a", outline=GREEN, width=2)
draw.text((795, 88), "BANKER  ✓", font=font_bold, fill=GREEN, anchor="mm")

# ── Função para desenhar dado ─────────────────────────────────────────────────
def draw_die(cx, cy, value, size=95, winner=False, color="#1a3a1a"):
    border = GREEN if winner else "#2d5a2d"
    bw = 3 if winner else 1
    # Sombra
    draw.rounded_rectangle([cx - size//2 + 4, cy - size//2 + 4,
                             cx + size//2 + 4, cy + size//2 + 4],
                            radius=16, fill="#000000")
    # Corpo do dado
    draw.rounded_rectangle([cx - size//2, cy - size//2,
                             cx + size//2, cy + size//2],
                            radius=16, fill=color, outline=border, width=bw)

    pip_color = WHITE if winner else "#9ca3af"
    pip_r = 7
    pips = {
        1: [(0, 0)],
        2: [(-28, -28), (28, 28)],
        3: [(-28, -28), (0, 0), (28, 28)],
        4: [(-28, -28), (28, -28), (-28, 28), (28, 28)],
        5: [(-28, -28), (28, -28), (0, 0), (-28, 28), (28, 28)],
        6: [(-28, -20), (28, -20), (-28, 0), (28, 0), (-28, 20), (28, 20)],
    }
    for (dx, dy) in pips.get(value, []):
        px, py = cx + dx, cy + dy
        draw.ellipse([px - pip_r, py - pip_r, px + pip_r, py + pip_r], fill=pip_color)

# ── Dados PLAYER (perdedor) ───────────────────────────────────────────────────
# Round 1: 3 + 2 = 5
draw_die(180, 220, 3, winner=False)
draw_die(370, 220, 2, winner=False)
draw.text((285, 285), "= 5", font=font_medium, fill="#6b7280", anchor="mm")

# ── Dados BANKER (vencedor) ───────────────────────────────────────────────────
# Round 1: 4 + 4 = 8
draw_die(710, 220, 4, winner=True, color="#1a4a1a")
draw_die(900, 220, 4, winner=True, color="#1a4a1a")
draw.text((805, 285), "= 8", font=font_medium, fill=GREEN, anchor="mm")

# ── Histórico de resultados ───────────────────────────────────────────────────
draw.text((W//2, 340), "HISTÓRICO", font=font_small, fill="#4ade80", anchor="mm")

results = [
    ("B", GREEN), ("B", GREEN), ("P", "#6b7280"), ("B", GREEN),
    ("P", "#6b7280"), ("B", GREEN), ("P", "#6b7280"), ("B", GREEN),
    ("B", GREEN), ("P", "#6b7280"), ("B", GREEN), ("B", GREEN),
]

rx_start = 120
ry = 385
for i, (label, color) in enumerate(results):
    rx = rx_start + i * 73
    draw.ellipse([rx, ry, rx+52, ry+52], fill=color if color==GREEN else "#1c2b1c", outline=color, width=2)
    draw.text((rx+26, ry+26), label, font=font_medium, fill=WHITE if color==GREEN else "#6b7280", anchor="mm")

# ── Painel de sinal ───────────────────────────────────────────────────────────
signal_y = 490
draw.rounded_rectangle([80, signal_y, W-80, signal_y + 220],
                        radius=20, fill="#071a07", outline=GREEN, width=3)

# Pulso verde (badge)
draw.ellipse([108, signal_y + 18, 126, signal_y + 36], fill=GREEN)
draw.text((140, signal_y + 27), "SINAL IDENTIFICADO AGORA", font=font_small, fill=GREEN, anchor="lm")

draw.text((W//2, signal_y + 90), "🎯  Aposte em BANKER", font=font_bold, fill=WHITE, anchor="mm")
draw.text((W//2, signal_y + 145), "Confiança: 91%  •  Gale: até 2x", font=font_medium, fill=GRAY, anchor="mm")
draw.text((W//2, signal_y + 193), "Receba via Telegram  →  @20k_bot", font=font_small, fill=GREEN, anchor="mm")

# ── Stats ─────────────────────────────────────────────────────────────────────
stats = [("87%", "Assertividade", GREEN), ("24/7", "Monitoramento", GOLD), ("+500", "Sinais/mês", "#60a5fa")]
sy = 760
cols = [200, 540, 880]
for (val, label, color), cx in zip(stats, cols):
    draw.rounded_rectangle([cx-145, sy, cx+145, sy+130], radius=16, fill="#071a07", outline="#1a4a1a", width=1)
    draw.text((cx, sy + 48), val,   font=font_black,  fill=color, anchor="mm")
    draw.text((cx, sy + 102), label, font=font_small, fill=GRAY,  anchor="mm")

# ── CTA ───────────────────────────────────────────────────────────────────────
cta_y = 940
for i in range(4):
    draw.rounded_rectangle([160+i, cta_y+i, W-160+i, cta_y+82+i], radius=14, fill="#065f46")
draw.rounded_rectangle([160, cta_y, W-160, cta_y+82], radius=14, fill=GREEN)
draw.text((W//2, cta_y+41), "QUERO RECEBER OS SINAIS →", font=font_bold, fill=WHITE, anchor="mm")

# ── Logo/watermark ────────────────────────────────────────────────────────────
draw.text((W//2, 1045), "@20k_bot  •  Sistema de Sinais Bac Bo", font=font_xs, fill="#374151", anchor="mm")

out = "C:/Users/Game-PC/signal-bot/ad_image_jogo.png"
img.save(out, "PNG")
print(f"Salvo: {out}")
