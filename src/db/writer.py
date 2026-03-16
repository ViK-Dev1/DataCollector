import asyncio
import logging

import asyncpg

from queues.data_queue import DataQueue, QueueItem
from db.models.orders import Order
from db.models.price_data import PriceData
from db.models.orderbook import OrderbookData
from db.models.liquidations import Liquidation
from db.db_tables import ORDERS, PRICE_DATA, ORDERBOOK_DATA, LIQUIDATIONS

logger = logging.getLogger(__name__)

'''
C - DBWriter - async data persistence layer
'''
class DBWriter:
    def __init__(self, queue: DataQueue, pool: asyncpg.Pool, app_cfg: dict):
        self._queue = queue
        self._pool = pool
        # Writing flush parameters
        self._batch_size = app_cfg["insert_batch_size"] # whenever It has N elements to write
        self._flush_interval = app_cfg["insert_flush_interval_ms"] / 1000.0 # flush time interval
        # in memory buffer to keep track of what to write on the db
        self._buffers: dict[str, list] = {
            ORDERS: [],
            PRICE_DATA: [],
            ORDERBOOK_DATA: [],
            LIQUIDATIONS: [],
        }

    '''
    F - task execution where it listens to queue data and appends it to the buffers array
    when conditions are met, it flushes the data!
    '''
    async def run(self) -> None:
        flush_task = asyncio.create_task(self._flush_loop())
        try:
            while True:
                item: QueueItem = await self._queue.get()
                self._buffers[item.table].append(item.data)
                if len(self._buffers[item.table]) >= self._batch_size:
                    await self._flush(item.table)
        finally:
            flush_task.cancel()

    '''
    F - flush loop based on flush interval time
    '''
    async def _flush_loop(self) -> None:
        while True:
            await asyncio.sleep(self._flush_interval)
            for table in list(self._buffers.keys()):
                if self._buffers[table]:
                    await self._flush(table)

    '''
    F - flush operations
    '''
    async def _flush(self, table: str) -> None:
        records = self._buffers[table]
        if not records:  # nothing to write
            return
        self._buffers[table] = [] # renew the considered buffer
        try:
            async with self._pool.acquire() as conn:
                await _insert(conn, table, records)
            logger.debug(f"[writer] Flushed {len(records)} rows to {table}")
        except Exception as e:
            logger.error(f"[writer] Insert failed for {table}: {e}")
            # Re-queue records to avoid data loss
            self._buffers[table] = records + self._buffers[table]


# ── Per-table insert functions ────────────────────────────────────────────────

async def _insert(conn: asyncpg.Connection, table: str, records: list) -> None:
    if table == ORDERS:
        await _insert_orders(conn, records)
    elif table == PRICE_DATA:
        await _insert_price_data(conn, records)
    elif table == ORDERBOOK_DATA:
        await _insert_orderbook(conn, records)
    elif table == LIQUIDATIONS:
        await _insert_liquidations(conn, records)

'''
F - inserts into orders table
'''
async def _insert_orders(conn: asyncpg.Connection, records: list[Order]) -> None:
    await conn.executemany(
        """
        INSERT INTO orders (id, ts, symbol_id, trade_id, side, size1, price, tick_direction)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT DO NOTHING
        """,
        [
            (r.id, r.ts, r.symbol_id, r.trade_id, r.side,
             float(r.size1), float(r.price), r.tick_direction)
            for r in records
        ],
    )

'''
F - inserts into price_data table
'''
async def _insert_price_data(conn: asyncpg.Connection, records: list[PriceData]) -> None:
    await conn.executemany(
        """
        INSERT INTO price_data (id, ts, symbol_id, o, h, l, c, vol)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT DO NOTHING
        """,
        [
            (r.id, r.ts, r.symbol_id,
             float(r.o), float(r.h), float(r.l), float(r.c), float(r.vol))
            for r in records
        ],
    )

'''
F - inserts into orderbook_data table
'''
async def _insert_orderbook(conn: asyncpg.Connection, records: list[OrderbookData]) -> None:
    await conn.executemany(
        """
        INSERT INTO orderbook_data (id, ts, symbol_id, bid_levels, ask_levels)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT DO NOTHING
        """,
        [
            (r.id, r.ts, r.symbol_id, r.bid_levels, r.ask_levels)
            for r in records
        ],
    )

'''
F - inserts into liquidations table
'''
async def _insert_liquidations(conn: asyncpg.Connection, records: list[Liquidation]) -> None:
    await conn.executemany(
        """
        INSERT INTO liquidations (id, ts, symbol_id, side, size1, price)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT DO NOTHING
        """,
        [
            (r.id, r.ts, r.symbol_id, r.side, float(r.size1), float(r.price))
            for r in records
        ],
    )
