import asyncio
import json
import logging
from typing import Optional

from websockets import connect
from websockets.exceptions import ConnectionClosed

from db.models.crypto_pair import CryptoPair
from fetcher.handlers.base_handler import BaseHandler
from fetcher.handlers.trades_handler import TradesHandler
from fetcher.handlers.kline_handler import KlineHandler
from fetcher.handlers.liquidation_handler import LiquidationHandler
from fetcher.handlers.orderbook_handler import OrderbookHandler
from queues.data_queue import DataQueue
from tgbot.notifier import TelegramNotifier
from tgbot.status_tracker import StatusTracker

logger = logging.getLogger(__name__)

class WSClient:
    """
    Manages one WebSocket connection for a single crypto pair.

    Responsibilities:
    - Connect to exchange WS endpoint
    - Subscribe to all configured subjects for this symbol
    - Send periodic pings to keep the connection alive
    - Route incoming messages to the appropriate handler
    - Reconnect with exponential backoff on any disconnect or error
    - Call handler lifecycle hooks (on_connect / on_disconnect / reset)
    - Notify Telegram and update StatusTracker on reconnect events
    """

    def __init__(
        self,
        pair: CryptoPair,
        exchange_cfg: dict,
        app_cfg: dict,
        queue: DataQueue,
        notifier: Optional[TelegramNotifier] = None,
        tracker: Optional[StatusTracker] = None,
    ):
        self._pair = pair
        self._ws_url = exchange_cfg["ws_url"]
        self._subjects = [f"{s}.{pair.symbol}" for s in exchange_cfg["subjectStrings"]]
        self._reconnect = app_cfg["reconnect"]
        self._ping_interval = app_cfg["ping_interval_s"]
        self._notifier = notifier
        self._tracker = tracker
        self._handlers: dict[str, BaseHandler] = self._build_handlers(
            pair, queue, app_cfg["orderbook_snapshot_interval_s"]
        )

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self) -> None:
        attempt = 0
        base = self._reconnect["base_delay_s"]
        max_delay = self._reconnect["max_delay_s"]
        max_retries = self._reconnect["max_retries"]

        while attempt <= max_retries:
            try:
                logger.info(f"[ws][{self._pair.symbol}] Connecting...")
                await self._connect_and_run()
                attempt = 0
            except (ConnectionClosed, OSError, Exception) as exc:
                attempt += 1
                reason = str(exc) or type(exc).__name__

                if attempt > max_retries:
                    logger.error(f"[ws][{self._pair.symbol}] Max retries ({max_retries}) reached. Stopping.")
                    raise

                delay = min(base * (2 ** (attempt - 1)), max_delay)
                logger.warning(
                    f"[ws][{self._pair.symbol}] Disconnected: {reason}. "
                    f"Retry {attempt}/{max_retries} in {delay}s..."
                )

                if self._tracker:
                    self._tracker.mark_disconnected(self._pair.symbol, reason)

                if self._notifier:
                    await self._notifier.send_alert(
                        f"[{self._pair.symbol}] WS disconnected: {reason}\n"
                        f"Retry {attempt}/{max_retries} in {delay}s..."
                    )

                await self._on_disconnect()
                await asyncio.sleep(delay)

    # ── Internal connect/run loop ─────────────────────────────────────────────

    async def _connect_and_run(self) -> None:
        async with connect(self._ws_url) as ws:
            await self._subscribe(ws)
            await self._on_connect()

            ping_task = asyncio.create_task(
                self._ping_loop(ws),
                name=f"ping_{self._pair.symbol}",
            )
            try:
                async for raw in ws:
                    msg = json.loads(raw)
                    await self._dispatch(msg)
            finally:
                ping_task.cancel()

    async def _subscribe(self, ws) -> None:
        payload = {"op": "subscribe", "args": self._subjects}
        await ws.send(json.dumps(payload))
        logger.info(f"[ws][{self._pair.symbol}] Subscribed to: {self._subjects}")

    async def _ping_loop(self, ws) -> None:
        while True:
            await asyncio.sleep(self._ping_interval)
            await ws.send(json.dumps({"op": "ping"}))
            logger.debug(f"[ws][{self._pair.symbol}] Ping sent")

    # ── Message routing ───────────────────────────────────────────────────────

    async def _dispatch(self, msg: dict) -> None:
        topic = msg.get("topic", "")
        if not topic:
            return  # pong / subscription ack — ignore

        for prefix, handler in self._handlers.items():
            if topic.startswith(prefix):
                await handler.handle(msg)
                return

        logger.debug(f"[ws][{self._pair.symbol}] Unhandled topic: {topic}")

    # ── Lifecycle hooks ───────────────────────────────────────────────────────

    async def _on_connect(self) -> None:
        if self._tracker:
            self._tracker.mark_connected(self._pair.symbol)
        for handler in self._handlers.values():
            await handler.on_connect()

    async def _on_disconnect(self) -> None:
        for handler in self._handlers.values():
            await handler.on_disconnect()
            handler.reset()

    # ── Handler setup ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_handlers(
        pair: CryptoPair,
        queue: DataQueue,
        ob_interval: int,
    ) -> dict[str, BaseHandler]:
        return {
            "publicTrade":      TradesHandler(pair.symbol, pair.id, queue),
            "orderbook":        OrderbookHandler(pair.symbol, pair.id, queue, ob_interval),
            "kline":            KlineHandler(pair.symbol, pair.id, queue),
            "allLiquidation":   LiquidationHandler(pair.symbol, pair.id, queue),
        }
