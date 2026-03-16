from dataclasses import dataclass
from datetime import datetime


@dataclass
class CryptoPair:
    id: int
    symbol: str
    exchange: str
    base: str
    quote: str
    addet_at: datetime
    monitoring_on: bool
