import json
from loguru import logger

# Mapeamento de resultados do Bac Bo
# Ajuste conforme o formato real do seu cassino
RESULT_MAP = {
    "player": "PLAYER",
    "banker": "BANKER",
    "tie": "TIE",
    "p": "PLAYER",
    "b": "BANKER",
    "t": "TIE",
    # valores numéricos comuns em algumas plataformas
    "1": "PLAYER",
    "2": "BANKER",
    "0": "TIE",
}


def parse_bacbo_message(raw: str | bytes) -> dict | None:
    """
    Tenta extrair um resultado de Bac Bo de uma mensagem WebSocket.
    Retorna dict com {table_id, result, player_dice, banker_dice, raw} ou None.
    """
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")

        data = json.loads(raw)

        # Tenta diferentes estruturas de payload
        result_data = _extract_from_payload(data)
        if result_data:
            return result_data

    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    except Exception as e:
        logger.debug(f"[BacBo] Erro ao parsear mensagem: {e}")

    return None


def _extract_from_payload(data: dict) -> dict | None:
    """Tenta múltiplos formatos de payload."""

    # Formato 1: {type: "result", data: {outcome: "player", ...}}
    if isinstance(data, dict) and data.get("type") in ("result", "game_result", "round_result"):
        inner = data.get("data", data)
        return _build_result(inner, data)

    # Formato 2: {event: "result", payload: {...}}
    if isinstance(data, dict) and data.get("event") in ("result", "game_result"):
        inner = data.get("payload", data)
        return _build_result(inner, data)

    # Formato 3: array de eventos
    if isinstance(data, list):
        for item in data:
            result = _extract_from_payload(item)
            if result:
                return result

    # Formato 4: nested em "results" ou "games"
    for key in ("results", "game", "round", "outcome"):
        if isinstance(data, dict) and key in data:
            nested = data[key]
            if isinstance(nested, dict):
                result = _build_result(nested, data)
                if result:
                    return result

    return None


def _build_result(inner: dict, raw: dict) -> dict | None:
    """Constrói o resultado normalizado."""
    # Campos comuns para o resultado
    outcome = (
        inner.get("outcome")
        or inner.get("result")
        or inner.get("winner")
        or inner.get("side")
        or inner.get("win")
        or ""
    )

    if not outcome:
        return None

    outcome_str = str(outcome).lower().strip()
    normalized = RESULT_MAP.get(outcome_str)
    if not normalized:
        return None

    table_id = (
        inner.get("tableId")
        or inner.get("table_id")
        or inner.get("roomId")
        or raw.get("tableId")
        or "default"
    )

    return {
        "table_id": str(table_id),
        "result": normalized,
        "player_dice": inner.get("playerDice") or inner.get("player_dice"),
        "banker_dice": inner.get("bankerDice") or inner.get("banker_dice"),
        "round_id": inner.get("roundId") or inner.get("round_id"),
        "raw": raw,
    }
