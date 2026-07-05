from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1080, 1080

img = Image.new("RGB", (W, H), "#080e1a")
draw = ImageDraw.Draw(img)

# ── Gradiente de fundo radial simulado ──────────────────────────────────────
for i in range(300):
    alpha = int(60 * (1 - i / 300))
    r = int(alpha * 16 / 60)
    g = int(alpha * 185 / 60)
    b = int(alpha * 129 / 60)
    draw.ellipse(
        [W//2 - (300-i), H//2 - 200 - (300-i),
         W//2 + (300-i), H//2 - 200 + (300-i)],
        outline=(r, g, b)
    )

# ── Fontes ───────────────────────────────────────────────────────────────────
font_black  = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf",  90)
font_bold   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 52)
font_medium = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 38)
font_small  = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   30)

GREEN  = "#10b981"
GOLD   = "#f59e0b"
WHITE  = "#ffffff"
GRAY   = "#9ca3af"
DARK   = "#111827"
RED    = "#ef4444"

# ── Badge "AO VIVO" ──────────────────────────────────────────────────────────
badge_x, badge_y = W//2, 95
badge_w, badge_h = 320, 48
draw.rounded_rectangle(
    [badge_x - badge_w//2, badge_y - badge_h//2,
     badge_x + badge_w//2, badge_y + badge_h//2],
    radius=24, fill="#0d2e20", outline="#10b981", width=2
)
draw.ellipse([badge_x - 130, badge_y - 7, badge_x - 116, badge_y + 7], fill=GREEN)
draw.text((badge_x - 105, badge_y), "SISTEMA ATIVO — AO VIVO", font=font_small, fill=GREEN, anchor="lm")

# ── Título principal ─────────────────────────────────────────────────────────
draw.text((W//2, 205), "O Robô que", font=font_black, fill=WHITE, anchor="mm")
draw.text((W//2, 305), "Lê o Jogo", font=font_black, fill=GOLD, anchor="mm")

# ── Subtítulo ────────────────────────────────────────────────────────────────
draw.text((W//2, 390), "Sinal exato no seu Telegram.", font=font_bold, fill=WHITE, anchor="mm")
draw.text((W//2, 440), "Você só aposta quando o robô manda.", font=font_bold, fill=WHITE, anchor="mm")

# ── Mockup de notificação Telegram ───────────────────────────────────────────
notif_y = 510
draw.rounded_rectangle([100, notif_y, 980, notif_y + 200], radius=20, fill="#1c2b1e", outline="#10b981", width=2)

# Ícone do bot (círculo verde)
draw.ellipse([130, notif_y + 25, 190, notif_y + 85], fill=GREEN)
draw.text((160, notif_y + 55), "🤖", font=font_small, fill=WHITE, anchor="mm")

# Texto da notificação
draw.text((210, notif_y + 32), "Signal Bot @20k_bot", font=font_small, fill=GREEN, anchor="lm")
draw.text((210, notif_y + 75), "🟢  SINAL IDENTIFICADO", font=font_medium, fill=WHITE, anchor="lm")
draw.text((210, notif_y + 120), "🎯  Entrada: BAC BO — BANKER", font=font_medium, fill=GOLD, anchor="lm")
draw.text((210, notif_y + 160), "⚡  Confiança: 91% · Gale máx: 2", font=font_small, fill=GRAY, anchor="lm")

# ── Stats 3 colunas ──────────────────────────────────────────────────────────
stats = [("87%", "Assertividade", GREEN), ("24/7", "Monitoramento", GOLD), ("+500", "Sinais/mês", "#60a5fa")]
cols = [200, 540, 880]
sy = 760

for (val, label, color), cx in zip(stats, cols):
    draw.rounded_rectangle([cx-150, sy, cx+150, sy+140], radius=16, fill=DARK, outline="#374151", width=1)
    draw.text((cx, sy + 52), val,   font=font_black,  fill=color, anchor="mm")
    draw.text((cx, sy + 110), label, font=font_small, fill=GRAY,  anchor="mm")

# ── CTA ──────────────────────────────────────────────────────────────────────
cta_y = 945
draw.rounded_rectangle([180, cta_y, 900, cta_y + 90], radius=16, fill=GREEN)
draw.text((W//2, cta_y + 45), "QUERO RECEBER OS SINAIS →", font=font_bold, fill=WHITE, anchor="mm")

# ── Salvar ───────────────────────────────────────────────────────────────────
out = "C:/Users/Game-PC/signal-bot/ad_image.png"
img.save(out, "PNG")
print(f"Imagem salva: {out}")
print(f"Dimensões: {W}x{H}px")
