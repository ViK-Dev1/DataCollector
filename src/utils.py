import itertools
import time
from zoneinfo import ZoneInfo

TZ_ROME = ZoneInfo("Europe/Rome")

# Monotonically increasing ID generator.
# Seeded with current millisecond timestamp to avoid collisions across restarts.
# Safe to use without locking since asyncio is single-threaded.
_counter = itertools.count(int(time.time() * 1000))


def next_id() -> int:
    return next(_counter)
