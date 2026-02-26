## 2024-07-22 - Non-blocking CPU-Bound Tasks in Asyncio

**Learning:** I discovered a performance bottleneck in `core/trading_engine.py` where a CPU-bound operation, `technical_indicators.add_all_indicators`, was blocking the `asyncio` event loop. Even though the I/O operations were concurrent, this synchronous calculation serialized the execution, negating the benefits of `asyncio.gather`.

**Action:** In the future, I will use `asyncio.to_thread` to run any CPU-bound function in a separate thread. This will keep the event loop free and ensure that both I/O and CPU-bound tasks can run in parallel, maximizing throughput.

## 2025-01-30 - Vectorizing Rolling Linear Regression Slope

**Learning:** I identified a major performance bottleneck in `utils/technical_indicators.py` where `rolling().apply(np.polyfit)` was used to calculate trend strength. This iterative approach is extremely slow because it invokes the SVD-based `polyfit` solver and Python-level overhead for every window.

**Action:** I replaced the iterative approach with a vectorized mathematical formula using `np.convolve` and `rolling().sum()`. This optimization provided a ~3x speedup for the `add_trend_indicators` method, significantly reducing the CPU load during market data processing and signal generation.

## 2025-02-14 - Redundant Mean in Mean Absolute Deviation (MAD)

**Learning:** While optimizing CCI in `utils/technical_indicators.py`, I realized that the rolling Mean Absolute Deviation (MAD) step was re-calculating the rolling mean for every window, even though the Simple Moving Average (SMA) of the Typical Price (`sma_tp`) had already been computed. Reusing these pre-calculated mean values in the vectorized MAD calculation avoids redundant arithmetic.

**Action:** I refactored the CCI calculation to reuse `sma_tp.values` during the vectorized MAD step. I also switched from `as_strided` to `np.lib.stride_tricks.sliding_window_view` for safer and more modern vectorized window generation. This improved the CCI calculation speed by ~17%.

## 2025-02-14 - Weight Ordering in Vectorized WMA

**Learning:** I discovered that the previous `np.convolve` implementation of the Weighted Moving Average (WMA) was logically incorrect because it didn't account for the fact that convolution flips the kernel. This resulted in older prices receiving higher weights than recent ones.

**Action:** I corrected the WMA implementation by reversing the weights (`weights[::-1]`) before passing them to `np.convolve`. I also optimized the denominator calculation using the constant-time arithmetic series formula `n*(n+1)/2`, ensuring the indicator is both fast and mathematically sound.

## 2025-01-30 - Row-wise Maximum and Arithmetic Overhead

**Learning:** I identified a significant performance bottleneck in the ADX calculation within `utils/technical_indicators.py`. Specifically, using `pd.concat([...], axis=1).max(axis=1)` to calculate the True Range (TR) is extremely inefficient compared to nested `np.maximum` calls. Additionally, performing row-wise arithmetic on Pandas Series carries substantial overhead for index alignment and validation.

**Action:** I replaced `pd.concat().max()` with nested `np.maximum` and moved arithmetic operations to raw NumPy arrays by using `.values`. This combination reduced the ADX calculation time by ~43%, demonstrating that bypassing the Pandas Series abstraction for simple row-wise math is a powerful optimization in hot code paths.

## 2025-02-12 - Reusing Intermediate Indicator Results

**Learning:** I identified a common performance anti-pattern where multiple technical indicators (e.g., Stochastic Oscillator, Williams %R, Bollinger Bands, and Support/Resistance) re-calculate the same rolling windows (min, max, mean, std) independently. This redundancy wastes CPU cycles, especially as the number of indicators grows.

**Action:** I refactored `utils/technical_indicators.py` to calculate shared rolling windows once and reuse them. For example, rolling min/max for window 14 is now shared between Stochastic and Williams %R, and `sma_20`/`std_20` are shared between Bollinger Bands and Volatility Indicators. This optimization provides a ~10-15% speedup across the affected methods without changing the output logic.

## 2025-05-15 - Vectorized Sliding Windows in Feature Engineering

**Learning:** I identified a massive performance bottleneck in `ai_models/feature_engineer.py` where Python loops were used to generate sliding windows for LSTMs and CNNs. Generating chart images was particularly slow (~1.7s for 2000 rows) due to repeated `.iloc` slicing and redundant normalization in every window. Additionally, the inference path redundantly calculated the entire history even though only the last window was needed.

**Action:** I replaced the Python loops with `numpy.lib.stride_tricks.sliding_window_view` for fully vectorized window generation, yielding a ~270x speedup for chart images. I also introduced an `only_last` flag to optimize the inference path, providing a ~60x speedup for real-time predictions. Using `np.stack` and `np.column_stack` on the vectorized windows ensures the multi-channel structure is maintained without explicit iteration.

## 2025-05-20 - Index Alignment Overhead in Row-wise Arithmetic

