"""
META MARKETING API — Criador de Campanha
Produto: 20KBACBO - Sinais de Bac Bo
"""

import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ─── CONFIG ───────────────────────────────────────────────────────────────────
ACCESS_TOKEN  = "EAAMWvToQLowBRvnMSC8TPhZAEvxwxNdozyuaQJlswNjH3UVo4PIX3FoU9EhBaPIM2TCjWnFaznUDBh6kumO55kwGHZBlgmTMZBL4DAFDZBticSabIUZCiC6P2FaaZBrGVATDiRiZCGogpEzyjhzN1y6ZARZCOSZAWZA5XNbQDcxutcPiMLZCIggKHtK2MYZBvBTY9BDWjZCgESLwk4GZBbBrFtoHkCZCi5IdA2d3bJLzRofMSILZBw1ZB21QrWFpZAbOhwamNLHGJ9ZCx3R1CMFXe8HZCyUv8wRFw"
AD_ACCOUNT_ID = "act_1504040791178635"
LANDING_URL   = "https://bacbo-bridge.pages.dev"

# Orçamento diário em centavos (R$30 = 3000)
DAILY_BUDGET  = 3000

BASE_URL = "https://graph.facebook.com/v20.0"

# ─── HELPER ───────────────────────────────────────────────────────────────────
def api(method, endpoint, data=None):
    url = f"{BASE_URL}/{endpoint}"
    params = {"access_token": ACCESS_TOKEN}
    if method == "GET":
        resp = requests.get(url, params={**params, **(data or {})})
    else:
        resp = requests.post(url, params=params, json=data)
    result = resp.json()
    if "error" in result:
        print(f"\n❌ Erro na API: {result['error']['message']}")
        print(f"   Código: {result['error'].get('code')}")
        print(f"   Subtipo: {result['error'].get('error_subcode')}")
        print(f"   Detalhes: {result['error'].get('error_user_msg', '')}")
        print(f"   Raw: {json.dumps(result['error'], ensure_ascii=False)}")
        sys.exit(1)
    return result

# ─── STEP 1: Buscar Página do Facebook ────────────────────────────────────────
def get_page():
    print("🔍 Buscando páginas vinculadas à conta...")
    result = api("GET", "me/accounts")
    pages = result.get("data", [])
    if not pages:
        print("❌ Nenhuma Página do Facebook encontrada.")
        print("   Crie uma Página em facebook.com/pages/create e tente novamente.")
        sys.exit(1)
    print(f"   Páginas encontradas:")
    for p in pages:
        print(f"   → {p['name']} (ID: {p['id']})")
    page = pages[0]
    print(f"\n   Usando: {page['name']} (ID: {page['id']})")
    return page["id"]

# ─── STEP 2: Criar Campanha ───────────────────────────────────────────────────
def criar_campanha():
    print("\n📢 Criando campanha...")
    result = api("POST", f"{AD_ACCOUNT_ID}/campaigns", {
        "name": "20KBACBO | Sinais | Brasil",
        "objective": "OUTCOME_TRAFFIC",
        "status": "PAUSED",
        "special_ad_categories": [],
        "is_adset_budget_sharing_enabled": False,
    })
    cid = result["id"]
    print(f"   ✅ Campanha criada: {cid}")
    return cid

# ─── STEP 3: Criar Conjunto de Anúncios ───────────────────────────────────────
def criar_adset(campaign_id):
    print("\n🎯 Criando conjunto de anúncios...")
    result = api("POST", f"{AD_ACCOUNT_ID}/adsets", {
        "name": "Brasil | Homens 22-45 | Sinais Bot",
        "campaign_id": campaign_id,
        "daily_budget": DAILY_BUDGET,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "LINK_CLICKS",
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "targeting": {
            "geo_locations": {
                "countries": ["BR"]
            },
            "age_min": 22,
            "age_max": 45,
            "genders": [1],
            "targeting_automation": {
                "advantage_audience": 0
            },
        },
        "status": "PAUSED",
    })
    aid = result["id"]
    print(f"   ✅ Conjunto criado: {aid}")
    return aid

# ─── STEP 4: Criar Criativo ───────────────────────────────────────────────────
def criar_criativo(page_id):
    print("\n🎨 Criando criativo do anúncio...")
    result = api("POST", f"{AD_ACCOUNT_ID}/adcreatives", {
        "name": "Criativo | Sinais Bot | V1",
        "object_story_spec": {
            "page_id": page_id,
            "link_data": {
                "link": LANDING_URL,
                "message": (
                    "🤖 Esse robô analisa milhares de padrões por segundo "
                    "e te manda o sinal exato de quando entrar.\n\n"
                    "✅ +87% de assertividade comprovada\n"
                    "📲 Sinal direto no seu Telegram\n"
                    "⚡ Acesso imediato após o PIX\n\n"
                    "👇 Clica e vê como funciona"
                ),
                "name": "O Robô que Lê o Jogo Antes de Você",
                "description": "Sistema ativo 24/7 • Cancele quando quiser • Acesso em minutos",
                "call_to_action": {
                    "type": "LEARN_MORE",
                    "value": {"link": LANDING_URL}
                },
            }
        }
    })
    cid = result["id"]
    print(f"   ✅ Criativo criado: {cid}")
    return cid

# ─── STEP 5: Criar Anúncio ────────────────────────────────────────────────────
def criar_anuncio(adset_id, creative_id):
    print("\n📣 Criando anúncio...")
    result = api("POST", f"{AD_ACCOUNT_ID}/ads", {
        "name": "Anúncio | Sinais Bot | V1",
        "adset_id": adset_id,
        "creative": {"creative_id": creative_id},
        "status": "PAUSED",
    })
    aid = result["id"]
    print(f"   ✅ Anúncio criado: {aid}")
    return aid

# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("   META CAMPAIGN CREATOR — 20KBACBO")
    print("=" * 55)

    page_id     = get_page()
    campaign_id = "52601211152077"  # ja criada
    adset_id    = "52601211498077"  # ja criado
    creative_id = criar_criativo(page_id)
    ad_id       = criar_anuncio(adset_id, creative_id)

    print("\n" + "=" * 55)
    print("   ✅ CAMPANHA CRIADA COM SUCESSO!")
    print("=" * 55)
    print(f"   Campaign ID  : {campaign_id}")
    print(f"   AdSet ID     : {adset_id}")
    print(f"   Creative ID  : {creative_id}")
    print(f"   Ad ID        : {ad_id}")
    print()
    print("   ⚠️  Tudo criado como PAUSADO.")
    print("   Acesse o Gerenciador de Anúncios para revisar")
    print("   e ativar quando estiver pronto.")
    print(f"\n   🔗 business.facebook.com/adsmanager")
    print("=" * 55)
