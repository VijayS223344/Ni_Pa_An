
import yfinance as yf
import pandas as pd


class DataLoader:
    def __init__(self):
        pass

    def download_data(self, symbol, period='2y', interval='1d'):
        df = yf.download(symbol, period=period, interval=interval)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(col).lower() for col in df.columns]
        df = df.dropna()
        return df

    def load_from_csv(self, filepath):
        df = pd.read_csv(filepath, parse_dates=['date'], index_col='date')
        df.columns = [col.lower() for col in df.columns]
        return df
