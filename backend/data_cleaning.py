import datetime

import pandas as pd
from yahoofinancials import YahooFinancials
import numpy as np


spreadsheet = pd.read_excel("Considered_Stocks.xlsx", sheet_name="Stocks")


def verify_tickers():
    # Find tickers that do not exist anymore, tickers with incomplete data (need handling)

    sectors = ["Information Technology", "Communication Services", "Consumer Discretionary",
            "Consumer Staples", "Finance", "Healthcare", "Industrials", "Energy", "Real Estate"]
    
    bad_tickers = []
    for sector in sectors:
        tickers = spreadsheet[sector].dropna()

        for ticker in tickers:
            print(ticker)
            try:
                stock = YahooFinancials(ticker)
                start = str(datetime.date.today() - datetime.timedelta(days=4))
                end = str(datetime.date.today() - datetime.timedelta(days=0))
                historical_closes = stock.get_historical_price_data(start, end, "daily")
                prices = historical_closes[ticker]['prices']
                closes = [round(day['close'], 2) for day in prices]     
            except:
                bad_tickers.append(ticker)
        
    return bad_tickers


print(verify_tickers())