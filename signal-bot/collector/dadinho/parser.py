import json
from loguru import logger


def parse_dadinho_message(raw: str | bytes) -> dict | None:
    """
    Parseia resultado do Dadinho (Dice).
    Retorna dict com {table_id, die1, die2, total, result_type} ou None.
    """
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")

        data = json.loads(raw)
        return _extract_dice(data)

    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    except Exception as e:
        logger.debug(f"[Dadinho] Erro ao parsear: {e}")

    return None


def _extract_dice(data) -> dict | None:
    if isinstance(data, list):
        for item in data:
            r = _extract_dice(item)
            if r:
                return r

    if not isinstance(data, dict):
        return None

    # Tenta identificar evento de resultado de dice
    event_type = data.get("type") or data.get("event") or ""
    is_result = any(k in str(event_type).lower() for k in ("result", "round", "outcome", "dice"))

    inner = data.get("data") or data.get("payload") or data

    die1 = (
        inner.get("dice1") or inner.get("die1") or inner.get("d1")
        or inner.get("player") or inner.get("result1")
    )
    die2 = (
        inner.get("dice2") or inner.get("die2") or inner.get("d2")
        or inner.get("banker") or inner.get("result2")
    )

    if die1 is None or die2 is None:
        # Tenta lista de dados
        dice_list = inner.get("dice") or inner.get("results")
        if isinstance(dice_list, list) and len(dice_list) >= 2:
            die1, die2 = dice_list[0], dice_list[1]

    if die1 is None or die2 is None:
        return None

    try:
        die1, die2 = int(die1), int(die2)
    except (ValueError, TypeError):
        return None

    if not (1 <= die1 <= 6 and 1 <= die2 <= 6):
        return None

    total = die1 + die2
    result_type = "HIGH" if total > 7 else ("LOW" if total < 7 else "EQUAL")

    table_id = (
        inner.get("tableId") or inner.get("table_id")
        or data.get("tableId") or "default"
    )

    return {
        "table_id": str(table_id),
        "die1": die1,
        "die2": die2,
        "total": total,
        "result_type": result_type,
        "is_double": die1 == die2,
        "round_id": inner.get("roundId") or inner.get("round_id"),
        "raw": data,
    }
