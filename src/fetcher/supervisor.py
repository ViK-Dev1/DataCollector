import asyncio
import logging
from typing import Optional

from db.models.crypto_pair import CryptoPair
from fetcher.ws_client import WSClient
from queues.data_queue import DataQueue
from tgbot.notifier import TelegramNotifier
from tgbot.status_tracker import StatusTracker

logger = logging.getLogger(__name__)

class Supervisor:
    """
    Manages the cryptopairs for one exchange.
    Launches and monitors one WSClient task per crypto pair.

    Layer 2 resilience: if a WSClient task crashes with an unhandled exception
    (i.e. exhausted its own internal retries), the Supervisor logs it,
    sends a Telegram alert, and relaunches the task after a short delay.
    """

    def __init__(
        self,
        pairs: list[CryptoPair],
        exchange_cfg: dict,
        app_cfg: dict,
        queue: DataQueue,
        notifier: Optional[TelegramNotifier] = None,
        tracker: Optional[StatusTracker] = None,
    ):
        self._pairs = pairs
        self._exchange_cfg = exchange_cfg
        self._app_cfg = app_cfg
        self._queue = queue
        self._notifier = notifier
        self._tracker = tracker
        self._tasks: dict[str, asyncio.Task] = {}

    '''
    F - run method needed for task launching + updates the pair into the tracker class
    '''
    async def run(self) -> None:
        if not self._pairs:
            logger.warning("[supervisor] No pairs to monitor.")
            return

        # launches the data collection for every pair
        for pair in self._pairs:
            if self._tracker:
                self._tracker.register(pair.symbol)
            self._launch(pair)

        # makes the supervisor keep running, until all the collection tasks are all completed
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)

    def _launch(self, pair: CryptoPair) -> None:
        client = WSClient(pair, self._exchange_cfg, self._app_cfg, self._queue,
                          self._notifier, self._tracker)
        task = asyncio.create_task(client.run(), name=f"ws_{pair.symbol}")
        task.add_done_callback(lambda t, p=pair: self._on_task_done(t, p))
        self._tasks[pair.symbol] = task
        logger.info(f"[supervisor] Launched task for {pair.symbol}")

    '''
    F - whenever a data collection task is completed, it has to be restarted after a certain delay
    '''
    def _on_task_done(self, task: asyncio.Task, pair: CryptoPair) -> None:
        if task.cancelled():
            logger.info(f"[supervisor] Task for {pair.symbol} cancelled.")
            return

        exc = task.exception()
        if exc:
            reason = str(exc) or type(exc).__name__
            delay = self._app_cfg["relaunch_delay_s"]
            logger.error(f"[supervisor] Task for {pair.symbol} crashed: {reason}. Relaunching in {delay}s...")

            if self._tracker:
                self._tracker.mark_disconnected(pair.symbol, reason)

            if self._notifier:
                asyncio.create_task(
                    self._notifier.send_alert(
                        f"[{pair.symbol}] Task crashed: {reason}\n"
                        f"Relaunching in {delay}s..."
                    )
                )

            asyncio.create_task(self._delayed_relaunch(pair))

    async def _delayed_relaunch(self, pair: CryptoPair) -> None:
        await asyncio.sleep(self._app_cfg["relaunch_delay_s"])
        self._launch(pair)
