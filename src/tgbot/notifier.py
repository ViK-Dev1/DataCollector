import logging
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Wraps the Telegram Bot API for sending messages.

    - send_alert()   : sends only if notifications are enabled
    - send_message() : always sends (used for command responses)
    """

    def __init__(self, token: str, chat_id: str) -> None:
        self._bot = Bot(token=token)
        self._chat_id = chat_id
        self._enabled = True

    async def send_alert(self, text: str) -> None:
        if not self._enabled:
            return
        await self._send('❗ - '+text)

    async def send_message(self, text: str) -> None:
        await self._send(text)

    async def _send(self, text: str) -> None:
        try:
            await self._bot.send_message(chat_id=self._chat_id, text=text)
        except TelegramError as e:
            logger.error(f"[telegram] Failed to send message: {e}")

    def disable(self) -> None:
        self._enabled = False
        logger.info("[telegram] Notifications disabled.")

    def enable(self) -> None:
        self._enabled = True
        logger.info("[telegram] Notifications enabled.")

    @property
    def enabled(self) -> bool:
        return self._enabled
