from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class PriceData:
    id: int
    ts: datetime
    symbol_id: int
    o: Decimal
    h: Decimal
    l: Decimal
    c: Decimal
    vol: Decimal
