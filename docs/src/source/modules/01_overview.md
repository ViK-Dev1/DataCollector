# Overview

## Purpose

Understanding when specific market patterns occur — across different times of the day or days of the week — requires access to granular, historical market data. While several online platforms offer visualisation tools and some degree of data export, they typically impose strict limitations on the amount of data that can be downloaded and how far back in time the user can go. This makes them unsuitable for building a complete, long-term dataset for automated analysis.

Commercial solutions that provide raw derivatives data at tick level with no such restrictions, such as [Tardis](https://tardis.dev/#pricing), exist but come at a significant cost, making them impractical for personal or exploratory use.

**DataCollector** was built to address this gap. The goal was to have a self-hosted, fully controlled pipeline that continuously collects raw market data from **Bybit** — one of the leading derivatives exchanges — and stores it locally for analysis.

## What It Collects

The service subscribes to the following real-time data feeds:

- **Trades** — every executed transaction on the order book
- **Order Book** — snapshots of the top 50 bid and ask levels
- **Klines** — 1-minute candlestick data (open, high, low, close, volume)
- **Liquidations** — forced position closures across the market

## Future Direction

Beyond data analysis, the architecture of DataCollector is designed with extensibility in mind. The collected data can serve as the foundation for future integrations, including automated trading bots or real-time signal generation systems.
