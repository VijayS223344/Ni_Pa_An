
from data_loader import DataLoader
from evaluator import WalkForwardEvaluator


def main():
    loader = DataLoader()
    df = loader.load_from_csv("nifty_data.csv")

    evaluator = WalkForwardEvaluator(
        df=df,
        lookback=15,
        forward_window=30,
        step_size=5
    )

    results = evaluator.run()
    results.to_csv("walk_forward_results.csv", index=False)
    print(results.head())


if __name__ == "__main__":
    main()
