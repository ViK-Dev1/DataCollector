<h1 align="center"><a href="https://vik-dev1.github.io/DataCollector/" target="_blank">DataCollector</a></h1>

<p align="center">
  📡 Real-Time Crypto Data Pipeline 🗄️
</p>

<p align="center">
  ⚡ Fast &nbsp;|&nbsp; 🔁 Resilient &nbsp;|&nbsp; 📊 Precise
</p>

<p align="center">
  <a href="https://vik-dev1.github.io/DataCollector/" target="_blank">
    <img src="botLogo.png" width="180" style="border-radius:50%; border: 3px solid #e53935;" />
  </a>
</p>

---

**DataCollector** is a Python service that connects to **Bybit WebSocket** streams and continuously collects real-time crypto market data — trades, order book snapshots, klines, and liquidations — storing everything into a **TimescaleDB** time-series database. 📈

<p align="center">
  📖 Full documentation available at <a href="https://vik-dev1.github.io/DataCollector/" target="_blank">vik-dev1.github.io/DataCollector</a>
</p>

---

### 😎 Disclaimer ⚠️

- This project was built for personal use and as a learning exercise in async Python and time-series data engineering
- The service intentionally omits trading logic — it is purely a **data collection layer**
- Credentials and configuration are kept outside the repository and injected at runtime via mounted volumes

---

### 🗂️ Repository Structure 📁

- **`src/`** — Python source code (handlers, WebSocket client, Telegram bot, DB writer)
- **`db/`** — SQL scripts to create the TimescaleDB schema
- **`docs/`** — Documentation and assets
- **`Dockerfile`** — Container definition for the collector service
- **`docker-compose.yml`** — Orchestrates the collector + TimescaleDB together
- **`requirements.txt`** — Python dependencies

---

### ❓ Why did I build it? 👀

- 🔌 Existing solutions didn't give full control over what data to store and how
- ⏱️ Needed tick-level granularity, not just OHLCV candles
- 📦 Wanted a self-hosted, always-on pipeline with no third-party dependencies

---

### 🤖 How does it work? 🔍

The service opens a persistent WebSocket connection to Bybit and subscribes to multiple feeds at once. Each message is routed to a dedicated handler that parses and queues it. A batch writer flushes the queue into TimescaleDB at a configurable interval. A supervisor monitors all tasks and automatically restarts any that crash — keeping the pipeline running 24/7 without manual intervention.

A **Telegram bot** runs alongside the collector for remote monitoring and control — no need to SSH into the server to check on it.
