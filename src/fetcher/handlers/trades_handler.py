import asyncio
import logging
from datetime import datetime
from decimal import Decimal

from fetcher.handlers.base_handler import BaseHandler
from db.models.orders import Order
from db.db_tables import ORDERS
from queues.data_queue import DataQueue, QueueItem
from utils import next_id, TZ_ROME

logger = logging.getLogger(__name__)


class TradesHandler(BaseHandler):
    """
    Handles 'publicTrade' messages.
    Each message may contain multiple trade entries — all are saved.

    Bybit message structure:
        {
            "topic": "publicTrade.BTCUSDT",
            "data": [
                {
                    "T": 1672304486865,   # timestamp ms
                    "s": "BTCUSDT",
                    "S": "Buy",           # side
                    "v": "0.001",         # size
                    "p": "16578.50",      # price
                    "L": "PlusTick",      # tick direction
                    "i": "trade-uuid"     # trade id
                }
            ]
        }
    """

    async def handle(self, msg: dict) -> None:
        for trade in msg.get("data", []):
            try:
                record = Order(
                    id=next_id(),
                    ts=datetime.fromtimestamp(trade["T"] / 1000, tz=TZ_ROME),
                    symbol_id=self.symbol_id,
                    trade_id=trade["i"],
                    side=trade["S"],
                    size1=Decimal(trade["v"]),
                    price=Decimal(trade["p"]),
                    tick_direction=trade.get("L", ""),
                )
                await self.queue.put(QueueItem(table=ORDERS, data=record))
            except Exception as e:
                logger.error(f"[trades][{self.symbol}] Parse error: {e} — {trade}")
