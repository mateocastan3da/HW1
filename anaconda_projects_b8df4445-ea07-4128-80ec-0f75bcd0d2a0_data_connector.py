import os
from datetime import datetime, timedelta, timezone

import alpaca_trade_api as tradeapi
from dotenv import load_dotenv


class AlpacaDataConnector:
    """
    Connects to Alpaca's paper-trading and market-data APIs.
    """

    def __init__(self):
        # Load variables from the .env file
        load_dotenv()

        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.paper_url = "https://paper-api.alpaca.markets"

        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Alpaca API credentials were not found."
            )

        # REST connection used for account information,
        # historical data, and latest quotes
        self.api = tradeapi.REST(
            key_id=self.api_key,
            secret_key=self.secret_key,
            base_url=self.paper_url,
            api_version="v2"
        )

    def get_account(self):
        """Return paper-trading account information."""
        return self.api.get_account()

    def get_historical_data(
        self,
        symbol="TQQQ",
        days=30,
        bar_minutes=5
    ):
        """
        Download 1-minute or 5-minute OHLCV data for a symbol.
        """
        if bar_minutes not in (1, 5):
            raise ValueError(
                "bar_minutes must be either 1 or 5."
            )

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        timeframe = tradeapi.TimeFrame(
            bar_minutes,
            tradeapi.TimeFrameUnit.Minute
        )

        bars = self.api.get_bars(
            symbol=symbol.upper(),
            timeframe=timeframe,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            adjustment="raw",
            feed="iex"
        )

        historical_data = bars.df[
            ["open", "high", "low", "close", "volume"]
        ].copy()

        if historical_data.empty:
            raise ValueError(
                f"No historical data was returned for {symbol}."
            )

        return historical_data

    def get_latest_quote(self, symbol="TQQQ"):
        """Return the latest available bid/ask quote."""
        return self.api.get_latest_quote(symbol.upper())

    def create_quote_stream(self):
        """Create a real-time IEX quote stream."""
        return tradeapi.Stream(
            key_id=self.api_key,
            secret_key=self.secret_key,
            base_url=self.paper_url,
            data_feed="iex"
        )
