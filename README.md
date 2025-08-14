# bot_binance

Binance Futures Trading Bot – Testnet Version
A Python-based automated trading bot for Binance Futures Testnet, designed for learning, testing, and experimenting with API-based trading strategies without risking real money.

Features
Connects securely to Binance Futures Testnet using API keys
Place, cancel, and track market orders
Error handling for network failures and Binance API errors
Retry mechanism for temporary issues (e.g., timeouts)
Logging of all trading activities and errors to trading_log.txt
Modular and extendable code for adding strategies

Libraries:
requests – API communication
hmac & hashlib – request signing
dotenv – secure API key management
datetime – timestamp logging
