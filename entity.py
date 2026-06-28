from __future__ import annotations

import aiohttp
import async_timeout

from .const import API_URL


class EssentDynamicApiClient:
    async def async_get_prices(self) -> dict:
        headers = {
            "Accept": "application/json",
            "x-request-origin": "client",
            "User-Agent": "Home Assistant Essent Dynamic Prices",
        }

        async with async_timeout.timeout(20):
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, headers=headers) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise RuntimeError(f"Essent API returned {response.status}: {text[:150]}")
                    return await response.json()
