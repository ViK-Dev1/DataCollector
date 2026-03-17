import asyncio
from abc import ABC, abstractmethod

from queues.data_queue import DataQueue


class BaseHandler(ABC):
    def __init__(self, symbol: str, symbol_id: int, queue: DataQueue):
        self.symbol = symbol
        self.symbol_id = symbol_id
        self.queue = queue

    @abstractmethod
    async def handle(self, msg: dict) -> None:
        """Process a raw message from the websocket."""

    def reset(self) -> None:
        """Called on WS reconnect. Override to clear stateful data."""

    async def on_connect(self) -> None:
        """Called after a successful WS connection and subscription."""

    async def on_disconnect(self) -> None:
        """Called before a reconnection attempt."""
