from data_loader import DataLoader
from evaluator import ExperimentConfig, WalkForwardEvaluator, summarize_results


def main():
    loader = DataLoader()
    df = loader.load_from_csv("nifty_data_recent.csv")

    config = ExperimentConfig(
        lookback=15,
        forward_window=30,
        step_size=5,
        n_max=5,
        k_min=2,
        theta_pct=0.0,
        similarity_threshold=None,
        atr_threshold=0.20,
        atr_window=14,
        trend_flat_threshold_pct=0.5,
        show_progress=True,
        progress_every=10,
    )

    print(
        "Running walk-forward simulation with config: "
        f"lookback={config.lookback}, forward_window={config.forward_window}, "
        f"step_size={config.step_size}, n_max={config.n_max}, k_min={config.k_min}"
    )

    evaluator = WalkForwardEvaluator(df=df, config=config)
    results = evaluator.run()

    results.to_csv("walk_forward_results.csv", index=False)

    summary = summarize_results(results)
    summary.to_csv("walk_forward_summary.csv", index=False)

    print("Saved: walk_forward_results.csv")
    print("Saved: walk_forward_summary.csv")
    print("\nTop models by wrong-way rate then conditional accuracy:")
    print(summary.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
