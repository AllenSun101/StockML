from datetime import datetime, timedelta
import pandas as pd
from yahoofinancials import YahooFinancials
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_sector(sector, spreadsheet, start, end):
    tickers = spreadsheet[sector].dropna()

    score_5 = 0
    score_10 = 0
    score_20 = 0
    total = 0

    for ticker in tickers:
        # print(ticker)
        
        try:
            stock = YahooFinancials(ticker)
            historical_closes = stock.get_historical_price_data(start, end, "daily")
            prices = historical_closes[ticker]['prices']
        except:
            continue

        closes = [round(day['close'], 2) for day in prices]     
        
        # Dataframe of exponential moving averages
        ema = pd.DataFrame()
        ema["Closes"] = closes
        ema["5 EMA"] = round(ema["Closes"].ewm(span=5).mean(), 2)
        ema["10 EMA"] = round(ema["Closes"].ewm(span=10).mean(), 2)
        ema["20 EMA"] = round(ema["Closes"].ewm(span=20).mean(), 2)

        # Add one point for every increase in EMA
        for i in range(-5, 0, 1):
            if ema["5 EMA"].iloc[i] > ema["5 EMA"].iloc[i - 1]:
                score_5 += 1

        for i in range(-10, 0, 1):
            if ema["10 EMA"].iloc[i] > ema["10 EMA"].iloc[i - 1]:
                score_10 += 1

        for i in range(-20, 0, 1):
            if ema["20 EMA"].iloc[i] > ema["20 EMA"].iloc[i - 1]:
                score_20 += 1

        total += 1
    
    score_5 = round(score_5 / total, 2)
    score_10 = round(score_10 / total, 2)
    score_20 = round(score_20 / total, 2)

    sector_scores = {"sector": sector, "5 Day": score_5, "10 Day": score_10, "20 Day": score_20}
    return sector_scores

if __name__ == "__main__":
    spreadsheet = pd.read_excel("Considered_Stocks.xlsx", sheet_name="Stocks")

    sectors = ["Information Technology", "Communication Services", "Consumer Discretionary",
            "Consumer Staples", "Finance", "Healthcare", "Industrials", "Energy", "Real Estate"]

    scores = []

    # Define the input format
    input_format = "%Y-%m-%d"

    # Get the current date as a string in the desired format
    date = datetime.now().strftime(input_format)

    # Convert the formatted date string back to a date object
    date_object = datetime.strptime(date, input_format).date()

    # Calculate the start and end dates
    start = str(date_object - timedelta(days=40))
    end = str(date_object - timedelta(days=0))

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_sector = {executor.submit(process_sector, sector, spreadsheet, start, end): sector for sector in sectors}
        
        for future in as_completed(future_to_sector):
            sector_scores = future.result()
            scores.append(sector_scores)

    for score in scores:
        print(f"{score['sector']}: 5 Day: {score['5 Day']}, 10 Day: {score['10 Day']}, 20 Day: {score['20 Day']}")
