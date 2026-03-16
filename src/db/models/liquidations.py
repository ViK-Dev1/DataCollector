from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Liquidation:
    id: int
    ts: datetime
    symbol_id: int
    side: str
    size1: Decimal
    price: Decimal
