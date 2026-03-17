from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SymbolStatus:
    symbol: str
    connected: bool = False
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    restart_count: int = 0


class StatusTracker:
    """
    Tracks the live health of every monitored symbol.
    Updated by WSClient (connect/disconnect) and read by the Telegram /status command.
    """

    def __init__(self) -> None:
        self._started_at = datetime.now()
        self._symbols: dict[str, SymbolStatus] = {}

    """ 
    F - Register a new symbol when the application start monitoring it
    """
    def register(self, symbol: str) -> None:
        self._symbols[symbol] = SymbolStatus(symbol=symbol)

    """ 
    F - Mark the as connected and ready to monitor that symbol
    """
    def mark_connected(self, symbol: str) -> None:
        if symbol in self._symbols:
            self._symbols[symbol].connected = True

    """ 
    F - Mark the as disconnected whenever any error or forcestop command arises
    and restart the counter to tell how many time it was restarted.
    """
    def mark_disconnected(self, symbol: str, reason: str) -> None:
        if symbol in self._symbols:
            s = self._symbols[symbol]
            s.connected = False
            s.last_error = reason
            s.last_error_time = datetime.now()
            s.restart_count += 1

    def get_all(self) -> list[SymbolStatus]:
        return list(self._symbols.values())

    '''
    F - p - property that calculates and returns the value of the uptime of the system
    '''
    @property
    def uptime(self) -> str:
        delta = datetime.now() - self._started_at
        total_seconds = int(delta.total_seconds())
        d, rem = divmod(total_seconds, 86400) # it calculates the days by dividing by 86400 seconds (= 60 * 60 * 24)
        h, rem = divmod(rem, 3600) # it calculate the hours by dividing by 3600 seconds (= 60 * 60)
        m = rem // 60 # it calculate the minutes by dividing by 60 seconds
        return f"{d}dd - {h:02}hh {m:02} mm"
