"""Descobre seu chat_id no Telegram."""
import sys, asyncio, httpx
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOKEN = "8817817097:AAGIOtF61oGCSXfIfnwdH1haA3OdFQGYvD4"

async def main():
    print("Buscando seu chat_id...")
    timeout = httpx.Timeout(connect=30.0, read=30.0, write=30.0, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates")
        data = r.json()

    results = data.get("result", [])
    if not results:
        print("Nenhuma mensagem encontrada.")
        print("-> Mande /start para @Quantico20k_bot no Telegram e rode este script novamente.")
        return

    for update in reversed(results):
        msg = update.get("message") or update.get("edited_message")
        if msg and "chat" in msg:
            chat_id = msg["chat"]["id"]
            name = msg["chat"].get("first_name", "")
            print(f"\nChat ID encontrado: {chat_id}  ({name})")
            print(f"\nCopie esse numero e cole no proximo passo.")
            return

    print("Nenhum chat com mensagem encontrado.")

asyncio.run(main())