**Learning:** I identified a performance bottleneck in `utils/technical_indicators.py` where multiple technical indicators (RSI, Bollinger Bands, Pivot Points) were performing row-wise arithmetic directly on Pandas Series. Each Series-to-Series operation triggers index validation and alignment, which is costly when done repeatedly for many columns.

**Action:** I replaced Series arithmetic with raw NumPy array operations by extracting `.values`. This optimization provided a ~20% speedup for Support/Resistance levels and a ~5% boost for Bollinger Bands. Moving to NumPy for final arithmetic steps after windowed operations (like rolling mean) is a consistent win in this codebase.

## 2025-05-25 - Bypassing Series Index Alignment in Bulk Indicator Arithmetic

**Learning:** I identified a consistent performance overhead in `utils/technical_indicators.py` where row-wise arithmetic operations (addition, subtraction, division) were performed directly on Pandas Series. Even when indexes are aligned, Pandas performs validation that becomes significant when called repeatedly across dozens of indicators.

**Action:** I replaced Series-to-Series arithmetic with raw NumPy array operations by extracting `.values`. For OBV and VPT, I fully vectorized the logic using `np.diff` and `np.where`. This provided a ~14% overall speedup for the `add_all_indicators` method (~100ms per 100k rows), demonstrating that "dropping down" to NumPy for final arithmetic steps after windowed operations is a high-value performance pattern in data-intensive paths.

## 2026-02-14 - Vectorizing SMA, ROC, and ADX Shifting

**Learning:** I identified a performance bottleneck in the technical indicator utility where SMA, ROC, and ADX were using Pandas-level operations (`rolling().mean()`, `pct_change()`, and `shift()`). While these are optimized in Pandas, they still carry significant overhead for index alignment and validation when called repeatedly for multiple periods and columns.

**Action:** I replaced Pandas `rolling().mean()` with `np.convolve` for SMAs, and replaced `pct_change()` and `shift()` with vectorized NumPy arithmetic. These optimizations provided a ~32% overall speedup for the `add_all_indicators` method (~91ms vs ~135ms for 10k rows), confirming that "dropping down" to raw NumPy arrays for even basic arithmetic and windowing is a consistent performance win in data-intensive paths.

## 2026-02-14 - Broad Optimization with np.convolve and NumPy Shifting

**Learning:** I identified that while many technical indicators had been partially optimized, several still relied on Pandas-level `rolling().mean()` and `shift()` operations (ATR, Volume SMA, RSI smoothing, Stochastic D, and ADX). While Pandas is efficient, it still carries significant overhead for index alignment and validation compared to raw NumPy operations, especially when these operations are nested or called repeatedly.

**Action:** I replaced all remaining simple rolling means and sums with `np.convolve` and replaced Pandas `shift()` with raw NumPy array slicing. This broad application of "dropping down" to NumPy across multiple indicators provided a cumulative ~28% speedup for the `add_all_indicators` method (reducing execution time from ~0.75s to ~0.54s for 100k rows), confirming that eliminating even minor Pandas overhead in hot code paths yields significant measurable gains.

## 2026-02-14 - Redundant TA-Lib Calls and Inference Slicing

**Learning:** I identified two major performance bottlenecks in `ai_models/feature_engineer.py`. First, multi-output indicators (MACD, BBANDS) were called three times each to extract individual components, tripling the C-level execution time. Second, the inference path (`engineer_features_for_prediction`) was calculating indicators and patterns for the entire historical dataset even though only the last window was required for model input.

**Action:** I consolidated multi-output library calls to execute once and unpack results. I also implemented a "safe lookback" slicing logic (500 bars) in the prediction path, ensuring that indicators have sufficient history to converge while preventing performance degradation on large input datasets. Consistently reusing library results and slicing before heavy computation are critical patterns for high-frequency prediction pipelines.

## 2026-02-14 - NumPy 2.0 Compatibility with Legacy ML Libraries

**Learning:** I discovered that legacy versions of machine learning libraries (like `scikit-learn==1.3.2`) fail to build from source on newer Python versions (like 3.13) when `numpy>=2.0` is present. The error `'int_t' is not a type identifier` occurs because NumPy 2.0 removed several deprecated type aliases used in older Cython files.

**Action:** I pinned `numpy<2.0.0` in `requirements.txt` to ensure compatibility across all supported Python versions (3.11-3.13) and to maintain stable builds for the AI prediction pipeline. When working with older ML stacks on modern runtimes, pinning the major version of core numerical libraries is essential for CI stability.

## 2026-02-14 - Scikit-Learn Upgrade for Python 3.13 and CI Speed

**Learning:** Using legacy library versions (like `scikit-learn==1.3.2`) on modern Python runtimes (like 3.13) forces `pip` to build from source because pre-built wheels don't exist for that combination. This not only makes CI runs significantly slower but also risks build-time failures if the library's Cython files are incompatible with the latest version of build-time dependencies like NumPy.

**Action:** I upgraded `scikit-learn` to `>=1.5.2` in `requirements.txt`. This allows `pip` to install pre-built wheels on all supported Python versions (3.11-3.13), resolving the CI build error and drastically reducing installation time. Favoring libraries with modern wheel support is a key performance strategy for CI/CD pipelines.

