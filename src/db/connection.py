import asyncpg
import json

_pool: asyncpg.Pool | None = None

'''
F - Creates the connection object to the postgres db instance
'''
async def init_pool(db_cfg: dict) -> asyncpg.Pool:
    global _pool

    _pool = await asyncpg.create_pool(
        host=db_cfg["host"],
        port=db_cfg["port"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        database=db_cfg["dbname"],
        min_size=db_cfg["pool_min_size"],
        max_size=db_cfg["pool_max_size"],
        init=_init_conn,
    )
    return _pool

'''
F - It creates the real connection to the DB
'''
async def _init_conn(conn: asyncpg.Connection) -> None:
    # Register JSONB codec so dicts are automatically serialized/deserialized
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )

'''
F - Close the pool of connections
'''
async def close_pool() -> None:
    if _pool:
        await _pool.close()
