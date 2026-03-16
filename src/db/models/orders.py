from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Order:
    id: int
    ts: datetime
    symbol_id: int
    trade_id: str
    side: str
    size1: Decimal
    price: Decimal
    tick_direction: str
