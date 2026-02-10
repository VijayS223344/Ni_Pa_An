import pandas as pd
import yfinance as yf


class DataLoader:
    def __init__(self):
        pass

    def download_data(self, symbol, period="2y", interval="1d"):
        df = yf.download(symbol, period=period, interval=interval)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(col).lower() for col in df.columns]
        df = df.dropna()
        return df

    def load_from_csv(self, filepath):
        raw = pd.read_csv(filepath)
        cols = {c.lower(): c for c in raw.columns}

        if "date" not in cols:
            raise ValueError(f"CSV must contain a date column. Found columns: {list(raw.columns)}")

        date_col = cols["date"]
        raw[date_col] = pd.to_datetime(raw[date_col])
        raw = raw.set_index(date_col)

        raw.columns = [str(col).lower() for col in raw.columns]

        required = {"open", "high", "low", "close"}
        missing = required - set(raw.columns)
        if missing:
            raise ValueError(f"Missing required OHLC columns: {sorted(missing)}")

        return raw.sort_index().dropna(subset=["open", "high", "low", "close"])
