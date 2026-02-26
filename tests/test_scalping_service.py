import sys
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# Mock talib if not installed
if "talib" not in sys.modules:
    sys.modules["talib"] = MagicMock()

from api.services.scalping_service import ScalpingService


class TestScalpingService(unittest.TestCase):
    def setUp(self):
        self.service = ScalpingService()
        self.df = pd.DataFrame(
            {
                "open": np.random.rand(100),
                "high": np.random.rand(100),
                "low": np.random.rand(100),
                "close": np.random.rand(100),
                "volume": np.random.rand(100),
            }
        )

    @patch("talib.EMA")
    @patch("talib.STOCH")
    def test_5m_buy_signal(self, mock_stoch, mock_ema):
        # Setup specific values for Buy Signal
        # Trend: Close > EMA20 > EMA50
        # Stoch: Cross Up (prev k < prev d, curr k > curr d) in Oversold (<20)

        # Mock EMA return values (numpy arrays - matching optimized service behavior)
        ema20_vals = np.full(100, 100.0)
        ema50_vals = np.full(100, 90.0)
        mock_ema.side_effect = [ema20_vals, ema50_vals]

        # Mock Stoch return values
        k_vals = np.full(100, 10.0)
        d_vals = np.full(100, 15.0)
        # Last index: k=18, d=15 (Cross up? No wait. Prev: k=10, d=15. Curr: k=18, d=15 -> Cross Up)
        k_vals[-1] = 18.0
        d_vals[-1] = 15.0
        k_vals[-2] = 10.0
        d_vals[-2] = 15.0  # d stays same for simplicity

        mock_stoch.return_value = (k_vals, d_vals)

        # Adjust DF close price to be > EMA20 (100)
        self.df["close"] = 110.0

        result = self.service.analyze_strategy(self.df, "5m")

        self.assertEqual(result["signal"], "BUY")
        self.assertEqual(result["timeframe"], "5m")
        self.assertIn("Uptrend", result["reasoning"])
        self.assertIn("Stochastic Cross Up", result["reasoning"])

    @patch("talib.BBANDS")
    @patch("talib.RSI")
    def test_15m_sell_signal(self, mock_rsi, mock_bbands):
        # Setup Sell Signal
        # Price touches Upper BB, RSI Overbought (>70)

        upper = np.full(100, 105.0)
        middle = np.full(100, 100.0)
        lower = np.full(100, 95.0)
        mock_bbands.return_value = (
            upper,
            middle,
            lower,
        )

        rsi_vals = np.full(100, 75.0)
        mock_rsi.return_value = rsi_vals

        # High >= Upper
        self.df["high"] = 106.0
        self.df["low"] = (
            100.0  # Ensure low is NOT <= lower band (95.0) to avoid entering Long block
        )
        self.df["close"] = (
            104.0  # Doesn't matter for touch check which uses high/low depending on implementation
        )

        result = self.service.analyze_strategy(self.df, "15m")

        self.assertEqual(result["signal"], "SELL")
        self.assertEqual(result["timeframe"], "15m")
        self.assertIn("Upper Bollinger Band", result["reasoning"])
        self.assertIn("RSI Overbought", result["reasoning"])

    @patch("talib.MACD")
    @patch("talib.EMA")
    def test_30m_buy_signal(self, mock_ema, mock_macd):
        # Setup Buy Signal
        # Price > EMA50, MACD Hist Cross Up 0

        ema50_vals = np.full(100, 90.0)
        mock_ema.return_value = ema50_vals

        macd_line = np.zeros(100)
        signal_line = np.zeros(100)
        hist = np.full(100, -1.0)

        # Cross up: Prev <= 0, Curr > 0
        hist[-2] = -0.5
        hist[-1] = 0.5

        mock_macd.return_value = (
            macd_line,
            signal_line,
            hist,
        )

        self.df["close"] = 95.0

        result = self.service.analyze_strategy(self.df, "30m")

        self.assertEqual(result["signal"], "BUY")
        self.assertEqual(result["timeframe"], "30m")
        self.assertIn("Price > EMA50", result["reasoning"])
        self.assertIn("MACD Histogram crossed above Zero", result["reasoning"])


if __name__ == "__main__":
    unittest.main()
