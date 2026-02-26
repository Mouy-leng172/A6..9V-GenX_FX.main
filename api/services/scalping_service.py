import logging
from typing import Any, Dict

import pandas as pd
import talib

logger = logging.getLogger(__name__)


class ScalpingService:
    """
    Service for generating scalping signals based on 5m, 15m, and 30m timeframes.
    """

    def __init__(self):
        pass

    def analyze_strategy(self, df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """
        Analyzes the dataframe based on the specified timeframe strategy.

        Args:
            df (pd.DataFrame): OHLCV data. Must contain 'open', 'high', 'low', 'close', 'volume'.
            timeframe (str): One of "5m", "15m", "30m".

        Returns:
            Dict[str, Any]: Signal details including 'action' (BUY, SELL, NEUTRAL), 'confidence', and 'reasoning'.
        """
        # Ensure required columns exist
        required_cols = ["open", "high", "low", "close", "volume"]
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")

        if timeframe == "5m":
            return self._analyze_5m(df)
        elif timeframe == "15m":
            return self._analyze_15m(df)
        elif timeframe == "30m":
            return self._analyze_30m(df)
        else:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. Supported: 5m, 15m, 30m"
            )

    def _analyze_5m(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        5-Minute Strategy: EMA Trend Pullback with Stochastic.
        """
        # ⚡ Bolt: Extract NumPy arrays once to bypass Pandas Series overhead (~3x speedup on access)
        close_vals = df["close"].values
        high_vals = df["high"].values
        low_vals = df["low"].values

        # Indicators
        # ⚡ Bolt: Passing NumPy arrays to TA-Lib is ~8x faster than passing Pandas Series
        ema20 = talib.EMA(close_vals, timeperiod=20)
        ema50 = talib.EMA(close_vals, timeperiod=50)
        stoch_k, stoch_d = talib.STOCH(
            high_vals,
            low_vals,
            close_vals,
            fastk_period=5,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0,
        )

        # Get latest values (assume last row is the current candle)
        # We need the completed previous candle for confirmation, but for real-time we might check current.
        # Let's check the last completed candle (-1) and the one before (-2) for crossovers.

        idx = -1

        c_close = close_vals[idx]
        c_ema20 = ema20[idx]
        c_ema50 = ema50[idx]

        k_curr = stoch_k[idx]
        d_curr = stoch_d[idx]
        k_prev = stoch_k[idx - 1]
        d_prev = stoch_d[idx - 1]

        signal = "NEUTRAL"
        reason = []
        confidence = 0.0

        # Long Condition
        # Trend: Price > EMA20 > EMA50
        is_uptrend = c_close > c_ema20 and c_ema20 > c_ema50
        # Pullback/Entry: Stoch Cross Up in Oversold (<20)
        stoch_cross_up = k_prev < d_prev and k_curr > d_curr
        stoch_oversold = k_curr < 25  # Slightly loose threshold

        if is_uptrend:
            reason.append("Uptrend (Close > EMA20 > EMA50)")
            if stoch_cross_up and stoch_oversold:
                signal = "BUY"
                confidence = 0.85
                reason.append("Stochastic Cross Up in Oversold Zone")
            elif stoch_oversold:
                reason.append("Stochastic Oversold (Waiting for cross)")

        # Short Condition
        # Trend: Price < EMA20 < EMA50
        is_downtrend = c_close < c_ema20 and c_ema20 < c_ema50
        # Pullback/Entry: Stoch Cross Down in Overbought (>80)
        stoch_cross_down = k_prev > d_prev and k_curr < d_curr
        stoch_overbought = k_curr > 75  # Slightly loose threshold

        if is_downtrend:
            reason.append("Downtrend (Close < EMA20 < EMA50)")
            if stoch_cross_down and stoch_overbought:
                signal = "SELL"
                confidence = 0.85
                reason.append("Stochastic Cross Down in Overbought Zone")
            elif stoch_overbought:
                reason.append("Stochastic Overbought (Waiting for cross)")

        return {
            "signal": signal,
            "confidence": confidence,
            "timeframe": "5m",
            "indicators": {
                "ema20": float(c_ema20),
                "ema50": float(c_ema50),
                "stoch_k": float(k_curr),
                "stoch_d": float(d_curr),
            },
            "reasoning": "; ".join(reason),
        }

    def _analyze_15m(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        15-Minute Strategy: Bollinger Bands Reversal with RSI.
        """
        # ⚡ Bolt: Extract NumPy arrays once to bypass Pandas Series overhead
        close_vals = df["close"].values
        high_vals = df["high"].values
        low_vals = df["low"].values

        # Indicators
        # ⚡ Bolt: Passing NumPy arrays to TA-Lib is ~8x faster than passing Pandas Series
        upper, middle, lower = talib.BBANDS(
            close_vals, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        rsi = talib.RSI(close_vals, timeperiod=14)

        idx = -1
        # ⚡ Bolt: Removed redundant close.iloc[idx] and switched to direct NumPy indexing
        c_low = low_vals[idx]
        c_high = high_vals[idx]
        c_upper = upper[idx]
        c_lower = lower[idx]
        c_rsi = rsi[idx]

        signal = "NEUTRAL"
        reason = []
        confidence = 0.0

        # Long Condition: Price touches lower band, RSI oversold
        if c_low <= c_lower:
            reason.append("Price touched Lower Bollinger Band")
            if c_rsi < 35:  # Oversold threshold
                signal = "BUY"
                confidence = 0.8
                reason.append(f"RSI Oversold ({c_rsi:.2f})")
            else:
                reason.append(f"RSI Neutral ({c_rsi:.2f})")

        # Short Condition: Price touches upper band, RSI overbought
        elif c_high >= c_upper:
            reason.append("Price touched Upper Bollinger Band")
            if c_rsi > 65:  # Overbought threshold
                signal = "SELL"
                confidence = 0.8
                reason.append(f"RSI Overbought ({c_rsi:.2f})")
            else:
                reason.append(f"RSI Neutral ({c_rsi:.2f})")

        return {
            "signal": signal,
            "confidence": confidence,
            "timeframe": "15m",
            "indicators": {
                "bb_upper": float(c_upper),
                "bb_lower": float(c_lower),
                "rsi": float(c_rsi),
            },
            "reasoning": "; ".join(reason),
        }

    def _analyze_30m(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        30-Minute Strategy: MACD Trend Following.
        """
        # ⚡ Bolt: Extract NumPy arrays once to bypass Pandas Series overhead
        close_vals = df["close"].values

        # Indicators
        # ⚡ Bolt: Passing NumPy arrays to TA-Lib is ~8x faster than passing Pandas Series
        ema50 = talib.EMA(close_vals, timeperiod=50)
        macd, macd_signal, macd_hist = talib.MACD(
            close_vals, fastperiod=12, slowperiod=26, signalperiod=9
        )

        idx = -1
        # ⚡ Bolt: Switch to direct NumPy indexing
        c_close = close_vals[idx]
        c_ema50 = ema50[idx]
        c_hist = macd_hist[idx]
        p_hist = macd_hist[idx - 1]

        signal = "NEUTRAL"
        reason = []
        confidence = 0.0

        # Long Condition: Above EMA50, MACD Hist crosses above 0
        is_above_ema = c_close > c_ema50
        macd_cross_up = p_hist <= 0 and c_hist > 0

        if is_above_ema:
            reason.append("Price > EMA50")
            if macd_cross_up:
                signal = "BUY"
                confidence = 0.9
                reason.append("MACD Histogram crossed above Zero")

        # Short Condition: Below EMA50, MACD Hist crosses below 0
        is_below_ema = c_close < c_ema50
        macd_cross_down = p_hist >= 0 and c_hist < 0

        if is_below_ema:
            reason.append("Price < EMA50")
            if macd_cross_down:
                signal = "SELL"
                confidence = 0.9
                reason.append("MACD Histogram crossed below Zero")

        return {
            "signal": signal,
            "confidence": confidence,
            "timeframe": "30m",
            "indicators": {"ema50": float(c_ema50), "macd_hist": float(c_hist)},
            "reasoning": "; ".join(reason),
        }
