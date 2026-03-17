import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, filters

from tgbot.notifier import TelegramNotifier
from tgbot.status_tracker import StatusTracker
from db.db_tables import PRICE_DATA, ORDERS, LIQUIDATIONS, ORDERBOOK_DATA

logger = logging.getLogger(__name__)


# ── Command handlers ──────────────────────────────────────────────────────────

async def _status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    tracker: StatusTracker = context.application.bot_data["tracker"]
    notifier: TelegramNotifier = context.application.bot_data["notifier"]

    lines = ["DataCollector Status", "=" * 24]

    symbols = tracker.get_all()
    if not symbols:
        lines.append("No symbols registered yet.")
    else:
        for s in symbols:
            state = "✅ - Active" if s.connected else "❌ - Disconnected"
            line = f"{s.symbol}: {state}  (restarts: {s.restart_count})"
            if not s.connected and s.last_error:
                ts = s.last_error_time.strftime("%H:%M:%S") if s.last_error_time else "?"
                line += f"\n  Last error: {s.last_error} @ {ts}"
            lines.append(line)

    lines.append("")
    lines.append(f"Uptime: {tracker.uptime}")
    lines.append(f"Notifications: {'ON' if notifier.enabled else 'OFF'}")

    await update.message.reply_text("\n".join(lines))


async def _disable_notifications_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    notifier: TelegramNotifier = context.application.bot_data["notifier"]
    notifier.disable()
    await update.message.reply_text("🔴 - Notifications disabled")


async def _enable_notifications_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    notifier: TelegramNotifier = context.application.bot_data["notifier"]
    notifier.enable()
    await update.message.reply_text("🟢 - Notifications enabled")


async def _stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text("Example: /stats BTCUSDT")
        return

    symbol = context.args[0].upper()
    pool = context.application.bot_data["pool"]

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM crypto_pairs WHERE symbol = $1",
            symbol,
        )
        if row is None:
            await update.message.reply_text(f"Symbol '{symbol}' not saved")
            return

        symbol_id = row["id"]

        counts = {}
        for table in (PRICE_DATA, ORDERS, LIQUIDATIONS, ORDERBOOK_DATA):
            counts[table] = await conn.fetchval(
                f"SELECT COUNT(*) FROM {table} WHERE symbol_id = $1",
                symbol_id,
            )

    lines = [
        f"📊 {symbol} Stats",
        "=" * 24,
        f"Price data:   {counts[PRICE_DATA]:,} records",
        f"Orders:       {counts[ORDERS]:,}  records",
        f"Liquidations: {counts[LIQUIDATIONS]:,}  records",
        f"Orderbook:    {counts[ORDERBOOK_DATA]:,}  records",
    ]
    await update.message.reply_text("\n".join(lines))


async def _dbsize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    pool = context.application.bot_data["pool"]

    async with pool.acquire() as conn:
        db_size = await conn.fetchval(
            "SELECT pg_size_pretty(pg_database_size(current_database()))"
        )
        rows = await conn.fetch("""
            SELECT hypertable_name,
                   pg_size_pretty(hypertable_size(format('%I', hypertable_name)::regclass)) AS size
            FROM timescaledb_information.hypertables
            ORDER BY hypertable_name
        """)

    lines = [
        "🗄️ Database Size",
        "=" * 24,
        f"Total DB: {db_size}",
        "",
        "Hypertables:",
    ]
    for r in rows:
        lines.append(f"  {r['hypertable_name']}: {r['size']}")

    await update.message.reply_text("\n".join(lines))


async def _force_stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    now = datetime.now()
    expected = f"{now.year}{now.hour:02d}"

    if not context.args or context.args[0] != expected:
        await update.message.reply_text(f"❌ Wrong code! You are not allowed to stop the application")
        return

    stop_event: asyncio.Event = context.application.bot_data["stop_event"]
    await update.message.reply_text("🛑 Stopping DataCollector...")
    stop_event.set()


# ── Bot lifecycle ─────────────────────────────────────────────────────────────

class TelegramBot:
    """
    Manages the Telegram bot lifecycle as an asyncio-compatible service.
    Runs alongside the main event loop — no blocking calls.
    """

    def __init__(self, token: str, notifier: TelegramNotifier, tracker: StatusTracker, stop_event: asyncio.Event, pool) -> None:
        self._app: Application = ApplicationBuilder().token(token).build()
        self._app.bot_data["notifier"] = notifier
        self._app.bot_data["tracker"] = tracker
        self._app.bot_data["stop_event"] = stop_event
        self._app.bot_data["pool"] = pool

        # commands
        self._app.add_handler(CommandHandler("status", _status_cmd))
        self._app.add_handler(CommandHandler("disableNotifications", _disable_notifications_cmd))
        self._app.add_handler(CommandHandler("enableNotifications", _enable_notifications_cmd))
        self._app.add_handler(CommandHandler("forceStop", _force_stop_cmd))
        self._app.add_handler(CommandHandler("stats", _stats_cmd))
        self._app.add_handler(CommandHandler("dbsize", _dbsize_cmd))

    async def start(self) -> None:
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(drop_pending_updates=True)
        logger.info("[telegram] Bot started.")

    async def stop(self) -> None:
        await self._app.updater.stop()
        await self._app.stop()
        await self._app.shutdown()
        logger.info("[telegram] Bot stopped.")
