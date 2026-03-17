import asyncio
import logging
from datetime import datetime

from fetcher.handlers.base_handler import BaseHandler
from db.models.orderbook import OrderbookData
from db.db_tables import ORDERBOOK_DATA
from queues.data_queue import DataQueue, QueueItem
from utils import next_id, TZ_ROME

logger = logging.getLogger(__name__)


class OrderbookHandler(BaseHandler):
    """
    Handles 'orderbook.50' messages.

    Strategy:
    - Maintains a local mirror of the top-50 bids/asks in memory.
    - Applies Bybit 'snapshot' (full replace) and 'delta' (incremental) updates.
    - A background task snapshots the current state every N seconds and pushes
      it to the queue. No snapshot is pushed if the orderbook is empty.

    Bybit message structure:
        snapshot → replace entire local state
        delta    → apply updates; [price, "0"] means remove that level

        {
            "topic": "orderbook.50.BTCUSDT",
            "type":  "snapshot" | "delta",
            "data":  {
                "b": [["84100.00", "0.50"], ...],   # bids
                "a": [["84101.00", "0.60"], ...]    # asks
            }
        }
    """

    def __init__(self, symbol: str, symbol_id: int, queue: DataQueue, snapshot_interval_s: int):
        super().__init__(symbol, symbol_id, queue)
        self._snapshot_interval = snapshot_interval_s
        self._bids: dict[str, str] = {}   # price -> size
        self._asks: dict[str, str] = {}
        self._snapshot_task: asyncio.Task | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def on_connect(self) -> None:
        self._snapshot_task = asyncio.create_task(
            self._snapshot_loop(),
            name=f"ob_snapshot_{self.symbol}",
        )
        logger.debug(f"[orderbook][{self.symbol}] Snapshot task started")

    async def on_disconnect(self) -> None:
        if self._snapshot_task and not self._snapshot_task.done():
            self._snapshot_task.cancel()
            self._snapshot_task = None
        logger.debug(f"[orderbook][{self.symbol}] Snapshot task stopped")

    def reset(self) -> None:
        self._bids.clear()
        self._asks.clear()
        logger.debug(f"[orderbook][{self.symbol}] State cleared on reconnect")

    # ── Message handling ──────────────────────────────────────────────────────

    async def handle(self, msg: dict) -> None:
        msg_type = msg.get("type")
        data = msg.get("data", {})

        # Update the orderbook in memory
        try:
            if msg_type == "snapshot":
                self._bids = {p: s for p, s in data.get("b", [])}
                self._asks = {p: s for p, s in data.get("a", [])}

            elif msg_type == "delta":
                for p, s in data.get("b", []):
                    if s == "0":
                        self._bids.pop(p, None) # if the size corresponding to price p is 0, just remove that value
                    else:
                        self._bids[p] = s # overwrite the value
                for p, s in data.get("a", []):
                    if s == "0":
                        self._asks.pop(p, None)
                    else:
                        self._asks[p] = s
        except Exception as e:
            logger.error(f"[orderbook][{self.symbol}] Update error: {e}")

    # ── Snapshot loop ─────────────────────────────────────────────────────────

    async def _snapshot_loop(self) -> None:
        while True:
            await asyncio.sleep(self._snapshot_interval)
            await self._push_snapshot()

    async def _push_snapshot(self) -> None:
        if not self._bids and not self._asks:
            return
        try:
            # each list is sorted by the price, which is firstly converted into a number first
            # bids are saved correcly in descending way
            bids = sorted(self._bids.items(), key=lambda x: float(x[0]), reverse=True)[:50]
            # asks are saved ascending way
            asks = sorted(self._asks.items(), key=lambda x: float(x[0]))[:50]

            record = OrderbookData(
                id=next_id(),
                ts=datetime.now(TZ_ROME),
                symbol_id=self.symbol_id,
                bid_levels=[{"p": p, "s": s} for p, s in bids],
                ask_levels=[{"p": p, "s": s} for p, s in asks],
            )
            await self.queue.put(QueueItem(table=ORDERBOOK_DATA, data=record))
            logger.debug(f"[orderbook][{self.symbol}] Snapshot pushed ({len(bids)} bids, {len(asks)} asks)")
        except Exception as e:
            logger.error(f"[orderbook][{self.symbol}] Snapshot push error: {e}")
