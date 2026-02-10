
import numpy as np
from dtaidistance import dtw


class PriceActionMatcher:
    def __init__(self, historical_data):
        self.historical_data = historical_data.copy()

    def find_similar_patterns(self, current_bars, lookback, forward_bars,
                              use_atr_filter=False, use_regime_filter=False):

        hist = self.historical_data
        curr = self._features(current_bars.iloc[-lookback:])

        matches = []
        total = len(hist) - lookback - forward_bars

        for i in range(total):
            hist_pattern = self._features(hist.iloc[i:i + lookback])
            dist = dtw.distance(curr, hist_pattern)
            sim = 1 / (1 + dist)

            future = hist.iloc[i + lookback:i + lookback + forward_bars]
            entry = hist["close"].iloc[i + lookback - 1]
            final = future["close"].iloc[-1]

            matches.append({
                "similarity": sim,
                "outcome": {"final_return_pct": (final - entry) / entry * 100}
            })

        matches.sort(key=lambda x: -x["similarity"])
        return matches

    def _features(self, bars):
        base = bars["open"].iloc[0]
        return ((bars[["open", "high", "low", "close"]] / base - 1) * 100).values.flatten()
