from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Amsterdam")


def prices(coordinator) -> list:
    return (coordinator.data or {}).get("prices", [])


def day_by_offset(coordinator, offset_days: int) -> dict | None:
    target = (datetime.now(TZ).date() + timedelta(days=offset_days)).isoformat()
    for day in prices(coordinator):
        if day.get("date") == target:
            return day
    return None


def today(coordinator) -> dict | None:
    return day_by_offset(coordinator, 0)


def tomorrow(coordinator) -> dict | None:
    return day_by_offset(coordinator, 1)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=TZ)


def electricity_tariffs(day: dict | None) -> list:
    return (day or {}).get("electricity", {}).get("tariffs", [])


def gas_tariffs(day: dict | None) -> list:
    return (day or {}).get("gas", {}).get("tariffs", [])


def all_electricity_tariffs(coordinator) -> list:
    rows = []
    for day in prices(coordinator):
        rows.extend(electricity_tariffs(day))
    return rows


def current_electricity_tariff(coordinator) -> dict | None:
    now = datetime.now(TZ)
    for tariff in all_electricity_tariffs(coordinator):
        start = parse_dt(tariff.get("startDateTime"))
        end = parse_dt(tariff.get("endDateTime"))
        if start and end and start <= now < end:
            return tariff
    return None


def next_electricity_tariff(coordinator) -> dict | None:
    now = datetime.now(TZ)
    future = []
    for tariff in all_electricity_tariffs(coordinator):
        start = parse_dt(tariff.get("startDateTime"))
        if start and start > now:
            future.append((start, tariff))
    return sorted(future, key=lambda item: item[0])[0][1] if future else None


def current_gas_tariff(coordinator) -> dict | None:
    day = today(coordinator)
    now = datetime.now(TZ)

    for tariff in gas_tariffs(day):
        start = parse_dt(tariff.get("startDateTime"))
        end = parse_dt(tariff.get("endDateTime"))
        if start and end and start <= now < end:
            return tariff

    tariffs = gas_tariffs(day)
    return tariffs[0] if tariffs else None


def group_amount(tariff: dict | None, group_type: str):
    for group in (tariff or {}).get("groups", []):
        if group.get("type") == group_type:
            return group.get("amount")
    return None


def cheapest_tariff(day: dict | None) -> dict | None:
    tariffs = electricity_tariffs(day)
    return min(tariffs, key=lambda t: t.get("totalAmount", 999)) if tariffs else None


def most_expensive_tariff(day: dict | None) -> dict | None:
    tariffs = electricity_tariffs(day)
    return max(tariffs, key=lambda t: t.get("totalAmount", -999)) if tariffs else None


def hour_label(tariff: dict | None) -> str | None:
    start = parse_dt((tariff or {}).get("startDateTime"))
    return start.strftime("%H:%M") if start else None


def hour_prices(day: dict | None) -> list:
    rows = []
    for tariff in electricity_tariffs(day):
        start = parse_dt(tariff.get("startDateTime"))
        rows.append({
            "time": start.strftime("%H:%M") if start else None,
            "start": tariff.get("startDateTime"),
            "end": tariff.get("endDateTime"),
            "price": tariff.get("totalAmount"),
            "price_ex_vat": tariff.get("totalAmountEx"),
            "vat": tariff.get("totalAmountVat"),
            "market_price": group_amount(tariff, "MARKET_PRICE"),
            "energy_tax": group_amount(tariff, "TAX"),
            "purchasing_fee": group_amount(tariff, "PURCHASING_FEE"),
        })
    return rows


def _blocks(rows: list, predicate):
    blocks = []
    current = []
    for row in rows:
        if predicate(row):
            current.append(row)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _block_info(block: list) -> dict | None:
    if not block:
        return None
    values = [row.get("price") for row in block if row.get("price") is not None]
    end = block[-1].get("end")
    if isinstance(end, str) and "T" in end:
        end = end.split("T")[1][:5]
    return {
        "start": block[0].get("time"),
        "end": end,
        "hours": len(block),
        "average": round(sum(values) / len(values), 5) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def _best_block(day: dict | None, predicate, mode: str) -> dict | None:
    rows = hour_prices(day)
    infos = [_block_info(block) for block in _blocks(rows, predicate)]
    infos = [info for info in infos if info and info.get("average") is not None]
    if not infos:
        return None
    if mode == "expensive":
        return max(infos, key=lambda item: (item["hours"], item["average"]))
    return min(infos, key=lambda item: (item["average"], -item["hours"]))


def summary(day: dict | None) -> dict:
    electricity = (day or {}).get("electricity", {})
    rows = hour_prices(day)
    values = [row.get("price") for row in rows if row.get("price") is not None]

    avg = electricity.get("averageAmount")
    mn = electricity.get("minAmount")
    mx = electricity.get("maxAmount")
    cheapest = cheapest_tariff(day)
    expensive = most_expensive_tariff(day)

    below = [row for row in rows if avg is not None and row.get("price") is not None and row.get("price") < avg]
    above = [row for row in rows if avg is not None and row.get("price") is not None and row.get("price") > avg]
    negative_market = [row for row in rows if row.get("market_price") is not None and row.get("market_price") < 0]
    negative_total = [row for row in rows if row.get("price") is not None and row.get("price") < 0]

    volatility = None
    if values:
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        volatility = round(variance ** 0.5, 5)

    return {
        "date": (day or {}).get("date"),
        "min": mn,
        "max": mx,
        "average": avg,
        "spread": round(mx - mn, 5) if mn is not None and mx is not None else None,
        "cheapest_hour": hour_label(cheapest),
        "cheapest_price": (cheapest or {}).get("totalAmount"),
        "most_expensive_hour": hour_label(expensive),
        "most_expensive_price": (expensive or {}).get("totalAmount"),
        "hours_below_average": len(below),
        "hours_above_average": len(above),
        "negative_market_hours": len(negative_market),
        "negative_total_hours": len(negative_total),
        "first_below_average_hour": below[0].get("time") if below else None,
        "last_below_average_hour": below[-1].get("time") if below else None,
        "cheapest_block_below_average": _best_block(day, lambda row: avg is not None and row.get("price") is not None and row.get("price") < avg, "cheapest"),
        "most_expensive_block_above_average": _best_block(day, lambda row: avg is not None and row.get("price") is not None and row.get("price") > avg, "expensive"),
        "volatility": volatility,
    }
