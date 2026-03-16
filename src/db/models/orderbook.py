from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict


@dataclass
class OrderbookData:
    id: int
    ts: datetime
    symbol_id: int
    bid_levels: List[Dict]  # [{"p": "84100.00", "s": "0.50"}, ...]
    ask_levels: List[Dict]  # [{"p": "84101.00", "s": "0.60"}, ...]