## 2026-02-14 - Pydantic Compatibility with Python 3.13

**Learning:** I identified a CI failure on Python 3.13 caused by `pydantic-core==2.14.1` (used by `pydantic==2.5.0`). The error `ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'` occurs because Python 3.13 changed internal APIs that older Pydantic versions relied on for forward reference evaluation.

**Action:** I upgraded `pydantic` to `>=2.10.0`, `fastapi` to `>=0.115.0`, and `pydantic-settings` to `>=2.4.0`. These versions include the necessary fixes for Python 3.13 compatibility. Maintaining core framework dependencies within their actively supported windows is critical for ensuring application stability on the latest language runtimes.

## 2026-02-14 - TA-Lib Vectorization and Label Optimization
**Learning:** I identified that passing Pandas Series to TA-Lib functions (especially candlestick patterns) triggers repeated index alignment and validation overhead. Extracting NumPy values once and passing them to 60+ pattern calls provides a massive speedup. Additionally, I found that `talib.SMA` is ~10x faster than `np.convolve` for moving averages, and NumPy-based slicing for labels is ~4x faster than `pd.Series.shift`.
**Action:** Always extract `.values` before multiple TA-Lib calls in a loop. Prefer `talib.SMA` over manual convolution when the library is available. Use NumPy slicing for future-looking label generation to avoid Pandas overhead in training data preparation.

## 2026-02-08 - Redis Caching for Static Constants
**Learning:** I discovered that several static API endpoints (like `/` and `/mt5-info`) were using Redis to cache hardcoded dictionary constants. This is an anti-pattern because the overhead of a Redis network round-trip and JSON serialization/deserialization is significantly higher than simply returning the in-memory constant.
**Action:** I removed the redundant Redis caching logic for static data and refactored the endpoints to return constants directly. In the future, I will only use Redis for dynamic data that is expensive to compute or retrieve from a primary database.

## 2026-02-14 - Vectorizing Rolling Std, Min, and Max

**Learning:** I identified that several technical indicators in `utils/technical_indicators.py` (Bollinger Bands, Stochastic Oscillator, Donchian Channels) were still using Pandas-level `rolling().std()`, `rolling().min()`, and `rolling().max()`. These operations carry significant overhead, especially for the small lookback windows (100-500 bars) used in this project's real-time inference path. I also discovered that `np.empty_like` on integer-based DataFrames fails when trying to assign `np.nan` for the initial bars.

**Action:** I replaced all remaining Pandas rolling window operations with vectorized NumPy equivalents using `np.convolve` (for variance/std) and `np.lib.stride_tricks.sliding_window_view` (for min/max). I also added explicit `.astype(float)` casting and `dtype=float` to NumPy array initializations to ensure robust handling of `np.nan`. These optimizations provided a ~5.2x speedup for rolling standard deviation on small datasets (n=100), significantly reducing latency for high-frequency signal generation.

## 2026-02-14 - Slicing Lists Before DataFrame Creation

**Learning:** I identified a significant performance bottleneck in the `get_predictions` and `get_scalping_signals` endpoints where the entire `historical_data` list (often containing thousands of rows) was being converted to a Pandas DataFrame, only to be sliced to 500 bars immediately after. Benchmark tests showed that converting 100k rows of a list of dicts to a DataFrame is ~100x slower than slicing the list first.

**Action:** I modified `api/main.py` to slice the incoming `historical_data` list to the last 1000 items BEFORE calling the DataFrame constructor. This ensures that the CPU-intensive DataFrame creation only processes the data actually needed for inference, drastically reducing latency and memory usage for large payloads.

## 2026-02-17 - Robust Distributed Lock with Retry

**Learning:** I identified a flaw in the Redis distributed lock implementation in `api/routers/predictions.py` where it only waited once for 0.1s if the lock was busy, leading to potential cache stampedes under high load. A single short wait is insufficient when the protected operation (ML model metrics calculation) takes longer than the wait time.

**Action:** I implemented a retry loop (5 attempts with 0.1s delay) to properly handle lock contention. This ensures that concurrent requests wait for the result to be cached instead of falling back to redundant expensive calculations or failing. I also verified this behavior with a dedicated test case using `unittest.mock`.

## 2026-02-18 - Passing NumPy Arrays to TA-Lib and Positional Indexing

**Learning:** I identified a significant performance bottleneck in `api/services/scalping_service.py` where Pandas Series were passed directly to `talib` functions and values were accessed using `.iloc`. Benchmarks showed that passing raw NumPy arrays (`.values`) to `talib` is ~8x faster than passing Series, and direct array indexing (`[idx]`) is ~3x faster than `.iloc`.

**Action:** In high-frequency signal generation paths, always extract `.values` from DataFrame columns once and pass these NumPy arrays to `talib` functions. Use positional indexing on the resulting arrays for maximum efficiency. When updating such services, ensure corresponding unit test mocks also return NumPy arrays to maintain compatibility with positional indexing.
