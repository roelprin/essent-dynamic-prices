from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from .data import (
    current_electricity_tariff,
    next_electricity_tariff,
    group_amount,
    hour_prices,
    summary,
    today,
)

TZ = ZoneInfo("Europe/Amsterdam")


def _minutes_until_time(time_label: str | None) -> int | None:
    if not time_label:
        return None

    try:
        hour, minute = [int(part) for part in time_label.split(":")]
    except ValueError:
        return None

    now = datetime.now(TZ)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target < now:
        return 0

    return int((target - now).total_seconds() // 60)


def _rank_current_price(day: dict | None, current_price: float | None) -> int | None:
    if current_price is None:
        return None

    rows = hour_prices(day)
    prices = sorted(row.get("price") for row in rows if row.get("price") is not None)

    for index, price in enumerate(prices, start=1):
        if current_price <= price:
            return index

    return len(prices) if prices else None


def _recommended_devices(score: int, negative_total: bool, negative_market: bool) -> list[str]:
    if negative_total:
        return ["washing_machine", "dishwasher", "dryer", "air_conditioner", "boiler", "ev_charging"]

    if negative_market or score >= 85:
        return ["washing_machine", "dishwasher", "dryer", "air_conditioner"]

    if score >= 70:
        return ["washing_machine", "dishwasher", "air_conditioner"]

    if score >= 55:
        return ["dishwasher"]

    return []


def build_advisor(coordinator) -> dict:
    day = today(coordinator)
    info = summary(day)

    current = current_electricity_tariff(coordinator)
    next_tariff = next_electricity_tariff(coordinator)

    current_price = (current or {}).get("totalAmount")
    next_price = (next_tariff or {}).get("totalAmount")
    market_price = group_amount(current, "MARKET_PRICE")

    avg = info.get("average")
    minimum = info.get("min")
    maximum = info.get("max")
    cheapest_hour = info.get("cheapest_hour")
    cheapest_price = info.get("cheapest_price")
    expensive_hour = info.get("most_expensive_hour")
    cheap_block = info.get("cheapest_block_below_average")

    negative_total = current_price is not None and current_price < 0
    negative_market = market_price is not None and market_price < 0

    score = 50
    reasons = []

    if current_price is None:
        return {
            "advice": "Geen prijsdata beschikbaar",
            "score": None,
            "rating": "Unknown",
            "confidence": 0,
            "reasons": ["No current price data available"],
            "recommended_devices": [],
        }

    if negative_total:
        score = 100
        reasons.append("Total price is negative")
    elif negative_market:
        score += 20
        reasons.append("Market price is negative")

    if avg is not None:
        difference_to_average = current_price - avg
        if current_price < avg:
            score += 20
            reasons.append("Price is below average")
        elif current_price > avg:
            score -= 20
            reasons.append("Price is above average")
    else:
        difference_to_average = None

    if minimum is not None and maximum is not None and maximum != minimum:
        position = (current_price - minimum) / (maximum - minimum)
        score += int((1 - position) * 30) - 15
        if position <= 0.20:
            reasons.append("Current price is in the cheapest part of the day")
        if position >= 0.80:
            reasons.append("Current price is in the most expensive part of the day")

    next_hour_difference = None
    if next_price is not None:
        next_hour_difference = next_price - current_price
        if next_price > current_price:
            score += 5
            reasons.append("Next hour is more expensive")
        elif next_price < current_price:
            score -= 8
            reasons.append("Next hour is cheaper")

    cheapest_block_active = False
    if cheap_block:
        now_label = datetime.now(TZ).strftime("%H:%M")
        start = cheap_block.get("start")
        end = cheap_block.get("end")
        cheapest_block_active = start is not None and end is not None and start <= now_label < end
        if cheapest_block_active:
            score += 15
            reasons.append("Cheap block is active")

    score = max(0, min(100, score))

    if score >= 90:
        rating = "Excellent"
    elif score >= 75:
        rating = "Very good"
    elif score >= 60:
        rating = "Good"
    elif score >= 40:
        rating = "Average"
    elif score >= 20:
        rating = "Expensive"
    else:
        rating = "Very expensive"

    rank = _rank_current_price(day, current_price)
    wait_minutes = _minutes_until_time(cheapest_hour)
    potential_saving = None
    if cheapest_price is not None:
        potential_saving = round(max(0, current_price - cheapest_price), 5)

    if negative_total:
        advice = "Gebruik nu veel stroom: de totaalprijs is negatief"
    elif negative_market:
        advice = "Goed moment: de kale beursprijs is negatief"
    elif score >= 75:
        advice = "Goed moment om stroom te gebruiken"
    elif potential_saving is not None and potential_saving >= 0.05 and cheapest_hour:
        advice = f"Wacht tot {cheapest_hour}; dat bespaart €{potential_saving:.3f}/kWh"
    elif next_hour_difference is not None and next_hour_difference < -0.03:
        advice = f"Wacht eventueel tot volgend uur; dat is €{abs(next_hour_difference):.3f}/kWh goedkoper"
    elif score <= 25 and expensive_hour:
        advice = f"Duur moment: stel groot verbruik uit. Duurste uur is {expensive_hour}"
    else:
        advice = "Geen bijzonder advies"

    return {
        "advice": advice,
        "score": score,
        "rating": rating,
        "confidence": 95 if current_price is not None and avg is not None else 70,
        "current_price": current_price,
        "next_price": next_price,
        "average_price": avg,
        "minimum_price": minimum,
        "maximum_price": maximum,
        "current_market_price": market_price,
        "difference_to_average": round(difference_to_average, 5) if difference_to_average is not None else None,
        "difference_to_cheapest": round(current_price - cheapest_price, 5) if cheapest_price is not None else None,
        "next_hour_difference": round(next_hour_difference, 5) if next_hour_difference is not None else None,
        "current_rank": rank,
        "total_hours": len(hour_prices(day)),
        "best_hour": cheapest_hour,
        "best_price": cheapest_price,
        "most_expensive_hour": expensive_hour,
        "wait_minutes": wait_minutes,
        "potential_saving": potential_saving,
        "cheapest_block": cheap_block,
        "current_block": cheapest_block_active,
        "recommended_devices": _recommended_devices(score, negative_total, negative_market),
        "reasons": reasons,
    }
