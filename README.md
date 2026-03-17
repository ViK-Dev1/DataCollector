# AlphaVolume — DataCollector

> A lightweight Python service that connects to crypto exchange WebSocket streams, collects real-time market data, and stores it into a TimescaleDB time-series database for further analysis.
> Built for reliability: automatic reconnection, crash recovery, and remote monitoring via Telegram bot.
> Designed to run 24/7 inside a Docker container on a Linux server.

---

## How It Works

The service opens persistent WebSocket connections to Bybit's public streaming API and subscribes to multiple data feeds simultaneously — trades, order book snapshots, candlestick (kline) data, and liquidations.
Each incoming message is parsed by a dedicated handler and pushed into an internal queue. A separate writer process consumes the queue in batches and inserts the records into TimescaleDB, a PostgreSQL extension optimised for time-series workloads.
A supervisor layer monitors all running tasks and automatically restarts any that crash, ensuring continuous data collection without manual intervention.

---

## Monitoring & Control

A Telegram bot runs alongside the collector and provides real-time visibility into the service without needing to SSH into the server.

| Command | Description |
|---|---|
| `/status` | Shows connection state and uptime for each tracked symbol |
| `/stats BTCUSDT` | Record counts per table for a given symbol |
| `/dbsize` | Total database size and per-table breakdown |
| `/enableNotifications` | Turn on error/disconnect alerts |
| `/disableNotifications` | Silence alerts |
| `/forceStop <code>` | Remotely shut down the service |
