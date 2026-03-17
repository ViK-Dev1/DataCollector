import logging
from datetime import datetime
from decimal import Decimal

from fetcher.handlers.base_handler import BaseHandler
from db.models.liquidations import Liquidation
from db.db_tables import LIQUIDATIONS
from queues.data_queue import DataQueue, QueueItem
from utils import next_id, TZ_ROME

logger = logging.getLogger(__name__)


class LiquidationHandler(BaseHandler):
    """
    Handles 'liquidation' messages.
    Every message is a forced liquidation event — all are saved.

    Bybit message structure:
        {
            "topic": "allLiquidation.BTCUSDT",
            "data": [
                {
                    "T":  1672304486866,
                    "s":  "BTCUSDT",
                    "S":  "Buy",
                    "v":  "0.100",
                    "p":  "16578.50"
                }
            ]
        }
    """

    async def handle(self, msg: dict) -> None:
        for d in msg.get("data", []):
            try:
                record = Liquidation(
                    id=next_id(),
                    ts=datetime.fromtimestamp(d["T"] / 1000, tz=TZ_ROME),
                    symbol_id=self.symbol_id,
                    side=d["S"],
                    size1=Decimal(d["v"]),
                    price=Decimal(d["p"]),
                )
                await self.queue.put(QueueItem(table=LIQUIDATIONS, data=record))
            except Exception as e:
                logger.error(f"[liquidation][{self.symbol}] Parse error: {e} — {d}")
