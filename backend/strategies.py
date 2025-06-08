import pandas as pd
import numpy as np
import yfinance as yf

def sharpe_ratio():
    pass

def trend_score(ticker, regime_start, regime_end):
    stock = yf.Ticker(ticker)
    data = stock.history(start=regime_start, end=regime_end, interval="1d")
    
    total_return = (data["Close"][-1] - data["Close"][0]) / data["Close"][0]
    num_days = len(data["Close"]) - 1

    average_move = total_return / num_days # interest rates/forward pricing, splits & dividends?

    returns = (data["Close"] - data["Close"].shift(1)) / data["Close"].shift(1)
    returns = returns.dropna().values
    
    volatility = np.std(returns)

    score = average_move / volatility

    return round(score, 4)

def range_score(ticker, regime_start, regime_end):
    pass

tickers = ["AAPL", "TSLA", "DG"]
regime_starts = ["2025-04-10", "2025-04-23", "2025-05-15"]
regime_ends = ["2025-06-04", "2025-06-04", "2025-06-04"]
for i in range(len(tickers)):
    print(trend_score(tickers[i], regime_starts[i], regime_ends[i]))