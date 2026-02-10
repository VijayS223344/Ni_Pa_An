from dataclasses import dataclass
from time import perf_counter

import pandas as pd

from matcher import PriceActionMatcher
from predictor import classify_return, predict_direction


@dataclass
class ExperimentConfig:
    lookback: int = 15
    forward_window: int = 30
    step_size: int = 1
    n_max: int = 5
    k_min: int = 2
    theta_pct: float = 0.0
    similarity_threshold: float = None
    atr_threshold: float = 0.20
    atr_window: int = 14
    trend_flat_threshold_pct: float = 0.5
    show_progress: bool = True
    progress_every: int = 10


class WalkForwardEvaluator:
    def __init__(self, df, config: ExperimentConfig, start_prediction_date: str = "2024-01-01"):
        self.df = df
        self.config = config
        self.start_prediction_date = pd.Timestamp(start_prediction_date)

        self.models = [
            {"name": "NO_FILTER", "use_atr": False, "use_regime": False},
            {"name": "ATR", "use_atr": True, "use_regime": False},
            {"name": "REGIME", "use_atr": False, "use_regime": True},
            {"name": "ATR_REGIME", "use_atr": True, "use_regime": True},
        ]

    def run(self, show_progress=None):
        cfg = self.config
        results = []

        min_start = max(cfg.lookback, cfg.forward_window)
        max_end = len(self.df) - cfg.forward_window

        evaluation_points = []
        for t_index in range(min_start, max_end, cfg.step_size):
            if self.df.index[t_index] >= self.start_prediction_date:
                evaluation_points.append(t_index)

        total_points = len(evaluation_points)
        if total_points == 0:
            return pd.DataFrame(results)

        use_progress = cfg.show_progress if show_progress is None else show_progress

        started_at = perf_counter()
        next_milestone = 10

        if use_progress:
            print(
                f"[START] walk-forward started | evaluation_points={total_points} | "
                f"models={len(self.models)} | expected_rows={total_points * len(self.models)}"
            )

        for processed_points, t_index in enumerate(evaluation_points, start=1):
            date = self.df.index[t_index]
            hist = self.df.iloc[:t_index]
            current = self.df.iloc[t_index - cfg.lookback : t_index]
            if len(current) < cfg.lookback:
                continue

            matcher = PriceActionMatcher(hist)
            actual = self._actual_outcome(t_index)

            for model in self.models:
                matches = matcher.find_similar_patterns(
                    current_bars=current,
                    lookback=cfg.lookback,
                    forward_bars=cfg.forward_window,
                    use_atr_filter=model["use_atr"],
                    use_regime_filter=model["use_regime"],
                    similarity_threshold=cfg.similarity_threshold,
                    atr_threshold=cfg.atr_threshold,
                    atr_window=cfg.atr_window,
                    trend_flat_threshold_pct=cfg.trend_flat_threshold_pct,
                )

                pred = predict_direction(
                    matches=matches,
                    n_max=cfg.n_max,
                    k_min=cfg.k_min,
                    theta_pct=cfg.theta_pct,
                )

                is_prediction = pred["prediction"] in ["UP", "DOWN", "NEUTRAL"]
                correct = is_prediction and pred["prediction"] == actual
                wrong_way = pred["prediction"] in ["UP", "DOWN"] and pred["prediction"] != actual

                results.append(
                    {
                        "T_index": t_index,
                        "T_date": date,
                        "model": model["name"],
                        "prediction": pred["prediction"],
                        "confidence": pred["confidence"],
                        "dominance_ratio": pred["dominance_ratio"],
                        "total_weight": pred["total_weight"],
                        "k": pred["k"],
                        "actual_outcome": actual,
                        "correct": correct,
                        "wrong_way": wrong_way,
                        "coverage_hit": int(is_prediction),
                    }
                )

            if use_progress:
                self._print_progress(
                    processed_points=processed_points,
                    total_points=total_points,
                    t_index=t_index,
                    t_date=date,
                    started_at=started_at,
                    progress_every=max(1, cfg.progress_every),
                    next_milestone=next_milestone,
                )
                while int((processed_points / total_points) * 100) >= next_milestone:
                    next_milestone += 10

        if use_progress:
            elapsed = perf_counter() - started_at
            print(
                f"[DONE] walk-forward finished | elapsed={elapsed:.1f}s | "
                f"rows_generated={len(results)}"
            )

        return pd.DataFrame(results)

    def _print_progress(
        self,
        processed_points: int,
        total_points: int,
        t_index: int,
        t_date,
        started_at: float,
        progress_every: int,
        next_milestone: int,
    ):
        pct = (processed_points / total_points) * 100
        elapsed = perf_counter() - started_at
        speed = processed_points / elapsed if elapsed > 0 else 0.0
        remaining_points = total_points - processed_points
        eta_seconds = (remaining_points / speed) if speed > 0 else float("inf")

        reached_milestone = int(pct) >= next_milestone
        periodic_tick = (processed_points % progress_every) == 0
        final_tick = processed_points == total_points

        if reached_milestone or periodic_tick or final_tick:
            eta_str = f"{eta_seconds:.1f}s" if eta_seconds != float("inf") else "unknown"
            print(
                f"[PROGRESS] {processed_points}/{total_points} ({pct:.1f}%) | "
                f"T_index={t_index} | T_date={t_date.date()} | elapsed={elapsed:.1f}s | eta={eta_str}"
            )

    def _actual_outcome(self, t_index: int) -> str:
        cfg = self.config
        entry = self.df["close"].iloc[t_index]
        future = self.df["close"].iloc[t_index + cfg.forward_window]
        final_return_pct = ((future - entry) / entry) * 100.0
        return classify_return(final_return_pct=final_return_pct, theta_pct=cfg.theta_pct)


def summarize_results(results_df: pd.DataFrame) -> pd.DataFrame:
    if results_df.empty:
        return results_df

    summary = []
    for model_name, grp in results_df.groupby("model"):
        predicted = grp[grp["prediction"] != "NO_PREDICTION"]
        coverage = len(predicted) / len(grp) if len(grp) else 0.0
        conditional_accuracy = predicted["correct"].mean() if len(predicted) else 0.0
        wrong_way_rate = predicted["wrong_way"].mean() if len(predicted) else 0.0

        summary.append(
            {
                "model": model_name,
                "rows": len(grp),
                "coverage": coverage,
                "conditional_accuracy": conditional_accuracy,
                "wrong_way_rate": wrong_way_rate,
                "avg_k": predicted["k"].mean() if len(predicted) else 0.0,
                "avg_confidence": predicted["confidence"].mean() if len(predicted) else 0.0,
            }
        )

    return pd.DataFrame(summary).sort_values(
        by=["wrong_way_rate", "conditional_accuracy"], ascending=[True, False]
    )
