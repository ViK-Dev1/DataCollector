import logging
from datetime import datetime
from decimal import Decimal

from fetcher.handlers.base_handler import BaseHandler
from db.models.price_data import PriceData
from db.db_tables import PRICE_DATA
from queues.data_queue import DataQueue, QueueItem
from utils import next_id, TZ_ROME

logger = logging.getLogger(__name__)


class KlineHandler(BaseHandler):
    """
    Handles 'kline.1' messages.
    Bybit sends frequent updates for the current candle — only saves when confirm=True,
    which means the candle is closed and final.

    Bybit message structure:
        {
            "topic": "kline.1.BTCUSDT",
            "data": [
                {
                    "start":     1672304460000,
                    "open":      "16578.50",
                    "high":      "16600.00",
                    "low":       "16570.00",
                    "close":     "16590.00",
                    "volume":    "1.234",
                    "confirm":   true        # only save when this is True
                }
            ]
        }
    """

    async def handle(self, msg: dict) -> None:
        for candle in msg.get("data", []):
            if not candle.get("confirm", False):
                return
            try:
                record = PriceData(
                    id=next_id(),
                    ts=datetime.fromtimestamp(candle["start"] / 1000, tz=TZ_ROME),
                    symbol_id=self.symbol_id,
                    o=Decimal(candle["open"]),
                    h=Decimal(candle["high"]),
                    l=Decimal(candle["low"]),
                    c=Decimal(candle["close"]),
                    vol=Decimal(candle["volume"]),
                )
                await self.queue.put(QueueItem(table=PRICE_DATA, data=record))
                logger.debug(f"[kline][{self.symbol}] Confirmed candle @ {record.ts}")
            except Exception as e:
                logger.error(f"[kline][{self.symbol}] Parse error: {e} — {candle}")
