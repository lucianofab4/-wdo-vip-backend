import json
from loguru import logger


def parse_crash_message(raw: str | bytes) -> dict | None:
    """
    Parseia resultado do Crash.
    Retorna dict com {table_id, multiplier, crashed_at, status} ou None.
    """
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")

        data = json.loads(raw)
        return _extract_crash(data)

    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    except Exception as e:
        logger.debug(f"[Crash] Erro ao parsear: {e}")

    return None


def _extract_crash(data) -> dict | None:
    if isinstance(data, list):
        for item in data:
            r = _extract_crash(item)
            if r:
                return r

    if not isinstance(data, dict):
        return None

    event_type = str(data.get("type") or data.get("event") or "").lower()

    # Só processa eventos de crash (fim de rodada)
    if not any(k in event_type for k in ("crash", "result", "end", "bust", "finish")):
        # Tenta procurar em sub-objetos
        for key in ("data", "payload", "result"):
            if key in data:
                r = _extract_crash(data[key])
                if r:
                    return r
        return None

    inner = data.get("data") or data.get("payload") or data

    multiplier = (
        inner.get("multiplier")
        or inner.get("crashPoint")
        or inner.get("crash_point")
        or inner.get("point")
        or inner.get("value")
        or inner.get("result")
    )

    if multiplier is None:
        return None

    try:
        multiplier = float(str(multiplier).replace("x", "").replace(",", "."))
    except (ValueError, TypeError):
        return None

    if multiplier < 1.0:
        return None

    table_id = (
        inner.get("tableId") or inner.get("table_id")
        or data.get("tableId") or data.get("gameId") or "default"
    )

    return {
        "table_id": str(table_id),
        "multiplier": multiplier,
        "round_id": inner.get("roundId") or inner.get("round_id") or inner.get("gameId"),
        "raw": data,
    }
