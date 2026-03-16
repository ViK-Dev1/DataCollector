import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class QueueItem:
    table: str  # "orders" | "price_data" | "orderbook_data" | "liquidations"
    data: Any   # model dataclass instance


# Type alias used across the codebase
DataQueue = asyncio.Queue
