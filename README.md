# Binance Futures Trading Bot - Hiring Assessment

**Note:** This project was developed as a technical assessment for a hiring process, with a completion timeframe of approximately 24-48 hours.

---

## Overview

This is a functional trading bot for the Binance Futures Testnet, complete with a user-friendly graphical interface (GUI). The application allows users to monitor cryptocurrency prices in real-time, place `MARKET` and `LIMIT` orders, and view their order history.

The project emphasizes a clean architecture, robust error handling, and a polished user experience.

## Features

-   **Real-Time Price Monitoring:** Live price feed for BTC/USDT with color-coded price change indicators.
-   **Interactive GUI:** A modern and intuitive interface built with `CustomTkinter`.
-   **Order Placement:** Easily place `MARKET` and `LIMIT` orders for multiple symbols (BTC, ETH, BNB).
-   **Order History:** A clear, styled table displays your recent order history with auto-refresh and color-coded order types.
-   **Notifications:** Get instant feedback on order successes and failures.
-   **Secure Configuration:** API keys are managed securely using a `.env` file.
-   **Robust Testing:** The core trading logic is validated by a comprehensive suite of unit tests.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd TradingBot_Python
    ```

2.  **Install Dependencies:**
    Make sure you have Python 3 installed. Then, install the required packages using pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Keys:**
    -   Create a file named `.env` in the root of the project directory.
    -   Add your Binance Testnet API key and secret to this file:
        ```env
        BINANCE_API_KEY=your_testnet_api_key
        BINANCE_API_SECRET=your_testnet_api_secret
        ```
    -   You can obtain testnet keys from [Binance Futures Testnet](https://testnet.binancefuture.com/).

## How to Run the Bot

To start the trading interface, run the `trading_ui.py` script from the root directory:

```bash
python trading_ui.py
```

## Running the Tests

The project includes a full suite of unit tests for the core bot logic to ensure its reliability.

To run the tests, execute the following command from the root directory:

```bash
python -m pytest
```

This command will automatically discover and run all tests located in the `tests/` directory.

## Project Structure

```
TradingBot_Python/
├── src/
│   └── bot.py             # Core trading logic
├── tests/
│   └── test_bot.py        # Unit tests for the bot
├── logs/                  # For storing log files (if implemented)
├── .env                   # Stores API keys (must be created manually)
├── trading_ui.py          # Main application entry point (GUI)
├── requirements.txt       # Project dependencies
└── README.md              # This file
```

