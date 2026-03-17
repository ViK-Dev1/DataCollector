<h1 align="center"><a href="https://vik-dev1.github.io/DataCollector/">DataCollector</a></h1>

<p align="center">
  📡 Real-Time Crypto Data Pipeline 🗄️
</p>

<p align="center">
  ⚡ Fast &nbsp;|&nbsp; 🔁 Resilient &nbsp;|&nbsp; 📊 Precise
</p>

<p align="center">
  <a href="https://vik-dev1.github.io/DataCollector/">
    <img src="botLogo.png" width="180" style="border-radius:50%; border: 3px solid #e53935;" />
  </a>
</p>

---

<p align="center"><a href="https://vik-dev1.github.io/DataCollector/">
  📖 Full documentation available here</a>
</p>

---

**DataCollector** is a Python application that connects to **Bybit WebSocket** streams and continuously collects real-time crypto market data — trades, order-book snapshots, klines, and liquidations — storing everything into a **TimescaleDB (PostgreSQL)** time-series database. 
A **Telegram bot** runs alongside the collector for remote monitoring and control — no need to SSH into the server to check on it. 📈

---

### ⚠️ Disclaimer

- This project was built for personal use and as a learning exercise in async Python and time-series data engineering
- The service intentionally omits trading logic — it is purely a **data collection layer**
- Credentials and configuration are kept outside the repository and injected at runtime to control all application settings

---

### 🗂️ Repository Structure

- **`src/`** — Python source code (handlers, WebSocket client, Telegram bot, DB writer)
- **`db/`** — SQL scripts to create the TimescaleDB schema
- **`docs/`** — Documentation files
- **`dockerfiles/docker-compose.yml`** — Orchestrates the collector + TimescaleDB together
- **`Dockerfile`** — Container definition for the collector service
- **`requirements.txt`** — Python dependencies

---

### ❓ Why did I build it?

- Existing solutions either lacked full control over what and how to store, or provided the required data at prohibitively high prices
- Needed tick-level granularity, not just OHLCV candles, to identify recurring patterns in selected crypto-pairs and develop data‑driven trading strategies
- Always wanted a self-hosted, always-on pipeline with no third-party dependencies

---

### 🤖 How does it work?

The service opens a dedicated WebSocket connection per crypto‑pair and subscribes to multiple feeds at once on each connection. Each message is routed to a dedicated handler that parses and queues it. A batch writer flushes the queue into TimescaleDB at a configurable interval. A supervisor monitors all tasks and automatically restarts any that crash — keeping the pipeline running 24/7 without manual intervention.

