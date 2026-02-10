
import pandas as pd
from predictor import predict_direction
from matcher import PriceActionMatcher

START_PREDICTION_DATE = pd.Timestamp("2024-01-01")


class WalkForwardEvaluator:
    def __init__(self, df, lookback=15, forward_window=30, step_size=1):
        self.df = df
        self.lookback = lookback
        self.forward_window = forward_window
        self.step_size = step_size

        self.models = [
            {"name": "NO_FILTER", "use_atr": False, "use_regime": False},
            {"name": "ATR", "use_atr": True, "use_regime": False},
            {"name": "REGIME", "use_atr": False, "use_regime": True},
            {"name": "ATR_REGIME", "use_atr": True, "use_regime": True},
        ]

    def run(self):
        results = []
        min_start = max(self.lookback, self.forward_window)
        max_end = len(self.df) - self.forward_window

        for T in range(min_start, max_end, self.step_size):
            date = self.df.index[T]
            if date < START_PREDICTION_DATE:
                continue

            hist = self.df.iloc[:T]
            current = self.df.iloc[T - self.lookback:T]

            matcher = PriceActionMatcher(hist)
            actual = self._actual_outcome(T)

            for m in self.models:
                matches = matcher.find_similar_patterns(
                    current, self.lookback, self.forward_window,
                    m["use_atr"], m["use_regime"]
                )

                pred = predict_direction(matches)
                wrong = pred["prediction"] in ["UP", "DOWN"] and pred["prediction"] != actual

                results.append({
                    "T_index": T,
                    "T_date": date,
                    "model": m["name"],
                    "prediction": pred["prediction"],
                    "confidence": pred["confidence"],
                    "k": pred["k"],
                    "actual_outcome": actual,
                    "wrong_way": wrong
                })

        return pd.DataFrame(results)

    def _actual_outcome(self, T):
        entry = self.df["close"].iloc[T]
        future = self.df["close"].iloc[T + self.forward_window]
        if future > entry:
            return "UP"
        if future < entry:
            return "DOWN"
        return "NEUTRAL"
