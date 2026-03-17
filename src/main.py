import asyncio
import logging
import signal
import sys

from config import cfg
from db.connection import init_pool, close_pool
from db.models.crypto_pair import CryptoPair
from db.writer import DBWriter
from fetcher.supervisor import Supervisor
from queues.data_queue import DataQueue
from tgbot.notifier import TelegramNotifier
from tgbot.status_tracker import StatusTracker
from tgbot.bot import TelegramBot

'''
F - prepares the async logging with logs queue and handlers
'''
def _setup_logging() -> None:
    import queue
    import logging.handlers
    from pathlib import Path

    level = getattr(logging, cfg["app"]["log_level"], logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # stdout handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    # Daily rotating file handler — creates logs/datacollector.log,
    # rotates at midnight and keeps up to 30 days of history
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=logs_dir / "datacollector.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)

    log_queue: queue.Queue = queue.Queue()
    listener = logging.handlers.QueueListener(
        log_queue, stream_handler, file_handler, respect_handler_level=True
    )
    listener.start()

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(logging.handlers.QueueHandler(log_queue))

'''
F - gets the crypto pairs to monitor from a specific exchange
'''
async def _load_pairs(pool, exchange_name: str) -> list[CryptoPair]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, symbol, exchange, base, quote, addet_at, monitoring_on
            FROM crypto_pairs
            WHERE monitoring_on = true AND exchange = $1
            """,
            exchange_name,
        )
    pairs = [
        CryptoPair(
            id=r["id"],
            symbol=r["symbol"],
            exchange=r["exchange"],
            base=r["base"],
            quote=r["quote"],
            addet_at=r["addet_at"],
            monitoring_on=r["monitoring_on"],
        )
        for r in rows
    ]
    logging.getLogger(__name__).info(
        f"Loaded {len(pairs)} pair(s) for '{exchange_name}': {[p.symbol for p in pairs]}"
    )
    return pairs


def _build_telegram(tracker: StatusTracker, stop_event: asyncio.Event, pool) -> tuple[TelegramNotifier | None, TelegramBot | None]:
    token = cfg["telegram"]["token"]
    chat_id = cfg["telegram"]["chat_id"]
    if not token or not chat_id:
        logging.getLogger(__name__).warning(
            "[telegram] token or chat_id not set — Telegram integration disabled."
        )
        return None, None
    notifier = TelegramNotifier(token, chat_id)
    bot = TelegramBot(token, notifier, tracker, stop_event, pool)
    return notifier, bot


async def main() -> None:
    # Logger
    _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("DataCollector starting...")

    # DB
    pool = await init_pool(cfg["database"])
    # DATA QUEUE
    queue: DataQueue = asyncio.Queue()

    # Stop event — shared with the Telegram bot so /forceStop can trigger shutdown
    stop_event = asyncio.Event()

    # TG bot for notifications
    tracker = StatusTracker()
    notifier, tg_bot = _build_telegram(tracker, stop_event, pool)
    if tg_bot:
        await tg_bot.start()

    # DB - writer preparation
    writer = DBWriter(queue, pool, cfg["app"])
    writer_task = asyncio.create_task(writer.run(), name="db_writer")

    # DATA COLLECTION - for each exchange, a supervisor task is started and it starts the fetching operation
    supervisor_tasks = []
    for exchange_cfg in cfg["exchanges"]:
        if not exchange_cfg["enabled"]:
            continue

        pairs = await _load_pairs(pool, exchange_cfg["name"])
        if not pairs:
            logger.warning(f"No active pairs found for '{exchange_cfg['name']}'. Skipping.")
            continue

        supervisor = Supervisor(pairs, exchange_cfg, cfg["app"], queue, notifier, tracker)
        supervisor_tasks.append(
            asyncio.create_task(supervisor.run(), name=f"supervisor_{exchange_cfg['name']}")
        )

    if not supervisor_tasks:
        logger.error("No supervisors started. Check your DB pairs and config.")
        writer_task.cancel()  # cancel all writer tasks
        if tg_bot:
            await tg_bot.stop()  # close tg bot
        await close_pool()  # close db pool
        return

    # Gentle shut down
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)

    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass  # Ctrl+C on Windows cancels the task — fall through to cleanup

    logger.info("Shutting down...")
    for task in supervisor_tasks:
        task.cancel()
    writer_task.cancel()
    # waits till every task has stopped completely
    await asyncio.gather(*supervisor_tasks, writer_task, return_exceptions=True)
    if tg_bot:
        await tg_bot.stop()
    await close_pool() # close the db pool

    logger.info("DataCollector stopped.")


if __name__ == "__main__":
    asyncio.run(main())
