from typing import Dict, List, Optional

import numpy as np
from dtaidistance import dtw


class PriceActionMatcher:
    def __init__(self, historical_data):
        self.historical_data = historical_data.copy()

    def find_similar_patterns(
        self,
        current_bars,
        lookback: int,
        forward_bars: int,
        use_atr_filter: bool = False,
        use_regime_filter: bool = False,
        similarity_threshold: Optional[float] = None,
        atr_threshold: float = 0.20,
        atr_window: int = 14,
        trend_flat_threshold_pct: float = 0.5,
    ) -> List[Dict]:
        hist = self.historical_data
        curr_window = current_bars.iloc[-lookback:]
        curr_features = self._features(curr_window)

        current_atr_pct = self._average_atr_pct(curr_window, atr_window)
        current_regime = self._regime_label(curr_window, atr_window, trend_flat_threshold_pct)

        matches: List[Dict] = []
        total = len(hist) - lookback - forward_bars + 1
        if total <= 0:
            return matches

        for i in range(total):
            hist_window = hist.iloc[i : i + lookback]
            future = hist.iloc[i + lookback : i + lookback + forward_bars]
            if len(future) < forward_bars:
                continue

            if use_atr_filter:
                hist_atr_pct = self._average_atr_pct(hist_window, atr_window)
                if current_atr_pct is None or hist_atr_pct is None or current_atr_pct <= 0:
                    continue
                atr_gap = abs(hist_atr_pct - current_atr_pct) / current_atr_pct
                if atr_gap > atr_threshold:
                    continue

            if use_regime_filter:
                hist_regime = self._regime_label(hist_window, atr_window, trend_flat_threshold_pct)
                if hist_regime != current_regime:
                    continue

            hist_features = self._features(hist_window)
            dist = dtw.distance(curr_features, hist_features)
            sim = 1.0 / (1.0 + dist)

            if similarity_threshold is not None and sim < similarity_threshold:
                continue

            entry = hist_window["close"].iloc[-1]
            final = future["close"].iloc[-1]
            final_return_pct = ((final - entry) / entry) * 100.0

            matches.append(
                {
                    "similarity": sim,
                    "outcome": {"final_return_pct": final_return_pct},
                    "meta": {
                        "window_start_idx": i,
                        "atr_pct": self._average_atr_pct(hist_window, atr_window),
                        "regime": self._regime_label(
                            hist_window, atr_window, trend_flat_threshold_pct
                        ),
                    },
                }
            )

        matches.sort(key=lambda x: -x["similarity"])
        return matches

    def _features(self, bars):
        base = bars["open"].iloc[0]
        return ((bars[["open", "high", "low", "close"]] / base - 1) * 100).values.flatten()

    def _average_atr_pct(self, bars, atr_window: int) -> Optional[float]:
        if len(bars) < 2:
            return None

        high = bars["high"]
        low = bars["low"]
        close = bars["close"]
        prev_close = close.shift(1)

        tr = np.maximum(high - low, np.maximum((high - prev_close).abs(), (low - prev_close).abs()))
        atr = tr.rolling(window=min(atr_window, len(bars)), min_periods=2).mean()
        atr_pct = (atr / close) * 100

        value = atr_pct.mean()
        if np.isnan(value):
            return None
        return float(value)

    def _regime_label(self, bars, atr_window: int, trend_flat_threshold_pct: float) -> str:
        if len(bars) < 2:
            return "flat_normal"

        start = float(bars["close"].iloc[0])
        end = float(bars["close"].iloc[-1])
        net_change_pct = ((end - start) / start) * 100.0

        if net_change_pct > trend_flat_threshold_pct:
            trend = "up"
        elif net_change_pct < -trend_flat_threshold_pct:
            trend = "down"
        else:
            trend = "flat"

        atr_pct = self._average_atr_pct(bars, atr_window)
        if atr_pct is None:
            vol = "normal"
        elif atr_pct < 0.8:
            vol = "low"
        elif atr_pct > 1.6:
            vol = "high"
        else:
            vol = "normal"

        return f"{trend}_{vol}"
