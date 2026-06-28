from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Amsterdam")


def prices(coordinator):
    return (coordinator.data or {}).get("prices", [])


def day_by_offset(coordinator, offset_days: int):
    target = (datetime.now(TZ).date() + timedelta(days=offset_days)).isoformat()
    for day in prices(coordinator):
        if day.get("date") == target:
            return day
    return None


def today(coordinator):
    return day_by_offset(coordinator, 0)


def tomorrow(coordinator):
    return day_by_offset(coordinator, 1)


def parse_dt(value):
    if not value:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=TZ)


def electricity_tariffs(day):
    return (day or {}).get("electricity", {}).get("tariffs", [])


def gas_tariffs(day):
    return (day or {}).get("gas", {}).get("tariffs", [])


def all_electricity_tariffs(coordinator):
    rows = []
    for day in prices(coordinator):
        rows.extend(electricity_tariffs(day))
    return rows


def current_electricity_tariff(coordinator):
    now = datetime.now(TZ)
    for tariff in all_electricity_tariffs(coordinator):
        start = parse_dt(tariff.get("startDateTime"))
        end = parse_dt(tariff.get("endDateTime"))
        if start and end and start <= now < end:
            return tariff
    return None


def next_electricity_tariff(coordinator):
    now = datetime.now(TZ)
    future = []
    for tariff in all_electricity_tariffs(coordinator):
        start = parse_dt(tariff.get("startDateTime"))
        if start and start > now:
            future.append((start, tariff))
    if not future:
        return None
    return sorted(future, key=lambda x: x[0])[0][1]


def current_gas_tariff(coordinator):
    day = today(coordinator)
    now = datetime.now(TZ)
    for tariff in gas_tariffs(day):
        start = parse_dt(tariff.get("startDateTime"))
        end = parse_dt(tariff.get("endDateTime"))
        if start and end and start <= now < end:
            return tariff
    tariffs = gas_tariffs(day)
    return tariffs[0] if tariffs else None


def cheapest_tariff(day):
    tariffs = electricity_tariffs(day)
    return min(tariffs, key=lambda t: t.get("totalAmount", 999)) if tariffs else None


def most_expensive_tariff(day):
    tariffs = electricity_tariffs(day)
    return max(tariffs, key=lambda t: t.get("totalAmount", -999)) if tariffs else None


def hour_label(tariff):
    start = parse_dt((tariff or {}).get("startDateTime"))
    return start.strftime("%H:%M") if start else None


def group_amount(tariff, group_type):
    for group in (tariff or {}).get("groups", []):
        if group.get("type") == group_type:
            return group.get("amount")
    return None


def hour_prices(day):
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
            "tax": group_amount(tariff, "TAX"),
            "purchasing_fee": group_amount(tariff, "PURCHASING_FEE"),
        })
    return rows


def _blocks(rows, predicate):
    blocks = []
    current = []

    for row in rows:
        if predicate(row):
            current.append(row)
        else:
            if current:
                blocks.append(current)
                current = []

    if current:
        blocks.append(current)

    return blocks


def _block_info(block):
    if not block:
        return None

    prices = [row.get("price") for row in block if row.get("price") is not None]
    return {
        "start": block[0].get("time"),
        "end": block[-1].get("end"),
        "hours": len(block),
        "average": round(sum(prices) / len(prices), 5) if prices else None,
        "min": min(prices) if prices else None,
        "max": max(prices) if prices else None,
    }


def _best_block(day, predicate, mode="cheapest"):
    rows = hour_prices(day)
    blocks = _blocks(rows, predicate)
    infos = [_block_info(block) for block in blocks if block]
    infos = [info for info in infos if info and info.get("average") is not None]

    if not infos:
        return None

    if mode == "expensive":
        return max(infos, key=lambda item: (item["hours"], item["average"]))
    return min(infos, key=lambda item: (item["average"], -item["hours"]))


def summary(day):
    electricity = (day or {}).get("electricity", {})
    rows = hour_prices(day)
    prices_only = [row.get("price") for row in rows if row.get("price") is not None]
    avg = electricity.get("averageAmount")
    mn = electricity.get("minAmount")
    mx = electricity.get("maxAmount")
    cheapest = cheapest_tariff(day)
    expensive = most_expensive_tariff(day)

    below_average = [row for row in rows if avg is not None and row.get("price") is not None and row.get("price") < avg]
    above_average = [row for row in rows if avg is not None and row.get("price") is not None and row.get("price") > avg]
    negative_market = [row for row in rows if row.get("market_price") is not None and row.get("market_price") < 0]
    negative_total = [row for row in rows if row.get("price") is not None and row.get("price") < 0]

    cheap_block = _best_block(day, lambda row: avg is not None and row.get("price") is not None and row.get("price") < avg, "cheapest")
    expensive_block = _best_block(day, lambda row: avg is not None and row.get("price") is not None and row.get("price") > avg, "expensive")

    volatility = None
    if prices_only:
        mean = sum(prices_only) / len(prices_only)
        variance = sum((p - mean) ** 2 for p in prices_only) / len(prices_only)
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

        "hours_below_average": len(below_average),
        "hours_above_average": len(above_average),
        "negative_market_hours": len(negative_market),
        "negative_total_hours": len(negative_total),

        "first_below_average_hour": below_average[0].get("time") if below_average else None,
        "last_below_average_hour": below_average[-1].get("time") if below_average else None,

        "cheapest_block_below_average": cheap_block,
        "most_expensive_block_above_average": expensive_block,
        "volatility": volatility,
    }
